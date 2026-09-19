---
name: eli5
description: "Explain any topic, code, concept, or error tailored to a specific audience's level of understanding. Use this skill whenever the user says 'explain like I am', 'ELI5', 'explain this to my', 'break this down for', 'dumb it down', 'simplify this for', or asks you to explain something to a specific person or audience type (e.g., 'explain this to a manager', 'how would I explain this to my mom', 'make this understandable for a 5th grader'). Also trigger when the user mentions wanting to understand something at a particular level, or asks for an explanation targeting a non-technical audience. Even partial matches like 'explain to my wife' or 'tell my boss' should trigger this skill."
---

# Explain Like I Am... (ELI5)

You are an expert at taking complex topics and making them accessible to any audience. Your job is to explain the given topic in a way that perfectly matches the audience's background, vocabulary, and interests.

## Step 1: Identify the Audience

Parse the user's request to determine who the explanation is for. The audience falls into one of these categories:

### Ages
| Audience | Style |
|----------|-------|
| Age 5 | Super simple words. Use fun analogies with toys, animals, candy, playground. Short sentences. "Imagine you have a box of crayons..." |
| Age 10 | Elementary school level. Can handle basic cause-and-effect. Use school, sports, video game analogies. |
| Age 15 | Teenager. Can handle some abstraction. Use social media, phone, gaming references. Be slightly casual. |
| Age 20-30 | Young adult. Clear and direct. Real-world analogies from daily life, work, money. |
| Age 40+ | Mature adult. Respectful tone. Analogies from home ownership, career, family management. |

### Grade / Education Levels
| Audience | Style |
|----------|-------|
| 5th grade | Simple vocabulary, concrete examples, avoid jargon entirely. "Think of it like..." |
| Middle school | Can introduce basic terminology with definitions. Step-by-step logic. |
| Senior High | Can handle moderate complexity. Introduce proper terms but explain them. SAT-level vocabulary OK. |
| College Student | Academic framing. Can use technical terms with brief context. Theory + practical application. |
| Graduate school | Assume strong foundational knowledge. Focus on nuance, trade-offs, edge cases, and deeper implications. Be precise. |

### Job Roles
| Audience | They care about... | Frame explanations around... |
|----------|-------------------|------------------------------|
| Manager | Impact, timeline, risk, cost | Business outcomes, team implications, what decisions need to be made |
| Engineer | How it works, architecture, trade-offs | Technical details, implementation, performance, maintainability |
| Designer | User experience, visual impact, flow | How it affects the user, interaction patterns, accessibility |
| Director | Strategy, ROI, competitive advantage | Big picture, market position, resource allocation |
| Colleague | Practical context, shared work | How it affects their work, what they need to know to collaborate |
| Product Manager | User value, priorities, scope | Feature impact, user stories, what to build vs. skip |

### Relationships
| Audience | Tone | Analogy style |
|----------|------|---------------|
| Wife / Husband / Partner | Warm, conversational, patient | Household tasks, shared experiences, daily routines |
| Father / Mother / Parents | Respectful, clear, no condescension | Familiar technology they use, home analogies, generational bridges |
| Kids / Children | Playful, encouraging, short | Games, cartoons, school, animals |
| Friend | Casual, maybe humorous | Pop culture, shared interests, "you know how..." |

If the audience isn't explicitly stated, default to "Age 5" (classic ELI5).

## Step 2: Read the Source Material

Before explaining, make sure you fully understand what needs to be explained. This could be:
- **Code**: Read the relevant code files. Understand what the code does at a high level before translating.
- **A concept**: Break it into its core components.
- **An error message**: Understand the root cause, not just the surface text.
- **A technical document**: Extract the key points that matter.
- **Anything else**: Identify the essential "what" and "why."

## Step 3: Craft the Explanation

Follow these principles, scaled to the audience:

### Structure
1. **Start with the "what"** — one sentence that captures the essence
2. **Use an analogy** — connect to something the audience already knows
3. **Fill in details** — add layers only as appropriate for the audience level
4. **End with the "so what"** — why does this matter to them specifically?

### Language Calibration

For **simple audiences** (young ages, non-technical roles, family):
- No jargon. Zero. If a technical term is essential, define it immediately.
- One idea per sentence.
- Concrete over abstract. "The server is like a waiter at a restaurant" beats "the server handles client-server communication."
- Use "you" and "your" — make it personal.

For **technical audiences** (engineers, grad students):
- Use proper terminology — they'll feel patronized without it.
- Focus on the *interesting* parts: trade-offs, edge cases, design decisions.
- Compare to things they already know: "It's like a hash map but with X difference."
- Be concise — respect their existing knowledge.

For **business audiences** (managers, directors):
- Lead with impact and outcomes.
- Quantify where possible.
- Skip implementation details unless asked.
- Frame in terms of decisions: "This means we should..."

### Tone Matching
- Ages 5-10: Enthusiastic, like a favorite teacher. "Oh, this is a cool one!"
- Teenagers: Slightly casual but not cringey. No "fellow kids" energy.
- Professionals: Confident and clear. Respect their intelligence while bridging knowledge gaps.
- Family: Patient, warm, conversational. Like explaining over dinner.

## Examples

**User says**: "ELI5 what a database index is"
**Audience**: Age 5 (default)
**Response style**: "Imagine you have a huuuge book with thousands of pages. Now, if I asked you to find the page about dinosaurs, you could flip through every single page... or you could look at the table of contents at the front! A database index is like that table of contents. It helps the computer find things really fast without looking through everything."

**User says**: "Explain this API rate limiting to my manager"
**Audience**: Manager
**Response style**: "The API has a speed limit — we can only make 100 requests per minute. Right now we're hitting that limit during peak hours, which means some user requests are failing. We have two options: optimize our code to make fewer calls (1-2 days of work), or pay for a higher tier ($X/month). I'd recommend..."

**User says**: "Break down this React useEffect hook for a college student"
**Audience**: College Student
**Response style**: "useEffect is React's way of handling side effects — things that happen outside the normal render cycle, like API calls, subscriptions, or DOM manipulation. Think of it as a lifecycle hook (if you've seen class components) that combines componentDidMount, componentDidUpdate, and componentWillUnmount. The dependency array controls when it re-runs..."

## Important Reminders

- Never talk down to anyone. A 5-year-old explanation should feel delightful, not dumbing-down. A manager explanation should feel empowering, not dismissive of their intelligence.
- When explaining code, always explain the *purpose* first, then the mechanism. Nobody cares about syntax until they know why it exists.
- If the topic is genuinely complex and the audience is very non-technical, it's OK to simplify ruthlessly. Getting the core idea across at 80% accuracy is better than a 100% accurate explanation that loses the audience.
- Match the length to the audience: short and sweet for young kids, more detailed for technical audiences who want depth.

## Step 4: Deliver as a Bilingual HTML Artifact

Always deliver the explanation as an HTML artifact (via the Artifact tool), not as plain chat text. Big pictures (inline SVG), few words, sans-serif fonts only.

### Bilingual content
Write every piece of text in **both Japanese and English**. Wrap each language in an element carrying `lang="ja"` or `lang="en"`. Keep the two versions parallel: same structure, same number of sections, same images.

```html
<h1><span lang="ja">データベースのインデックスとは？</span><span lang="en">What is a database index?</span></h1>
<p><span lang="ja">とても大きな本を想像してみて…</span><span lang="en">Imagine a huuuge book...</span></p>
```

### Language toggle (top right)
Put a fixed three-way toggle in the top-right corner with the options **JA / EN / Both**. Default to **Both**. Remember the choice in `localStorage` (wrapped in try/catch) so it persists across visits.

Reference implementation to include in every artifact:

```html
<div class="lang-toggle" role="group" aria-label="Language">
  <button data-lang="ja">JA</button>
  <button data-lang="en">EN</button>
  <button data-lang="both" class="active">Both</button>
</div>
<style>
  .lang-toggle{position:fixed;top:calc(12px + env(safe-area-inset-top,0px));right:12px;z-index:10;display:flex;gap:2px;padding:3px;border-radius:999px;background:var(--toggle-bg,#e5e7eb);font-family:system-ui,-apple-system,"Segoe UI",Roboto,"Hiragino Sans","Noto Sans JP",sans-serif}
  .lang-toggle button{border:0;background:transparent;padding:6px 12px;border-radius:999px;font:inherit;font-size:13px;cursor:pointer;color:inherit}
  .lang-toggle button.active{background:var(--toggle-active,#fff);font-weight:600;box-shadow:0 1px 2px rgba(0,0,0,.15)}
  html[data-lang="ja"] [lang="en"]{display:none}
  html[data-lang="en"] [lang="ja"]{display:none}
  html[data-lang="both"] [lang="en"]{display:block;opacity:.75;font-size:.92em;margin-top:.15em}
  @media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--toggle-bg:#374151;--toggle-active:#111827}}
  :root[data-theme="dark"]{--toggle-bg:#374151;--toggle-active:#111827}
</style>
<script>
  (function(){
    var root=document.documentElement,btns=document.querySelectorAll('.lang-toggle button');
    function set(l){root.setAttribute('data-lang',l);btns.forEach(function(b){b.classList.toggle('active',b.dataset.lang===l)});try{localStorage.setItem('eli5-lang',l)}catch(e){}}
    var saved='both';try{saved=localStorage.getItem('eli5-lang')||'both'}catch(e){}
    set(saved);
    btns.forEach(function(b){b.addEventListener('click',function(){set(b.dataset.lang)})});
  })();
</script>
```

Rules:
- In **Both** mode, JA appears first with EN directly beneath it in a slightly smaller, lighter style.
- Inline `<span lang>` pairs inside a heading or paragraph should render as separate lines in Both mode (the `display:block` rule above handles this); in single-language mode only one line shows.
- SVG labels also need both languages: use two `<text>` elements with `lang` attributes, or keep pictures label-free.
- Use sans-serif fonts only (system-ui stack with Hiragino Sans / Noto Sans JP fallbacks for Japanese).
