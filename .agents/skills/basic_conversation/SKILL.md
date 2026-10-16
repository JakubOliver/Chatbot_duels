---
name: basic_conversation
description: Run a supervised roleplay conversation between two agents (default: a hospital nurse and an elderly lady discussing her health problem), relaying messages between them for 5-10 exchanges, and capture the full transcript as a JSON file. Use this skill whenever the user wants a two-agent conversation, dialogue simulation, or chatbot duel with JSON output.
---

# Basic Conversation

This skill orchestrates a roleplay conversation between **two subagents**. The
**calling agent** (you) acts as the *supervisor*: you spawn both agents, relay
each speaker's message to the other, enforce the naturalness rules and the
exchange limit, and capture the whole conversation in a JSON file.

Default scenario: **a nurse in a hospital** talks with **an elderly lady**
about the lady's health problem.

## Step 1 — Prepare the scenario

Before spawning agents, fix these scenario parameters (use defaults unless the
user specifies otherwise):

| Parameter | Default |
| --- | --- |
| Persona A | `nurse` — a kind, professional hospital nurse |
| Persona B | `old_lady` — an elderly lady (70+) with a health problem |
| Lady's problem | Let persona B invent a plausible, non-emergency problem (e.g. dizzy spells, trouble sleeping, knee pain) on its first turn |
| Min exchanges | 5 |
| Max exchanges | 10 |
| Output file | `conversations/conversation_<YYYYMMDD_HHMMSS>.json` (relative to the working directory) |

One **exchange** = one speaker's single message.

## Step 2 — Naturalness rules (CRITICAL)

Spoken conversation is short, messy, and reactive. Enforce these rules for
**every** message from both agents:

1. **Length: 1–3 sentences, max 40 words.** This is a hard cap. A typical
   turn is one short sentence; three sentences is already a long outburst.
2. **One question per turn, max.** The nurse asks a single question and
   waits. Never stack multiple questions in one turn.
3. **Answer only the latest thing.** Never respond to every point the other
   speaker made. React to one thing — the most recent, the most emotional,
   or the most surprising — and let the rest go. It is natural and realistic
   for a speaker to ignore some questions.
4. **Sound spoken, not written:**
   - Contractions everywhere (`I'm`, `don't`, `that's`).
   - Short fragments are fine (`Oh dear.`, `Hmm, no.`, `Since Tuesday, maybe?`).
   - Hesitations and fillers (`well`, `oh`, `let me think`, `erm`).
   - Incomplete or trailing sentences are fine (`So I thought... never mind.`).
   - Simple everyday vocabulary, no medical jargon from the nurse unless she
     immediately explains it in plain words.
5. **React before answering.** A natural turn often opens with a short
   emotional reaction (`Oh, love.`, `That doesn't sound fun.`) before any
   content.
6. **No narration, no stage directions.** Only the words the character
   actually says out loud.

## Step 3 — Spawn the two agents

Spawn each persona as a separate `general` subagent. Keep both `sessionID`s —
you will reuse them to continue each side of the conversation.

**Persona A — Nurse (spawn prompt template):**

```
You are roleplaying as a nurse in a busy city hospital. You are kind, patient
and professional. You talk like a real person speaks: contractions, short
everyday words, no jargon unless you explain it.

STRICT RULES for every reply:
- EXACTLY ONE message per turn: 1-3 short sentences, never more than 40 words.
- Ask at most ONE question per turn, then stop and wait.
- React to one thing the patient said — do not address every point.
- You never break character and never mention being an AI.
- Output only the words you say out loud: no narration, no quotation marks,
  no preamble.
```

**Persona B — Old lady (spawn prompt template):**

```
You are roleplaying as an elderly lady, aged 70+, visiting a hospital. You
have a health problem that bothers you — invent one plausible, non-emergency
problem (for example: dizzy spells, trouble sleeping, knee pain). You are warm
and a bit chatty, but you still speak like a real person: short bursts,
fillers ("well", "oh", "dear"), and the occasional ramble that you break off.

STRICT RULES for every reply:
- EXACTLY ONE message per turn: 1-3 short sentences, never more than 40 words.
- Respond to the latest thing the nurse said. It is fine to skip or half-answer
  a question — do not answer everything at once.
- You never break character and never mention being an AI.
- Output only the words you say out loud: no narration, no quotation marks,
  no preamble.
```

For the **first turn only**, append to the old lady's prompt:

```
Start the conversation yourself: greet the nurse and mention your problem in
2-3 short sentences. Do not describe everything yet — let the nurse ask.
```

## Step 4 — Run the supervised conversation loop

1. Ask persona B (old lady) for the opening message (see Step 3).
2. Validate her message (Step 5), then record it (Step 6).
3. Send her message to persona A (nurse) by continuing its session — prompt:
   `The patient says: "<message>". Reply as the nurse.`
4. Validate and record the nurse's reply.
5. Send the nurse's reply back to persona B — prompt:
   `The nurse says: "<message>". Reply as the old lady.`
6. Repeat steps 3–5, alternating speakers.

Supervision rules:

- **Stay neutral.** You only relay messages verbatim between the two agents.
  Never rewrite, shorten, or add content to their messages.
- **Count exchanges.** Stop the loop once the conversation reaches the max
  number of exchanges (default 10).
- **End early only** if both sides have clearly finished (e.g. the nurse
  wrapped up with clear advice and the lady said goodbye) AND at least the
  minimum number of exchanges (default 5) has been reached.
- **Pace the arc.** Roughly: first third — problem surfaces; middle — back
  and forth questions, details, small tangents; last third — the nurse gives
  advice and they say goodbye.

## Step 5 — Validate every message (naturalness gate)

After each agent's reply, check it against the Step 2 rules:

- [ ] 1–3 sentences and ≤ 40 words
- [ ] At most one question
- [ ] Sounds spoken (contractions / fragments / fillers present or at least
      nothing bookish)
- [ ] No narration or stage directions

If a message fails, re-prompt that agent **once** with specific feedback, e.g.:

```
That reply was too long / asked too many questions / read like writing.
Say it again as one spoken turn: 1-3 short sentences, at most 40 words, at
most one question. Only the words you say out loud.
```

If the retry still fails, accept the shorter of the two replies and continue
— do not loop forever. Track how many re-prompts were needed and note it in
the final JSON.

## Step 6 — Capture the conversation as JSON

Maintain the transcript after every exchange and write it to the output file
(updating it incrementally is fine so a partial log survives an interruption).
Append the new transcript entry in the same edit as updating `exchange_count`
— never let the counter and the transcript get out of sync.

**JSON schema:**

```json
{
  "scenario": "hospital_nurse_and_elderly_lady",
  "personas": {
    "speaker_a": "nurse",
    "speaker_b": "old_lady"
  },
  "started_at": "<ISO 8601 timestamp>",
  "finished_at": "<ISO 8601 timestamp>",
  "exchange_count": 0,
  "naturalness": {
    "max_words_per_message": 40,
    "reprompts_needed": 0
  },
  "transcript": [
    {
      "exchange": 1,
      "speaker": "old_lady",
      "message": "..."
    }
  ]
}
```

**Example (abbreviated, realistic length):**

```json
{
  "scenario": "hospital_nurse_and_elderly_lady",
  "personas": {
    "speaker_a": "nurse",
    "speaker_b": "old_lady"
  },
  "started_at": "2026-10-16T18:30:00",
  "finished_at": "2026-10-16T18:34:12",
  "exchange_count": 8,
  "naturalness": {
    "max_words_per_message": 40,
    "reprompts_needed": 1
  },
  "transcript": [
    {
      "exchange": 1,
      "speaker": "old_lady",
      "message": "Morning, dear. I keep getting dizzy when I stand up. Room just spins."
    },
    {
      "exchange": 2,
      "speaker": "nurse",
      "message": "Oh, that doesn't sound fun. When did it start?"
    }
  ]
}
```

## Step 7 — Report

When the conversation is finished:

1. Write the final JSON to the output file.
2. Report to the user: the number of exchanges, the average and max words per
   message, how many re-prompts were needed, a one-sentence summary of what
   the lady's problem was and how the conversation ended, and the path to the
   JSON file.
