#!/usr/bin/env python3
"""Pack the runtime files of this Chrome extension into one zip.

The file list comes from manifest.json (plus local files those references
pull in, such as a popup script or a stylesheet url). Tests, fixtures,
package manifests, Playwright config, and this packer are left out.

The zip has a single top folder, asiandocs-1080p/, with manifest.json
directly inside it.
"""

from __future__ import annotations

import json
import posixpath
import re
import sys
import tempfile
import time
import zipfile
from pathlib import Path

TOP = "asiandocs-1080p"

DENY_DIRS = {
    "tests",
    "test",
    "fixtures",
    "fixture",
    "node_modules",
    ".git",
    "test-results",
    "playwright-report",
    "blob-report",
    "playwright",
    "__pycache__",
    ".github",
}

DENY_FILES = {
    "package.json",
    "package-lock.json",
    "playwright.config.js",
    "playwright.config.ts",
    "playwright.config.mjs",
    "playwright.config.cjs",
    ".gitignore",
    "readme.md",
    "readme",
    "pack_release.py",
}

_ES_IMPORT = re.compile(
    r"""\bimport\s+(?:[^'";]*?\sfrom\s+)?['"]([^'"]+)['"]"""
)
_IMPORT_SCRIPTS = re.compile(r"""\bimportScripts\s*\(([^)]*)\)""")
_QUOTED = re.compile(r"""['"]([^'"]+)['"]""")
_CSS_URL = re.compile(r"""url\(\s*(['"]?)([^'")]+)\1\s*\)""", re.I)
_CSS_IMPORT = re.compile(
    r"""@import\s+(?:url\(\s*)?(['"])([^'"]+)\1""",
    re.I,
)


def _html_refs(text: str) -> list[tuple[str, bool]]:
    """Local urls referenced by an extension HTML page."""
    from html.parser import HTMLParser

    class Parser(HTMLParser):
        def __init__(self) -> None:
            super().__init__(convert_charrefs=True)
            self.refs: list[tuple[str, bool]] = []

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            attr = {key: value for key, value in attrs if value is not None}
            if tag == "script" and attr.get("src"):
                self.refs.append((attr["src"], attr.get("type", "").lower() == "module"))
            elif tag == "link" and attr.get("href") and _link_is_resource(attr):
                module = "modulepreload" in attr.get("rel", "").lower()
                self.refs.append((attr["href"], module))
            elif tag in {"img", "source", "audio", "track"} and attr.get("src"):
                self.refs.append((attr["src"], False))
            elif tag == "video":
                if attr.get("src"):
                    self.refs.append((attr["src"], False))
                if attr.get("poster"):
                    self.refs.append((attr["poster"], False))

    parser = Parser()
    parser.feed(text)
    parser.close()
    return parser.refs


def _link_is_resource(attr: dict[str, str]) -> bool:
    rel = attr.get("rel", "").lower()
    if any(token in rel.split() for token in ("stylesheet", "icon", "modulepreload")):
        return True
    if "preload" in rel.split():
        return attr.get("as", "").lower() in {"script", "style", "font", "image", "fetch"}
    return False


def _is_remote(ref: str) -> bool:
    lowered = ref.lower()
    if lowered.startswith(
        (
            "http://",
            "https://",
            "data:",
            "blob:",
            "chrome:",
            "chrome-extension:",
            "about:",
            "file:",
            "javascript:",
            "//",
        )
    ):
        return True
    return "://" in ref


def _clean_path(ref: str) -> str | None:
    """Return a root-relative path, or None when ref is not a local file."""
    text = ref.strip()
    if not text:
        return None
    text = text.split("#", 1)[0].split("?", 1)[0].strip()
    if not text or _is_remote(text):
        return None
    if text.startswith("/"):
        text = text[1:]
    text = text.replace("\\", "/")
    parts: list[str] = []
    for part in text.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            return None
        parts.append(part)
    if not parts:
        return None
    return "/".join(parts)


def _resolve(from_rel: str, ref: str) -> str | None:
    text = ref.strip()
    if not text:
        return None
    text = text.split("#", 1)[0].split("?", 1)[0].strip()
    if not text or _is_remote(text):
        return None
    if text.startswith("/"):
        return _clean_path(text)
    joined = posixpath.normpath(posixpath.join(posixpath.dirname(from_rel), text))
    if joined.startswith("../") or joined == "..":
        return None
    return joined


def _denied(rel: str) -> bool:
    parts = rel.split("/")
    if any(part.lower() in DENY_DIRS or part.startswith(".") for part in parts[:-1]):
        return True
    name = parts[-1]
    return name.lower() in DENY_FILES or name.startswith(".")


def _has_glob(pattern: str) -> bool:
    return any(char in pattern for char in "*?[")


def _as_strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def _icon_paths(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [item for item in value.values() if isinstance(item, str)]
    if isinstance(value, list):
        found: list[str] = []
        for item in value:
            if isinstance(item, str):
                found.append(item)
            elif isinstance(item, dict):
                for key in ("light", "dark", "path"):
                    candidate = item.get(key)
                    if isinstance(candidate, str):
                        found.append(candidate)
        return found
    return []


def _manifest_refs(manifest: dict) -> list[tuple[str, bool]]:
    """Paths declared by the manifest. The bool is true when globs are allowed."""
    refs: list[tuple[str, bool]] = []

    def add(value: object, *, glob: bool = False) -> None:
        for item in _as_strings(value) if not isinstance(value, list) else _as_strings(value):
            refs.append((item, glob))

    def add_many(value: object, *, glob: bool = False) -> None:
        for item in _as_strings(value):
            refs.append((item, glob))

    background = manifest.get("background")
    if isinstance(background, dict):
        add(background.get("service_worker"))
        add(background.get("page"))
        add_many(background.get("scripts"))

    for group in manifest.get("content_scripts") or []:
        if isinstance(group, dict):
            add_many(group.get("js"))
            add_many(group.get("css"))

    for key in ("action", "browser_action", "page_action"):
        action = manifest.get(key)
        if isinstance(action, dict):
            add(action.get("default_popup"))
            for path in _icon_paths(action.get("default_icon")):
                refs.append((path, False))
            for path in _icon_paths(action.get("theme_icons")):
                refs.append((path, False))

    for path in _icon_paths(manifest.get("icons")):
        refs.append((path, False))

    add(manifest.get("options_page"))
    options_ui = manifest.get("options_ui")
    if isinstance(options_ui, dict):
        add(options_ui.get("page"))

    add(manifest.get("devtools_page"))
    side_panel = manifest.get("side_panel")
    if isinstance(side_panel, dict):
        add(side_panel.get("default_path"))

    overrides = manifest.get("chrome_url_overrides")
    if isinstance(overrides, dict):
        add_many(list(overrides.values()))

    sandbox = manifest.get("sandbox")
    if isinstance(sandbox, dict):
        add_many(sandbox.get("pages"), glob=True)

    rules = manifest.get("declarative_net_request")
    if isinstance(rules, dict):
        for rule in rules.get("rule_resources") or []:
            if isinstance(rule, dict):
                add(rule.get("path"))

    storage = manifest.get("storage")
    if isinstance(storage, dict):
        add(storage.get("managed_schema"))

    dictionaries = manifest.get("dictionaries")
    if isinstance(dictionaries, dict):
        add_many(list(dictionaries.values()))

    resources = manifest.get("web_accessible_resources")
    if isinstance(resources, list):
        for item in resources:
            if isinstance(item, str):
                refs.append((item, True))
            elif isinstance(item, dict):
                add_many(item.get("resources"), glob=True)

    for module in manifest.get("nacl_modules") or []:
        if isinstance(module, dict):
            add(module.get("path"))
    for plugin in manifest.get("plugins") or []:
        if isinstance(plugin, dict):
            add(plugin.get("path"))

    theme = manifest.get("theme")
    if isinstance(theme, dict) and isinstance(theme.get("images"), dict):
        add_many(list(theme["images"].values()))

    return refs


def _worker_paths(manifest: dict) -> set[str]:
    background = manifest.get("background")
    if not isinstance(background, dict):
        return set()
    paths = []
    if isinstance(background.get("service_worker"), str):
        paths.append(background["service_worker"])
    paths.extend(_as_strings(background.get("scripts")))
    cleaned = set()
    for path in paths:
        rel = _clean_path(path)
        if rel:
            cleaned.add(rel)
    return cleaned


def _module_worker(manifest: dict) -> bool:
    background = manifest.get("background")
    return isinstance(background, dict) and background.get("type") == "module"


def collect(root: Path) -> list[str]:
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        raise SystemExit(f"missing {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    if not isinstance(manifest, dict):
        raise SystemExit("manifest.json must be a JSON object")

    class Item:
        def __init__(self, rel: str) -> None:
            self.rel = rel
            self.module = False
            self.worker = False
            self.saw_html = False
            self.saw_css = False
            self.saw_module = False
            self.saw_worker = False

    items: dict[str, Item] = {}
    queue: list[Item] = []

    def enqueue(
        rel: str,
        *,
        module: bool = False,
        worker: bool = False,
        source: str,
    ) -> None:
        if _denied(rel):
            raise SystemExit(f"{source} points at a non-runtime path: {rel}")
        path = root / rel
        if not path.is_file():
            raise SystemExit(f"{source} points at a missing file: {rel}")
        item = items.get(rel)
        if item is None:
            item = Item(rel)
            item.module = module
            item.worker = worker
            items[rel] = item
            queue.append(item)
            return
        changed = False
        if module and not item.module:
            item.module = True
            changed = True
        if worker and not item.worker:
            item.worker = True
            changed = True
        if changed and item not in queue:
            queue.append(item)

    def add_ref(ref: str, *, glob: bool, source: str, module: bool = False, worker: bool = False) -> None:
        if glob and _has_glob(ref):
            matches = []
            for candidate in root.glob(ref):
                if not candidate.is_file():
                    continue
                rel = candidate.relative_to(root).as_posix()
                if _denied(rel):
                    continue
                matches.append(rel)
            if not matches:
                raise SystemExit(f"{source} glob matched no runtime files: {ref}")
            for rel in sorted(matches):
                enqueue(rel, module=module, worker=worker, source=source)
            return
        rel = _clean_path(ref)
        if rel is None:
            return
        enqueue(rel, module=module, worker=worker, source=source)

    enqueue("manifest.json", source="extension root")
    workers = _worker_paths(manifest)
    module_worker = _module_worker(manifest)
    for ref, allow_glob in _manifest_refs(manifest):
        rel = _clean_path(ref) if not (allow_glob and _has_glob(ref)) else None
        add_ref(
            ref,
            glob=allow_glob,
            source="manifest.json",
            worker=rel in workers if rel else False,
            module=module_worker and rel in workers if rel else False,
        )

    locale = manifest.get("default_locale")
    if isinstance(locale, str) and locale.strip():
        locale_root = root / "_locales"
        messages = sorted(locale_root.glob("*/messages.json")) if locale_root.is_dir() else []
        default_messages = locale_root / locale / "messages.json"
        if not default_messages.is_file():
            raise SystemExit(f"default_locale is set but _locales/{locale}/messages.json is missing")
        for message_file in messages:
            enqueue(message_file.relative_to(root).as_posix(), source="default_locale")

    while queue:
        item = queue.pop(0)
        path = root / item.rel
        if item.rel.endswith((".html", ".htm")) and not item.saw_html:
            item.saw_html = True
            for ref, as_module in _html_refs(path.read_text(encoding="utf-8-sig")):
                rel = _resolve(item.rel, ref)
                if rel is None:
                    continue
                enqueue(rel, module=as_module, source=item.rel)
        elif item.rel.endswith(".css") and not item.saw_css:
            item.saw_css = True
            text = path.read_text(encoding="utf-8-sig")
            found = [match.group(2) for match in _CSS_URL.finditer(text)]
            found.extend(match.group(2) for match in _CSS_IMPORT.finditer(text))
            for ref in found:
                rel = _resolve(item.rel, ref)
                if rel is None:
                    continue
                enqueue(rel, source=item.rel)
        if item.rel.endswith(".js") and item.worker and not item.saw_worker:
            item.saw_worker = True
            text = path.read_text(encoding="utf-8-sig")
            for block in _IMPORT_SCRIPTS.finditer(text):
                for ref in _QUOTED.findall(block.group(1)):
                    rel = _resolve(item.rel, ref)
                    if rel is None:
                        continue
                    enqueue(rel, worker=True, source=item.rel)
        if item.rel.endswith(".js") and item.module and not item.saw_module:
            item.saw_module = True
            text = path.read_text(encoding="utf-8-sig")
            for ref in _ES_IMPORT.findall(text):
                if not ref.startswith(("./", "../", "/")):
                    continue
                rel = _resolve(item.rel, ref)
                if rel is None:
                    continue
                enqueue(rel, module=True, source=item.rel)

    ordered = ["manifest.json"]
    ordered.extend(sorted(rel for rel in items if rel != "manifest.json"))
    return ordered


def _zip_time(path: Path) -> tuple[int, int, int, int, int, int]:
    stamp = path.stat().st_mtime if path.exists() else time.time()
    year, month, day, hour, minute, second, *_ = time.localtime(stamp)
    year = max(year, 1980)
    return (year, month, day, hour, minute, second)


def write_zip(root: Path, files: list[str], output: Path, top: str = TOP) -> list[str]:
    output.parent.mkdir(parents=True, exist_ok=True)
    names: list[str] = []
    directories = {f"{top}/"}
    for rel in files:
        parts = rel.split("/")
        for index in range(1, len(parts)):
            directories.add(top + "/" + "/".join(parts[:index]) + "/")
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for directory in sorted(directories):
            info = zipfile.ZipInfo(directory)
            info.date_time = _zip_time(root)
            info.external_attr = 0o040755 << 16
            archive.writestr(info, b"")
            names.append(directory)
        for rel in files:
            source = root / rel
            data = source.read_bytes()
            info = zipfile.ZipInfo(f"{top}/{rel}")
            info.date_time = _zip_time(source)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            info.flag_bits |= 0x800
            archive.writestr(info, data)
            names.append(f"{top}/{rel}")
    _assert_archive(output, top)
    return names


def pack(root: Path, output: Path) -> list[str]:
    return write_zip(root, collect(root), output)


def _assert_archive(path: Path, top: str) -> None:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
    if not names:
        raise SystemExit("zip is empty")
    tops = {name.split("/", 1)[0] for name in names}
    if tops != {top}:
        raise SystemExit(f"expected one top folder {top}/, found {sorted(tops)}")
    if f"{top}/manifest.json" not in names:
        raise SystemExit(f"{top}/manifest.json is missing")
    for name in names:
        if not name.startswith(f"{top}/"):
            raise SystemExit(f"path escapes the extension folder: {name}")
        parts = name.split("/")
        if any(part.lower() in DENY_DIRS for part in parts):
            raise SystemExit(f"non-runtime path in zip: {name}")
        if parts[-1].lower() in DENY_FILES:
            raise SystemExit(f"non-runtime file in zip: {name}")


def self_test() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary) / "extension"
        (root / "icons").mkdir(parents=True)
        (root / "styles").mkdir()
        (root / "assets" / "skip").mkdir(parents=True)
        (root / "vendor").mkdir()
        (root / "tests").mkdir()
        (root / "fixtures").mkdir()
        (root / "node_modules" / "left-pad").mkdir(parents=True)
        (root / "_locales" / "ja").mkdir(parents=True)
        (root / "_locales" / "en").mkdir()

        (root / "content.js").write_text(
            'const sample = \'import "./evil.js"\';\n',
            encoding="utf-8",
        )
        (root / "evil.js").write_text("/* must stay out */\n", encoding="utf-8")
        (root / "sw.js").write_text(
            'import "./lib.js";\nimportScripts("classic-extra.js");\n',
            encoding="utf-8",
        )
        (root / "lib.js").write_text('import "./more.js";\n', encoding="utf-8")
        (root / "more.js").write_text("export const n = 1;\n", encoding="utf-8")
        (root / "classic-extra.js").write_text("/* worker */\n", encoding="utf-8")
        (root / "popup.html").write_text(
            '<!doctype html><html><head>'
            '<link rel="stylesheet" href="styles/popup.css">'
            '<script type="module" src="popup.js"></script>'
            '<script src="classic-popup.js"></script>'
            '</head><body><img src="icons/badge.png"></body></html>\n',
            encoding="utf-8",
        )
        (root / "popup.js").write_text('import "./extra.js";\n', encoding="utf-8")
        (root / "extra.js").write_text("export const ready = true;\n", encoding="utf-8")
        (root / "classic-popup.js").write_text(
            'const hidden = "import \\"./nope.js\\"";\n',
            encoding="utf-8",
        )
        (root / "nope.js").write_text("/* classic script, not a module */\n", encoding="utf-8")
        (root / "styles" / "popup.css").write_text(
            "body { background: url('../icons/badge.png'); }\n@import \"./extra.css\";\n",
            encoding="utf-8",
        )
        (root / "styles" / "extra.css").write_text(
            "@font-face { src: url('../icons/font.woff2'); }\n",
            encoding="utf-8",
        )
        (root / "styles" / "app.css").write_text("html { color: black; }\n", encoding="utf-8")
        (root / "icons" / "icon.png").write_bytes(b"\x89PNG\r\n")
        (root / "icons" / "badge.png").write_bytes(b"\x89PNG\r\n")
        (root / "icons" / "font.woff2").write_bytes(b"woff")
        (root / "assets" / "ok.txt").write_text("ok\n", encoding="utf-8")
        (root / "assets" / "skip" / "nope.txt").write_text("no\n", encoding="utf-8")
        (root / "vendor" / "a.png").write_bytes(b"\x89PNG\r\n")
        (root / "vendor" / "note.txt").write_text("no\n", encoding="utf-8")
        (root / "unused.png").write_bytes(b"\x89PNG\r\n")
        (root / "tests" / "extension.spec.js").write_text("test\n", encoding="utf-8")
        (root / "tests" / "fixture.js").write_text("fixture\n", encoding="utf-8")
        (root / "tests" / "package.json").write_text("{}\n", encoding="utf-8")
        (root / "fixtures" / "sample.html").write_text("<p></p>\n", encoding="utf-8")
        (root / "node_modules" / "left-pad" / "index.js").write_text("module.exports\n", encoding="utf-8")
        (root / "package.json").write_text("{}\n", encoding="utf-8")
        (root / "README.md").write_text("readme\n", encoding="utf-8")
        (root / "playwright.config.js").write_text("export default {}\n", encoding="utf-8")
        (root / "pack_release.py").write_text("# packer\n", encoding="utf-8")
        (root / "_locales" / "ja" / "messages.json").write_text("{}\n", encoding="utf-8")
        (root / "_locales" / "en" / "messages.json").write_text("{}\n", encoding="utf-8")
        (root / "manifest.json").write_text(
            json.dumps(
                {
                    "manifest_version": 3,
                    "name": "sample",
                    "version": "1.0.0",
                    "default_locale": "ja",
                    "background": {"service_worker": "sw.js", "type": "module"},
                    "content_scripts": [
                        {"matches": ["*://example.com/*"], "js": ["content.js"], "css": ["styles/app.css"]}
                    ],
                    "action": {"default_popup": "popup.html", "default_icon": {"16": "icons/icon.png"}},
                    "web_accessible_resources": [
                        {"resources": ["assets/*", "vendor/*.png"], "matches": ["*://example.com/*"]}
                    ],
                }
            ),
            encoding="utf-8",
        )

        expected = {
            "manifest.json",
            "content.js",
            "styles/app.css",
            "sw.js",
            "lib.js",
            "more.js",
            "classic-extra.js",
            "popup.html",
            "styles/popup.css",
            "styles/extra.css",
            "popup.js",
            "extra.js",
            "classic-popup.js",
            "icons/icon.png",
            "icons/badge.png",
            "icons/font.woff2",
            "assets/ok.txt",
            "vendor/a.png",
            "_locales/ja/messages.json",
            "_locales/en/messages.json",
        }
        found = set(collect(root))
        if found != expected:
            missing = sorted(expected - found)
            extra = sorted(found - expected)
            raise SystemExit(f"self-test file list mismatch\nmissing: {missing}\nextra: {extra}")

        archive_path = Path(temporary) / "out.zip"
        names = pack(root, archive_path)
        with zipfile.ZipFile(archive_path) as archive:
            stored = archive.read("asiandocs-1080p/icons/icon.png")
        if stored != b"\x89PNG\r\n":
            raise SystemExit("zip bytes did not round-trip")
        if "asiandocs-1080p/manifest.json" not in names:
            raise SystemExit("manifest.json is not directly inside the top folder")
        banned_bits = ("tests/", "fixtures/", "node_modules/", "package.json", "README", "playwright", "evil.js", "nope.js", "unused.png")
        for name in names:
            if any(bit in name for bit in banned_bits):
                raise SystemExit(f"self-test zip contains {name}")

        broken = Path(temporary) / "broken"
        broken.mkdir()
        (broken / "manifest.json").write_text(
            json.dumps(
                {
                    "manifest_version": 3,
                    "name": "broken",
                    "version": "0",
                    "content_scripts": [{"matches": ["*://example.com/*"], "js": ["missing.js"]}],
                }
            ),
            encoding="utf-8",
        )
        try:
            collect(broken)
        except SystemExit:
            pass
        else:
            raise SystemExit("self-test expected a missing content script to fail")

    print("self-test ok")


def main() -> None:
    if "--self-test" in sys.argv:
        self_test()
        return
    root = Path(__file__).resolve().parent
    if root.name != TOP:
        raise SystemExit(f"pack_release.py must live in {TOP}/")
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("dist") / f"{TOP}.zip"
    names = pack(root, output)
    print(f"wrote {output}")
    for name in names:
        print(name)


if __name__ == "__main__":
    main()
