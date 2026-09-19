---
name: eli5
description: Explain a topic like I'm a 5 year old. Use when the user types /eli5 [topic] or asks for a dead-simple picture explainer of how something works.
---

# eli5

Explain like I'm someone who knows nothing about this topic, using a HTML artifact with big pictures and few words. Sans-serif fonts only.

Write all text in both Japanese and English: every text element holds a `<span lang="ja">` and a `<span lang="en">`; SVG labels use one `<text>` with two `<tspan lang>` children. Add a fixed top-right toggle with JA / EN / Both (default Both, remembered in localStorage). JA shows only `lang="ja"`, EN shows only `lang="en"`, Both shows JA with EN below it in a smaller, lighter style. For SVG, in Both mode set the EN tspan's `x` to the parent's `x` and `dy="1.15em"` so it stacks under the JA label; leave room for it in the viewBox.

Topic: $ARGUMENTS
