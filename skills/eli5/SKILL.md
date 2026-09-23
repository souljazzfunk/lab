---
name: eli5
description: Explain a topic like I'm a 5 year old. Use when the user types /eli5 [topic] or asks for a dead-simple picture explainer of how something works.
---

# eli5

Explain like I'm someone who knows nothing about this topic, using a HTML artifact with big pictures and few words. Sans-serif fonts only.

Write all text in both Japanese and English: every text element holds a `<span lang="ja">` and a `<span lang="en">`; SVG labels use one `<text>` with two `<tspan lang>` children. Add a fixed top-right toggle with JA / EN / Both (default Both, remembered in localStorage). Implement it as a global `window.setLang(mode)` (`mode` is `"ja"`, `"en"` or `"both"`) that sets `document.documentElement.dataset.lang` and re-lays out SVG labels; the buttons just call it. JA shows only `lang="ja"`, EN shows only `lang="en"`, Both shows JA with EN below it in a smaller, lighter style. For SVG, in Both mode set the EN tspan's `x` to the parent's `x` and `dy="1.15em"` so it stacks under the JA label; in EN mode reset that `dy` to 0 so the label doesn't drop a line. Labels get cut off easily, so: keep every label at least 100px from the left and right edges of the viewBox (estimate the longer EN string at 0.55em per character), leave 2 lines of empty height below the lowest label, never place more than 3 labels side by side in a 640px-wide row (use a second row instead), and set `svg{overflow:visible}`.

Next to it, add a Light / Dark toggle (default follows `prefers-color-scheme`, remembered in localStorage). Define all colors as CSS variables on `:root` for light and on `:root[data-theme="dark"]` for dark; SVG fills and strokes use those variables too (via `fill="var(--ink)"` etc.), so the whole page including diagrams switches together.

## Layout rules

- Give the page top padding at least the toggle bar's height so the bar never covers the title.
- SVGs scale: `width:100%; height:auto` with a `viewBox`, never a fixed pixel width wider than 400px.
- A shape holding a label must be wider than the label's longer line (EN at 0.55em/char, JA at 1em/char) plus 16px padding. Widen the shape or shorten the words; don't shrink the font below 13px.
- Captions and card labels: keep each language to 2 lines or fewer at 400px wide. Shorten the text rather than let it wrap into a tall column; put `word-break: keep-all; overflow-wrap: anywhere` on JA text so it breaks at natural points, and avoid a last line of only 1–2 characters.
- No fixed widths on text containers (use `max-width`), no `white-space: nowrap` on anything longer than a couple of words, and multi-column grids stack to one column under 480px.

## Check and fix layout (before publishing)

Save the page locally and run the bundled checker (Chromium + Playwright):

```
NODE_PATH="$(npm root -g)" node <this skill's dir>/scripts/check_layout.cjs page.html
```

It renders JA / EN / Both at 1024px and 400px and reports: horizontal page scroll, text overflowing its box or the screen, captions wrapping to more than 2 lines or leaving a stranded last line, SVG labels outside their figure, overlapping each other or spilling out of the shape behind them, and the fixed toggle covering content. Fix every reported issue using the layout rules above, then re-run until it prints `No layout issues found.` If Playwright isn't available, take screenshots of each mode at both widths instead and check the same list by eye.

## Add to the shelf

After publishing, add the new page to the index artifact "Artifact Shelf" (https://claude.ai/artifact/5Yk2Pzs2hRmdho9zCQJeQb): read it, insert a `<li>` at the top of the current month's list (create the month section if missing) with the title, an `ELI5` tag, and today's date (JST), bump the artifact count in the header, then republish it with `url` set so the link stays the same.

Topic: $ARGUMENTS
