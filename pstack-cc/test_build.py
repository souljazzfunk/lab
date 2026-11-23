import contextlib
import io
import shutil
import tempfile
import unittest
from pathlib import Path

import build


class UpstreamChange(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.vendor = self.tmp / "vendor"
        shutil.copytree(build.VENDOR, self.vendor)
        self.out = self.tmp / "plugin"

    def edit(self, rel: str, old: str, new: str) -> None:
        path = self.vendor / rel
        text = path.read_text()
        self.assertIn(old, text, f"上流の {rel} にこの文がもう無い。テストを今の上流に合わせる")
        path.write_text(text.replace(old, new))

    def run_build(self) -> tuple[str | None, str]:
        err = io.StringIO()
        original = build.VENDOR
        build.VENDOR = self.vendor
        try:
            with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
                build.build(self.out)
            return None, err.getvalue()
        except SystemExit as e:
            return str(e.code), err.getvalue()
        finally:
            build.VENDOR = original

    def assertNotShipped(self, word: str) -> None:
        hits = [p.relative_to(self.out) for p in (self.out / "skills").rglob("*.md") if word in p.read_text()]
        self.assertEqual(hits, [], f"{word!r} が残った")

    def test_issue_88_new_gemini_slug_still_becomes_sonnet(self):
        self.edit("skills/poteto-mode/SKILL.md", "gemini-4-neon-xhigh", "gemini-4-carbon-high")
        code, _ = self.run_build()
        self.assertIsNone(code)
        self.assertNotShipped("gemini-4-carbon")

    def test_pr_83_new_claude_slugs_become_family_names(self):
        self.edit("skills/poteto-mode/SKILL.md", "claude-fable-5-2-high", "claude-fable-6-0-max-fast")
        code, _ = self.run_build()
        self.assertIsNone(code)
        self.assertNotShipped("claude-fable-6")

    def test_issue_61_sentence_rewritten_into_harmless_text_passes_with_warning(self):
        rel = "skills/poteto-mode/playbooks/autopilot-full.md"
        self.edit(rel, "re-reads this playbook from trunk", "names this file")
        code, err = self.run_build()
        self.assertIsNone(code)
        self.assertIn("re-reads this playbook from trunk", err)

    def test_issue_36_trunk_reread_that_no_rule_covers_fails(self):
        self.edit(
            "skills/poteto-mode/playbooks/autopilot-stack.md",
            "Run the Autopilot-full playbook, but do not merge.",
            "Run the Autopilot-full playbook, but do not merge. Each tick re-reads both playbooks from trunk.",
        )
        code, err = self.run_build()
        self.assertIsNotNone(code)
        self.assertIn("autopilot-stack.md", err)
        self.assertIn("re-reads both playbooks from trunk", err)

    def test_issue_52_renumbered_step_leaves_cloud_environment_and_fails(self):
        self.edit("skills/swarm/SKILL.md", "and the step 3 model", "and the step 4 model")
        code, err = self.run_build()
        self.assertIsNotNone(code)
        self.assertIn("skills/swarm/SKILL.md", err)
        self.assertIn('environment: "cloud"', err)


class HandWrittenDocs(unittest.TestCase):
    def test_issue_88_table_naming_one_upstream_slug_fails_with_the_fix(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        adapter = tmp / "claude-code.md"
        adapter.write_text(build.ADAPTER.read_text() + "\n| `gemini-4-carbon-high` | `sonnet` |\n")
        original = build.ADAPTER
        build.ADAPTER = adapter
        err = io.StringIO()
        try:
            with contextlib.redirect_stderr(err), self.assertRaises(SystemExit):
                build.build(tmp / "plugin")
        finally:
            build.ADAPTER = original
        self.assertIn("gemini-4-carbon-high", err.getvalue())
        self.assertIn("claude-opus-<version>-<effort>", err.getvalue())


if __name__ == "__main__":
    unittest.main()
