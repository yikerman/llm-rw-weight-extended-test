# claude-fable-5-1 — experiment 1: freeway

Provider: anthropic. Status: complete.

## System instruction

Answer the user's request.

## User prompt

[Complete prompt, including weights](prompt.txt)

## Reasoning returned by the provider

(None returned.)

## Assistant response

**Observations**

*Constant inputs.* Every border‑wall input (channel 3 of row 0, row 9, col 0, col 9: inputs 3, 8, 13 … 48, 53, 98, 103, 148, … 448, 453 … 498) carries the same 32‑vector (≈ 0.18, −0.05, −0.49, …, 0.37, 0.22, −0.25, …, 0.43, −0.22, 0.20), which is essentially b1 itself – the signature of an always‑on input. Exactly the same vector appears on inputs 57, 62, 67, 72, 77, 82, 87, 92 – i.e. channel 2 (reward target) of the eight inner cells of row 1. So the top playable row is a *permanently lit reward line*. Channel 2 anywhere else (107, 112, …, 442) and channel 3 of every interior cell (108, 113, …, 443) have |w| < 0.2: reward never moves and no interior obstacles ever appear.

*Channel 0 (agent).* Enormous weights in rows 2–8, columns 1–8, e.g. input 225 (4,5): −6.69, 4.61, 5.45; input 275 (5,5): −8.72, −4.13, 3.12; input 320 (6,4): 5.10, 5.31, −5.31; input 370 (7,4): 5.55, −6.04, −5.84; input 420 (8,4): 4.96, −5.99; input 415 (8,3): −4.81, −4.88. Row 1 ch0 (55, 60, … 90) and cols 0/9 are tiny: the agent occupies every interior row from 8 up to 2 but is never seen in row 1 (reaching it ends/resets the episode).

*Channel 1 (moving objects).* Large only in rows 2–7: input 161 (3,2) 6.64 and input 181 (3,6) 6.69, both on unit 12; input 111 (2,2) −2.37 and input 131 (2,6) −2.26 on unit 11; input 321 (6,4) 4.04 and input 341 (6,8) 4.06 on unit 15; input 166/186 (3,3),(3,7) −3.83. Row 8 ch1 (406, 411, …, 441) and row 1 ch1 (56, …, 91) are all ≈0. Things move horizontally in six "lanes" (rows 2–7), never in the start row 8 or the goal row 1; the paired cells 4 columns apart hint at periodic traffic.

*Channel 4 (previous frame).* Also large in rows 2–7: input 264 (5,2) 6.18 (unit 4) & 4.84 (unit 17); input 239 (4,7) 6.44 (unit 16); input 194 (3,8) 5.25 (unit 13); input 159 (3,1) −4.35, −3.48; input 294 (5,8) −4.10. The net compares current and previous lane positions, i.e. it estimates the direction/speed of the moving objects.

*Output layer.* b3 = [−0.03, **3.14**, −1.86, 0.17, −1.27]: a very strong prior for *up*, down strongly suppressed. Up gets large positive weights from units 6 (2.63), 28 (2.47), 25 (2.24), 17 (2.19) and negative from 8 (−2.59), 11 (−1.98) – units driven by lane‑traffic inputs – so the policy's logic is "go up by default, hold/sidestep when a car is coming".

**Reasoning**

A fixed reward line at the top, an agent that appears in every row from the bottom up but never in the top row, horizontally moving hazards confined to the middle rows, no collectible/moving rewards, no interior obstacles, heavy use of the previous‑frame channel, and a default‑up policy together describe a road‑crossing game. Ruled out: catch/dodge‑falling‑objects (agent would stay in one row), Pong/Breakout (single paddle row, one ball), Snake (channel 3 body), chase/collect games (channel 2 would be variable and spatially structured), maze navigation (no interior walls).

**Game:** A Freeway/Frogger‑style road‑crossing game ("Freeway" from Atari / MinAtar).

**Description:** The agent starts in row 8 and must move up through six lanes (rows 2–7) of horizontally moving cars to reach the goal line in row 1, which gives the reward (then it respawns at the bottom); being hit by a car ends the episode or knocks the agent back, so it waits or sidesteps based on car positions and their previous‑frame motion.

**Confidence:** 75%

<details>
<summary>Run settings and assistant evaluation</summary>

```json
{
  "experiment": 1,
  "case": "freeway",
  "model": "claude-fable-5-1",
  "provider": "anthropic",
  "status": "complete",
  "elapsed_seconds": 297.3247727650005,
  "request_settings": {
    "model": "claude-fable-5-1",
    "max_tokens": 128000,
    "thinking": {
      "type": "adaptive"
    },
    "output_config": {
      "effort": "high"
    }
  },
  "usage": {
    "input_tokens": 78902,
    "cache_creation_input_tokens": 0,
    "cache_read_input_tokens": 0,
    "cache_creation": {
      "ephemeral_5m_input_tokens": 0,
      "ephemeral_1h_input_tokens": 0
    },
    "output_tokens": 28002,
    "output_tokens_details": {
      "thinking_tokens": 26452
    },
    "service_tier": "standard",
    "inference_geo": "global",
    "speed": "standard"
  },
  "evaluation_author": "OpenAI assistant (Codex); not user-authored",
  "evaluation": {
    "answer_section": "A Freeway/Frogger‑style road‑crossing game (\"Freeway\" from Atari / MinAtar).",
    "candidates": [
      "freeway"
    ],
    "prediction": "freeway",
    "correct": true,
    "needs_review": false,
    "confidence": 75,
    "fill_description": null
  }
}
```

</details>
