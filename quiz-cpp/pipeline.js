export const meta = {
  name: 'quiz-pipeline',
  description: 'Generate a course quiz, verify its sources, and review it key-blind',
  whenToUse: 'Driven by the quiz-cpp skill. Returns quiz, key, source check and blind review as text; the caller writes the four files.',
  phases: [
    { title: 'Generate', detail: 'one agent authors quiz + key together (opus, medium)' },
    { title: 'Check', detail: 'source verification and key-blind review, in parallel' },
  ],
}

// args: {
//   course, coverage, itemCount, composition, sourcePaths[], profilePath,
//   formatRules, extraInstructions
// }
// args may arrive as an object OR as a JSON-encoded string depending on how the
// Workflow tool serializes it — parse defensively. Getting this wrong silently
// makes every field undefined and produces a generic, unsourced quiz.
let a = args || {}
if (typeof a === 'string') {
  try {
    a = JSON.parse(a)
  } catch (e) {
    return { error: `args was a string and did not parse as JSON: ${e.message}` }
  }
}

const missing = ['coverage', 'itemCount', 'profilePath'].filter(k => !a[k])
const noSources = !a.packPath && !(a.sourcePaths || []).length
if (missing.length || noSources) {
  return { error: `missing required args: ${[...missing, ...(noSources ? ['sourcePaths or packPath'] : [])].join(', ')}` }
}

// A source pack (see sourcepack.js) is a verbatim distillation of the same YAML,
// ~5x smaller and one file instead of ~126. When one exists, the generator reads
// it instead — but the source-check agent always opens the ORIGINAL files, so the
// pack is never verified against itself.
const sources = a.packPath
  ? `- ${a.packPath}\n  (source pack: verbatim distillation of the assigned demos. Read this INSTEAD of the demo directories. Cite the 'Source:' path given inside each topic block, never the pack itself.)`
  : (a.sourcePaths || []).map(p => `- ${p}`).join('\n')

const QUIZ_SCHEMA = {
  type: 'object',
  required: ['quiz', 'key', 'unsourced'],
  properties: {
    quiz: { type: 'string', description: 'Full contents of quiz.md. No keys, no tier labels, no answer list.' },
    key: { type: 'string', description: 'Full contents of key.md, including the composition table with a Source column.' },
    unsourced: {
      type: 'array',
      description: 'Item numbers with no assigned-material source behind them. Empty if none.',
      items: { type: 'integer' },
    },
  },
}

const TEXT_SCHEMA = {
  type: 'object',
  required: ['report'],
  properties: { report: { type: 'string', description: 'Full markdown report.' } },
}

phase('Generate')

const authored = await agent(
  `You are authoring a quiz for ${a.course || 'a C++ course'}, covering: ${a.coverage}.

Read the course profile at ${a.profilePath} for the required composition, scope rule, and item conventions. Read these assigned sources in full before writing anything — not their index pages, not summaries:

${sources || '(none supplied — report every item as unsourced)'}

Generate roughly twice the target item count as candidates, then cut to ${a.itemCount}. ${a.composition || ''}

${a.formatRules || ''}

Return two complete documents.

quiz.md — the student paper. Numbered stems, lettered options, the point value printed on every stem, and NOTHING that reveals an answer: no asterisks, no tier labels, no answer list.

key.md — the instructor version. Open with a composition table: item number, tier, points, module, Source, agentic yes/no, key. The Source cell must be specific enough to reopen — a page plus its section, a slide number, a named example. Write 'none' where an item was invented rather than drawn from the material, and list those numbers in the unsourced field. Below the table, one paragraph per item: why the key is the key, and what misconception each wrong option catches.

${a.extraInstructions || ''}`,
  { label: 'author', phase: 'Generate', model: 'opus', effort: 'medium', schema: QUIZ_SCHEMA }
)

if (!authored) return { error: 'generation failed' }

// Models reliably emit HTML entities in code-bearing stems despite being told not
// to. These would go straight into LaTeX as literal &lt; text, so normalize here
// rather than relying on the instruction being obeyed.
const unescape = s => String(s || '')
  .replace(/&lt;/g, '<')
  .replace(/&gt;/g, '>')
  .replace(/&quot;/g, '"')
  .replace(/&#39;/g, "'")
  .replace(/&amp;/g, '&')   // last: an escaped & must not re-expand the others

authored.quiz = unescape(authored.quiz)
authored.key = unescape(authored.key)

// A generation agent once read the pack, authored ten items, compiled every stem —
// and then emitted the literal string "placeholder" into both fields. The schema was
// satisfied (a string is a string), so the run continued: the reviewer refused to
// review a placeholder, and the source-checker went off and verified an OLDER run's
// key.md that it found on disk, returning a confident report about the wrong items.
// Two agents and ~220k tokens spent on nothing. Fail here instead, in one second.
const DEGENERATE = /^(placeholder|todo|tbd|n\/a|none|\.\.\.)\.?$/i
const assertUsable = (name, text, minLen) => {
  const t = String(text || '').trim()
  if (!t) return `${name} came back empty`
  if (DEGENERATE.test(t)) return `${name} came back as the placeholder "${t}"`
  if (t.length < minLen) return `${name} is ${t.length} chars, below the ${minLen} floor — almost certainly a stub or a path rather than the document`
  return null
}

// ~600 chars per item is conservative: a real five-option L3 stem runs well past 1200.
const floor = Math.max(1000, 600 * Number(a.itemCount || 1))
const emitFault = assertUsable('quiz', authored.quiz, floor)
  || assertUsable('key', authored.key, Math.round(floor * 0.6))
if (emitFault) {
  log(`ABORT before the checking stages: ${emitFault}`)
  return {
    error: `generation emitted an unusable document — ${emitFault}. No files were written. Re-run with an edited prompt (an unchanged prompt replays this result from cache).`,
    quizLength: String(authored.quiz || '').length,
    keyLength: String(authored.key || '').length,
  }
}

// Cheap sanity check on coverage: the caller usually asks for a specific numbered
// range, so a document missing most of those numbers is worth flagging even if long.
const wanted = String(a.composition || '').match(/\b(\d+)\s+through\s+(\d+)\b/i)
if (wanted) {
  const [lo, hi] = [Number(wanted[1]), Number(wanted[2])]
  const missing = []
  for (let n = lo; n <= hi; n++) {
    if (!new RegExp(`(^|\\n)\\s*${n}\\.`, 'm').test(authored.quiz)) missing.push(n)
  }
  if (missing.length) log(`WARNING: quiz.md has no stem numbered ${missing.join(', ')}`)
}

phase('Check')

// Both checks depend only on the finished quiz, so they run concurrently.
// The reviewer is never given the key — and at this point no key exists on disk.
const [sourceCheck, review] = await parallel([
  () => agent(
    `Verify the sources cited by a quiz answer key. Here is key.md:

---
${authored.key}
---

If the text between those delimiters is not an answer key — it is empty, a placeholder, a file path, or a summary — STOP and report exactly that. Do NOT search the repository for another key.md to verify instead. An earlier run of this pipeline was handed a placeholder, went looking, found a previous run's key on disk, and returned a detailed and entirely confident report about items nobody had asked about. A one-line "no key was supplied" is far more useful than a thorough answer to the wrong question.

For every item, open the source it cites and report:

- the cited source, and whether it exists
- SUPPORTED / PARTIAL / UNSUPPORTED / NO SOURCE — does the cited section actually support what the item asserts?
- any term the item depends on that the cited source never introduces

- PLATFORM-DEPENDENT, if the item's key rests on a recorded observation — a printed value, a crash, an exit code, a sanitizer message, a diagnostic — rather than on a rule. The source material's runnable variants were recorded on one machine; their behavior is not portable, and the key must come from the explanation and the standard instead.

The vocabulary check is the one that matters most: an item testing a term the course has not taught will pass every other stage, because a reviewer who knows the subject will answer it without noticing anything is missing.

Return a markdown report, one section per item, ending with a summary table.`,
    { label: 'source-check', phase: 'Check', model: 'opus', effort: 'medium', schema: TEXT_SCHEMA }
  ),
  () => agent(
    `You are sitting this quiz cold, as a strong student would. No answer key exists — none has been written, and nothing you can reach contains one. Answer from the printed items and your own knowledge alone. Do not search for the source material or the course site.

---
${authored.quiz}
---

If the text between those delimiters is not a quiz — it is empty, a placeholder, a file path, or a summary — STOP and report exactly that. Do not invent quiz items and then review your own inventions, and do not go looking for a quiz elsewhere.

Write a review. For EVERY question:

1. Your answer, and your confidence (high / medium / low).
2. One paragraph per option, including the one you chose: the strongest case a well-prepared student could make FOR it, then why it is finally right or wrong. Do not skip options you consider obviously wrong — say why they are obviously wrong.
3. For each wrong option, the specific misconception a student holding it would have — or WEAK if it would catch nobody.
4. A difficulty estimate: time needed, and the fraction you would expect to answer correctly.
5. AMBIGUOUS, if two or more options are genuinely defensible — name them and give the argument for the second. This is the most important output. Be adversarial: actively try to construct a defense for a second option before concluding an item is clean.

Also flag: anything factually wrong in a stem; code that would not compile where that is not the point of the item; any option whose wording gives the key away by being longer, more hedged, or more precise than its neighbours; and — mark these PLATFORM-DEPENDENT — any item whose key would change with a different compiler, operating system, architecture, or optimization level. Students sit this on their own machines; an answer that holds only on arm64 macOS with clang is not an answer.

End with a summary table: question, your answer, confidence, AMBIGUOUS yes/no.`,
    { label: 'blind-review', phase: 'Check', model: 'opus', effort: 'high', schema: TEXT_SCHEMA }
  ),
])

log(`authored ${a.itemCount} items; unsourced: ${authored.unsourced.length ? authored.unsourced.join(', ') : 'none'}`)

return {
  quiz: authored.quiz,
  key: authored.key,
  source_check: sourceCheck ? sourceCheck.report : 'SOURCE CHECK FAILED — stage returned nothing.',
  analysis: review ? review.report : 'BLIND REVIEW FAILED — stage returned nothing.',
  unsourced: authored.unsourced,
}
