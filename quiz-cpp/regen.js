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
    quiz: { type: 'string', description: 'Student version of ONLY the replacement items, numbered with their original numbers, in ascending order. No asterisks, no tier labels, no answer list.' },
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

Read the course profile at ${a.profilePath} for the tier definitions, the scope rule, and the item conventions.
Read the assigned material at ${a.packPath} — this pack is the ENTIRE assigned corpus. Anything not in it is out of scope.
Read the CURRENT quiz at ${a.quizPath} so you know what the other items already ask. You are replacing only the items listed below; every other item stays exactly as it is and your replacements must not collide with any of them.

DO NOT read ${a.keyPath} for items other than the ones you are replacing — you may look at the key rows of YOUR items to understand what was intended.

=== YOU ARE REPLACING THESE ${t.tier} ITEMS (${t.points} points each) ===

${t.items.map(it => `--- item ${it.n} — REASON IT FAILED ---\n${it.reason}`).join('\n\n')}

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
