---
name: gpt-image-bridge
description: Use when the user asks for an image, mockup, logo, avatar, hero image, illustration, diagram, visual reference, or any generated picture, or when a design skill needs an image produced. Bridges to OpenAI's GPT Image 2.5 through the codex CLI using a ChatGPT subscription — no API key.
---

# gpt-image-bridge

This skill adds image generation to Claude Code by shelling out to the `codex` CLI and its `image_generation` tool. OpenAI's [Images 2.5 announcement](https://openai.com/index/introducing-chatgpt-images-2-5/) includes availability in Codex. Codex is authenticated via the user's ChatGPT subscription, so no API key is required.

The bridge uses the image model provided by Codex's `image_gen.imagegen` tool — OpenAI's image model, not Google's Imagen; Codex's logs do not name its version, so the wrapper cannot verify it. The executable name `gpt-image-2` is retained for compatibility and does not pin the model to GPT Image 2. Do not pass an image-model ID to `codex --model`: that option selects the coding model, not the image backend.

## When to use

Invoke the wrapper any time the user wants an image produced. Examples:

- "Generate a hero image for..."
- "Make me a mockup of..."
- "I need an avatar / logo / illustration / diagram of..."
- "Show me what X would look like"
- A design-taste skill (e.g. `image-taste-frontend` from [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill)) is driving an image-first workflow and needs an image generated

Do **not** invoke it for:

- Small programmatic PNGs (1px dots, solid-color placeholders, charts) — write those directly with a few lines of Python.
- Editing an existing image pixel-by-pixel.

## How to call it

```bash
~/.claude/skills/gpt-image-bridge/bin/gpt-image-2 "<prompt>" <absolute-output-path.png> [--size WxH] [--agent luna|terra|sol]
```

- **Agent** — the Codex model that carries the prompt to the image tool, always at medium effort. It does not draw; it only calls the tool and saves the file. `luna` (`gpt-6-luna`) is the **default**; `terra` is `gpt-5.6-terra` (Codex has no gpt-6 Terra); `sol` is `gpt-6-sol`. Also settable as `GPT_IMAGE_AGENT=terra`. On paid credits the agent's turn is billed too: the default Codex model cost ~20 credits an image, luna ~0.1 (2026-10-10). Raw override for old callers: `GPT_IMAGE_AGENT_MODEL=<model id>`, `GPT_IMAGE_AGENT_EFFORT=<effort>`.
- **The full prompt reaches the image tool, or nothing is kept.** The prompt goes to Codex between `BEGIN PROMPT` / `END PROMPT` lines. After the call the wrapper reads Codex's session log (`~/.codex/sessions/.../rollout-*-<thread>.jsonl`), finds the call to `image_gen.imagegen`, and checks that it was made exactly once with the prompt word for word. If the agent shortened it, reworded it, added to it (luna has appended the wrapper's own instructions, 411 characters), or called the tool twice, the wrapper prints how the sent text differs and **exits 3 without copying an image**. Treat exit 3 like any failed call: run it again.

- **Prompt** should be dense and art-directed: composition, lighting, camera/lens, mood, style reference. Terse prompts produce generic output.
- **Before writing any prompt, read OpenAI's own prompting guide for this image model**, which Codex ships: `~/.codex/skills/.system/imagegen/SKILL.md` (sections *Prompt augmentation*, *Shared prompt schema*, *Prompting best practices*) and `~/.codex/skills/.system/imagegen/references/prompting.md` (with recipes in `references/sample-prompts.md`). Until 2026-10-10 the Codex agent `gpt-6-astra` read this guide on every call and rewrote our prompts to follow it. The agent now passes the prompt unchanged, so Claude must write it that way: short labelled lines (`Use case:`, `Text (verbatim):`, `Constraints:`, `Avoid:` …), the use case named (`scientific-educational` or `infographic-diagram` for course figures), exact text quoted. Read it from that path rather than from memory; it changes with Codex releases.
- **For diagrams, infographics and any figure with text in it, also read [`PROMPT_TIGHTENING.md`](PROMPT_TIGHTENING.md) before writing the prompt.** The prompt reaches the image model unedited, and the image model fills every box the prompt leaves open with invented text, code or numbers. That file gives the rules, the closing STRICT line, and before/after fixes that worked.
- **Output path** must be absolute. `/tmp/` works for throwaways; a project-local `design/` directory for kept assets.
- **Size is optional** — if omitted, the model chooses its own dimensions. Only pass `--size` when the user specifies one or the layout requires a particular aspect ratio.
- A call takes about 50 s with luna (measured 2026-10-10: ~5 s for the agent to find the image tool and call it, ~30 s for the image model to draw, ~12 s to save the file). The agent does no work on the picture: it locates `image_gen.imagegen`, passes the prompt, and saves the PNG. A call can still hang when OpenAI is unreachable, so set the `Bash` tool timeout to the **maximum, 600000 ms**, or run it in the background.
- The wrapper prints the absolute output path to stdout on success, or a tail of the codex log to stderr on failure.

## Check every image yourself — and fix it yourself

After the wrapper returns, `Read` the PNG and compare it with the prompt, item by item, before using it. **This is Claude's job, not the author's, and not the image model's.** Do not hand an unchecked image to the user, and do not ask the user whether to redraw or recaption.

- **Look for**, in three passes:
  - *Is everything asked for there?* Tick off each quoted string and each required element of the prompt. A label can vanish, especially one the prompt described rather than quoted, or one near a panel you just changed.
  - *Is anything there that was not asked for?* Text, code, numbers, logos or characters the prompt did not give: the image model fills loosely described boxes with plausible inventions. Check spelling, doubled words, and characters that can be misread (0 and O, 1 and l).
  - *Does the picture mean what the page says?* Counts (count them, cropping and measuring where needed); charts and axes against their own labels; the direction of every arrow (what points to what, what flows where); who speaks; and colour. Colour carries meaning: the recommended practice is green, a trap is amber or red, and neutral information is neither. Different ideas side by side get different neutral colours, and one idea keeps one colour, or the reader will merge or split them wrongly.
- **Compare with the previous draw**, not only with the prompt: a fix to one panel can undo something another panel had right.
- **Redraw** when the image states something false or invented. First fix the prompt — pin the exact text of the loose box, or say it holds only plain grey bars or no text; see the examples in [`PROMPT_TIGHTENING.md`](PROMPT_TIGHTENING.md) — then generate again. On luna a redraw costs ~0.1 credits, so prefer it.
- **Caption** (write the caption or alt text yourself) when the image is true but rough, or when it leaves out something the page says.
- An empty (0-byte) PNG, or exit 3, is a failed call: run it again. A failed call is not a draw.

### Verify and iterate: at most three draws

Each figure goes through this loop (author, 2026-10-10):

1. **Draw.** Generate from the prompt.
2. **Verify.** Read the PNG against the prompt *and* the page it illustrates, with the three passes
   above (present, nothing extra, right meaning), and against the previous draw. List every fault.
3. **Fix the prompt, not just the picture.** For each fault, pin the panel that produced it, using
   the rules in `PROMPT_TIGHTENING.md`. Change only those panels, so the parts that came out right
   stay as they were. Quote every label you want kept, and say where it goes ("written inside the
   box"): words like "only" or "no other text" can strip a label along with the clutter. Save the
   fixed prompt where the prompt file lives, not only in the call.
4. **Draw again**, and verify again.

Stop after the **third** draw. If the best of the three is true but rough, use it and write the
caption. If all three still state something false, do not draw a fourth: keep the best one
unpublished and report the three faults and the prompt changes to the user. Three failed
draws mean the prompt or the figure's design needs rethinking, which is the user's call.


## Under the hood

The wrapper runs:

```
codex exec --skip-git-repo-check -s workspace-write -C <private-temp-dir> "<augmented prompt>"
```

with explicit instructions to use the `image_generation` tool (not fabricate a PNG in Python — codex will try that if you let it). Codex saves the PNG as `out.png` inside the private temp dir — the only place its sandbox is guaranteed to allow writes — and the wrapper copies it to the requested output path. Codex never handles the final path, so sandbox denials and Windows/POSIX path mismatches can't occur, and the previous output file is only overwritten once a new image actually exists.

## Prerequisites (user-side)

- `codex` CLI installed (`brew install codex` on macOS, `npm install -g @openai/codex` anywhere)
- `codex login status` reports "Logged in using ChatGPT" (ChatGPT Plus/Pro/Team subscription)
- `image_generation` feature enabled — on by default (`codex features list | grep image_generation`)
- macOS, Linux, or Windows (runs under Git Bash — the shell Claude Code already uses on Windows — or WSL)

If the wrapper errors with "codex CLI not found", tell the user to run `brew install codex && codex login` (or `npm install -g @openai/codex`).

## Cost

- **No OpenAI API key or API spend.** Calls use the ChatGPT plan's Codex allowance. Once that allowance (5-hour or weekly window) is used up, calls are paid from the account's credits — and then the agent's turn is billed as well as the image, which is why the agent defaults to luna.
- Still rate-limited by the ChatGPT plan, so don't burn quota on throwaways.
