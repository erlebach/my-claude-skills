export const meta = {
  name: 'quiz-regen-round',
  description: 'Regenerate only the flagged items of a quiz, tier-descending, against the facts ledger',
  phases: [{ title: 'Regenerate', detail: 'one agent per affected tier, L3 then L2 then L1' }],
}

const a = typeof args === 'string' ? JSON.parse(args) : args

const ITEM_SCHEMA = {
  type: 'object',
  required: ['quiz', 'key', 'facts'],
  properties: {
    quiz: { type: 'string', description: 'ONLY the replacement items, numbered with their original numbers, in ascending order, as they go into quiz.md: exactly one `*` before the correct choice of each item (e.g. `*c) ...`). No tier labels, no answer list.' },
    key: { type: 'string', description: 'One composition-table ROW per replacement item (no header row), then one rationale paragraph per item.' },
    facts: { type: 'string', description: 'One line per replacement item, "N: the single fact this item tests".' },
  },
}

phase('Regenerate')

let ledger = a.ledger
const parts = []

for (const t of a.tiers) {
  const out = await agent(
    `You are REPAIRING specific items of an existing quiz for ${a.course}, covering: ${a.coverage}

Read the course profile at ${a.profilePath} for the tier definitions, the scope rule, and the item conventions.${a.difficulty ? ` DIFFICULTY, set by the author for this quiz and overriding the profile: ${a.difficulty}.` : ''}
Read the assigned material at ${a.packPath} — this pack is the ENTIRE assigned corpus. Anything not in it is out of scope.
Read the CURRENT quiz at ${a.quizPath} so you know what the other items already ask. You are replacing only the items listed below; every other item stays exactly as it is and your replacements must not collide with any of them.

The quiz marks every key with a leading '*', so you can see what each surviving item answers; use that only to avoid colliding with it. You may read the key rows and rationales of YOUR items in ${a.keyPath} to understand what was intended.

=== YOU ARE REPLACING THESE ${t.tier} ITEMS (${t.points} points each) ===

${t.items.map(it => `--- item ${it.n} — REASON IT FAILED ---\n${it.reason}`).join('\n\n')}

Every replacement must be STANDALONE: answerable from the item itself plus the C++ rules the course teaches, never from memory of a specific demo or example (its names, values, story, or a line the item does not print). Code in a stem contains whatever triggers the behaviour asked about, and comes before the question sentence: open with 'N. (P points) Consider the program:' or 'Consider the code fragment:' (an agentic item may use a one-line scenario such as 'A model wrote stem below:' instead). Write code a stem would otherwise describe in prose as a fragment; it must compile once the standard includes are added and bare statements are wrapped in a function.

Keep the SAME item numbers. Write one replacement per number, at the same tier and point value. A replacement must test a DIFFERENT fact from the one that failed where the failure was a duplicate; where the failure was ambiguity, an untaught term, or a wrong key, it may test the same underlying topic but must be built so the named defect cannot recur.

=== FACTS ALREADY SPENT by items you are NOT replacing ===
Do NOT test any of these, and do not test a narrower or partial version of one.

${ledger}

${a.formatRules}

${a.extraInstructions}`,
    { label: `regen:${t.tier}`, phase: 'Regenerate', model: 'opus', effort: 'medium', schema: ITEM_SCHEMA }
  )

  if (!out) return { error: `regeneration failed at tier ${t.tier}` }
  parts.push({ tier: t.tier, ...out })
  ledger += '\n' + String(out.facts || '')
  log(`${t.tier}: replaced items ${t.items.map(i => i.n).join(', ')}`)
  log(`===== ${t.tier} REPLACEMENT ITEMS =====\n${out.quiz}`)
  log(`===== ${t.tier} REPLACEMENT FACTS =====\n${out.facts}`)
}

return { parts }
