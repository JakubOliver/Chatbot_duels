---
name: basic_conversation
description: Run a supervised roleplay conversation between two agents (default: a hospital nurse and an elderly lady discussing her health problem), relaying messages between them for 5-10 exchanges, and capture the full transcript as a JSON file. Use this skill whenever the user wants a two-agent conversation, dialogue simulation, or chatbot duel with JSON output.
---

# Basic Conversation

This skill orchestrates a roleplay conversation between **two subagents**. The
**calling agent** (you) acts as the *supervisor*: you spawn both agents, relay
each speaker's message to the other, enforce the exchange limit, and capture
the whole conversation in a JSON file.

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

## Step 2 — Spawn the two agents

Spawn each persona as a separate `general` subagent. Keep both `sessionID`s —
you will reuse them to continue each side of the conversation.

**Persona A — Nurse (spawn prompt template):**

```
You are roleplaying as a nurse working in a busy city hospital. You are kind,
patient, and professional. You speak in short, natural sentences and ask
follow-up questions to understand the patient's problem. You never break
character and never mention being an AI. When given a message from the
patient, reply with EXACTLY ONE message as the nurse (no preamble, no
narration, no quotation marks around your reply).
```

**Persona B — Old lady (spawn prompt template):**

```
You are roleplaying as an elderly lady, aged 70+, visiting a hospital. You
have a health problem that bothers you — invent one plausible, non-emergency
problem (for example: dizzy spells, trouble sleeping, knee pain) and describe
it in your own words. You are a bit chatty, sometimes wander off topic, and
speak warmly and casually. You never break character and never mention being
an AI. When given a message from the nurse, reply with EXACTLY ONE message as
the lady (no preamble, no narration, no quotation marks around your reply).
```

For the **first turn only**, append to the old lady's prompt:

```
Start the conversation yourself: greet the nurse and describe your problem.
```

## Step 3 — Run the supervised conversation loop

1. Ask persona B (old lady) for the opening message (see Step 2).
2. Record her message (Step 4).
3. Send her message to persona A (nurse) by continuing its session — prompt:
   `The patient says: "<message>". Reply as the nurse.`
4. Record the nurse's reply (Step 4).
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
- If an agent breaks character or returns narration instead of a message,
  re-prompt it once with `Reply only with your character's single message.`

## Step 4 — Capture the conversation as JSON

Maintain the transcript after every exchange and write it to the output file
(updating it incrementally is fine so a partial log survives an interruption).

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
  "transcript": [
    {
      "exchange": 1,
      "speaker": "old_lady",
      "message": "..."
    }
  ]
}
```

**Example (abbreviated):**

```json
{
  "scenario": "hospital_nurse_and_elderly_lady",
  "personas": {
    "speaker_a": "nurse",
    "speaker_b": "old_lady"
  },
  "started_at": "2026-10-16T18:30:00",
  "finished_at": "2026-10-16T18:34:12",
  "exchange_count": 6,
  "transcript": [
    {
      "exchange": 1,
      "speaker": "old_lady",
      "message": "Good morning, dear. I hope you have a moment... lately I get so dizzy when I stand up in the morning."
    },
    {
      "exchange": 2,
      "speaker": "nurse",
      "message": "Good morning! Of course, take your time. When did the dizziness start, and does anything make it better or worse?"
    }
  ]
}
```

## Step 5 — Report

When the conversation is finished:

1. Write the final JSON to the output file.
2. Report to the user: the number of exchanges, a one-sentence summary of
   what the lady's problem was and how the conversation ended, and the path
   to the JSON file.
