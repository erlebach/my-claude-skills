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

const DUP_SCHEMA = {
  type: 'object',
  required: ['pairs'],
  properties: {
    pairs: {
      type: 'array',
      description: 'Pairs of items testing the same underlying fact. Empty if none.',
      items: {
        type: 'object',
        required: ['a', 'b', 'same_fact', 'confidence', 'why'],
        properties: {
          a: { type: 'integer' },
          b: { type: 'integer' },
          same_fact: { type: 'boolean' },
          confidence: { type: 'number', description: '0.0-1.0' },
          why: { type: 'string', description: 'What a student answering one already knows about the other, and which item contains which.' },
        },
      },
    },
  },
}

// The source check used to return prose only, which meant the set of flagged
// items had to be READ out of a 22-row table plus a totals line further down.
// That is a human-eye step in the middle of an automated loop, and it failed:
// four flagged items were reported as two. Verdicts are data now; the flagged
// set is a filter, not a judgement.
const SOURCE_SCHEMA = {
  type: 'object',
  required: ['report', 'verdicts'],
  properties: {
    report: { type: 'string', description: 'Full markdown report, one section per item.' },
    verdicts: {
      type: 'array',
      description: 'One entry per item. Every item must appear exactly once.',
      items: {
        type: 'object',
        required: ['item', 'verdict', 'platform_dependent', 'untaught_terms', 'note'],
        properties: {
          item: { type: 'integer' },
          verdict: { type: 'string', enum: ['SUPPORTED', 'PARTIAL', 'UNSUPPORTED', 'NO SOURCE'] },
          platform_dependent: { type: 'boolean', description: 'True if the key rests on a recorded observation rather than a rule.' },
          untaught_terms: { type: 'array', items: { type: 'string' }, description: 'Terms the item depends on that no cited source introduces. Empty if none.' },
          note: { type: 'string' },
        },
      },
    },
  },
}

const TIER_SCHEMA = {
  type: 'object',
  required: ['quiz', 'key', 'facts', 'unsourced'],
  properties: {
    quiz: { type: 'string', description: 'Numbered items for THIS TIER ONLY. No keys, no tier labels, no header.' },
    key: { type: 'string', description: 'Composition table rows and rationales for THIS TIER ONLY. No table header row.' },
    facts: { type: 'string', description: 'One line per item: "N: the single fact this item tests".' },
    unsourced: { type: 'array', items: { type: 'integer' } },
  },
}

// Round 2 and later: the caller splices regenerated items into a full quiz and
// wants only the checks re-run. Without this the loop is not a loop - each round
// would rewrite all 22 items and throw away the ones that already passed.
let authored
// Passing the documents by PATH rather than by value. On round 2+ the files
// already exist on disk, so structural key-blindness is gone either way: the
// reviewer could find key.md whether or not we hand it a path. What replaces it
// is an explicit instruction not to look, plus the fact that the reviewer is
// only ever given the quiz path. Copying 40k characters through the args by
// hand would add a transcription risk for a guarantee already spent.
if (a.preAuthoredPaths && a.preAuthoredPaths.quiz && a.preAuthoredPaths.key) {
  log(`checking quizzes on disk; generation skipped`)
  authored = {
    quiz: `(READ THE QUIZ FROM THIS FILE, and read nothing else: ${a.preAuthoredPaths.quiz})`,
    key: `(READ THE KEY FROM THIS FILE: ${a.preAuthoredPaths.key})`,
    facts: a.preAuthoredPaths.facts ? `(facts ledger: ${a.preAuthoredPaths.facts})` : '',
    unsourced: [],
  }
} else if (a.preAuthored && a.preAuthored.quiz && a.preAuthored.key) {
  log('checking a supplied quiz; generation skipped')
  authored = {
    quiz: a.preAuthored.quiz,
    key: a.preAuthored.key,
    facts: a.preAuthored.facts || '',
    unsourced: a.preAuthored.unsourced || [],
  }
} else {

phase('Generate')

// Tier-descending: L3 first, then L2, then L1. An L3 item is a multi-step trace
// whose fact-set is a superset of several L1 facts, so writing the small items
// first leaves the big ones nothing to build from - which is exactly how every
// cross-tier collision in Quiz 1's 40-item pool was produced. Each tier is told
// the facts the tiers above it already spent.
const TIERS = a.tiers || [
  { tier: 'L3', count: 3, points: 3 },
  { tier: 'L2', count: 5, points: 2 },
  { tier: 'L1', count: 14, points: 1 },
]

let ledger = ''
let nextNumber = 1
const parts = []

for (const t of TIERS) {
  const spent = ledger
    ? `\n=== FACTS ALREADY SPENT by higher-tier items ===\nDo NOT test any of these, and do not test a narrower or partial version of one. If the obvious item for a topic is already spent, find a different angle on that topic or use a different topic.\n\n${ledger}\n`
    : ''

  const out = await agent(
    `You are authoring the ${t.tier} items of a quiz for ${a.course || 'a C++ course'}, covering: ${a.coverage}.

Read the course profile at ${a.profilePath} for the tier definitions, the scope rule, and the item conventions. Read these assigned sources in full before writing anything — not their index pages, not summaries:

${sources || '(none supplied — report every item as unsourced)'}

Write exactly ${t.count} ${t.tier} items, worth ${t.points} points each, numbered ${nextNumber} through ${nextNumber + t.count - 1}.
${spent}
${a.formatRules || ''}

Return THREE things.

quiz — the student version of these items only. Numbered stems, lettered options, the point value printed on every stem, and NOTHING that reveals an answer: no asterisks, no tier labels, no answer list. No document header; these items are concatenated with the other tiers'.

key — the instructor version of these items only: one composition-table ROW per item (no header row) with item number, tier, points, module, Source, agentic yes/no, key letter; then one rationale paragraph per item saying why the key is the key and what misconception each wrong option catches. The Source cell must be specific enough to reopen — a topic YAML path plus its section. Write 'none' where an item was invented rather than drawn from the material, and list those numbers in unsourced.

facts — one line per item, formatted "N: the single fact this item tests". These lines become the ledger the LATER, EASIER tiers must avoid, so be specific and concrete. Write "shallow copy leaves two objects pointing at one block, and both destructors free it" — not "copy semantics". A vague line here causes a duplicate item two tiers later.

${a.extraInstructions || ''}`,
    { label: `author:${t.tier}`, phase: 'Generate', model: 'opus', effort: 'medium', schema: TIER_SCHEMA }
  )

  if (!out) return { error: `generation failed at tier ${t.tier}` }
  parts.push(out)
  ledger += (ledger ? '\n' : '') + String(out.facts || '')
  nextNumber += t.count
  log(`${t.tier}: ${t.count} items written; ledger now ${ledger.split('\n').length} facts`)
}

authored = {
  quiz: parts.map(p => p.quiz).join('\n\n---\n\n'),
  key: parts.map(p => p.key).join('\n\n'),
  facts: parts.map(p => p.facts).join('\n'),
  unsourced: parts.flatMap(p => p.unsourced || []),
}
}

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
// The floor guards a GENERATION. When the caller supplied the documents - by
// value or by path - there was no generation to go wrong, and a path directive
// is legitimately ~170 chars. Applying the floor there rejects correct input.
const supplied = Boolean(a.preAuthoredPaths || a.preAuthored)
const floor = Math.max(1000, 600 * Number(a.itemCount || 1))
const emitFault = supplied ? null : (assertUsable('quiz', authored.quiz, floor)
  || assertUsable('key', authored.key, Math.round(floor * 0.6)))
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
const wanted = supplied ? null : String(a.composition || '').match(/\b(\d+)\s+through\s+(\d+)\b/i)
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
const [sourceCheck, review, duplication] = await parallel([
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

Return a markdown report, one section per item, ending with a summary table.

ALSO fill the verdicts array: one entry per item, every item exactly once. The field platform_dependent is true whenever the key rests on a recorded observation - a printed value, a crash, an exit code, a diagnostic, an elision the standard permits but does not mandate - rather than on a rule that holds everywhere. Put terms the item depends on that no cited source introduces into untaught_terms. This array is read by a script and decides which items get regenerated, so an item you flag in the prose but NOT in the array will be silently kept.`,
    { label: 'source-check', phase: 'Check', model: 'opus', effort: 'medium', schema: SOURCE_SCHEMA }
  ),
  () => agent(
    `You are sitting this quiz cold, as a strong student would. Answer from the printed items and your own knowledge alone.

An answer key for this quiz DOES exist on disk, and so does the source material. Do not go looking for either. Opening them invalidates this review completely, because the one question worth answering here is whether the key is findable from the item alone - and a reviewer who has seen the key cannot tell you that. Do not search the filesystem, the repository, or the web. If you find yourself wanting to check something, that wanting is the signal the item may be ambiguous: write that down instead.

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

End with a summary table having EXACTLY these seven columns, in this order:

| Q | Answer | Confidence | AMBIGUOUS | weak_count | expected_pass | trap_quality |

- Q — the question number, digits only
- Answer — one letter, a-e
- Confidence — exactly one of: high, medium, low
- AMBIGUOUS — exactly "yes" or "no", nothing else; put your reasoning in the per-question section above, not in this cell
- weak_count — an integer 0-4: how many of the four wrong options you judged WEAK
- expected_pass — a decimal 0.00-1.00: the fraction of well-prepared students you expect to answer correctly
- trap_quality — an integer 1-5: how hard you had to work to rule out the strongest wrong option. 5 means you had to build a real defence and then dismantle it; 1 means every wrong option fell away in a clause.

This table is read by a script. A cell containing prose breaks it.`,
    { label: 'blind-review', phase: 'Check', model: 'opus', effort: 'high', schema: TEXT_SCHEMA }
  ),
  () => agent(
    `Find duplicated facts across a quiz. You are given every question AND every answer key, together, because a collision is usually invisible from the stems alone: two items can cite different source files while one item's key rests on the other item's exact fact.

QUESTIONS
---
${authored.quiz}
---

KEYS
---
${authored.key}
---

Report every PAIR of items that test the same underlying fact.

Judge the FACT, not the topic file. Two items citing the same file may test genuinely different rules; two items citing different files may test one rule from both sides. The second case is the one that matters and the one nothing else in this pipeline can see.

Where the two items are in different tiers, say which contains which. A three-point trace over several objects usually swallows a one-point recall item, and it matters which is which — the cheap one is the one to replace.

Be strict about confidence. Use 0.9+ only when a student who answers one has plainly answered the other. Use 0.5-0.7 when they overlap but each still tests something the other does not. When in doubt report the pair with low confidence rather than omitting it.`,
    { label: 'duplication', phase: 'Check', model: 'opus', effort: 'high', schema: DUP_SCHEMA }
  ),
])

log(`authored ${a.itemCount} items; unsourced: ${authored.unsourced.length ? authored.unsourced.join(', ') : 'none'}`)

return {
  quiz: authored.quiz,
  key: authored.key,
  source_check: sourceCheck ? sourceCheck.report : 'SOURCE CHECK FAILED — stage returned nothing.',
  verdicts: sourceCheck ? (sourceCheck.verdicts || []) : [],
  analysis: review ? review.report : 'BLIND REVIEW FAILED — stage returned nothing.',
  unsourced: authored.unsourced,
  facts: authored.facts,
  duplication: duplication ? duplication.pairs : [],
}
