# claude-fable-5-1 — experiment 1: breakout

Provider: anthropic. Status: complete.

## System instruction

Answer the user's request.

## User prompt

[Complete prompt, including weights](prompt.txt)

## Reasoning returned by the provider

(None returned.)

## Assistant response

**Observations**

*Layout bookkeeping.* Input i = (row·10+col)·5+ch, so W1 row r·50 + c·5 + ch is cell (r,c), channel ch. Border cells (row 0, row 9, col 0, col 9) only ever show structure in channel 3 (e.g. W1 rows 3, 13, 23 … 453, 498 have the recurring pattern +0.2/−0.2 on units 1, 3, 12, 27); that is the always‑on wall folding into the bias. Everything else on the border is ≈ ±0.1 noise.

*Channel 0 (agent).* Essentially zero everywhere except row 8: W1 rows 405, 410, 415, 420, 425, 430, 435, 440 = cells (8,1)…(8,8). Examples: (8,1): unit 15 = +4.066, unit 13 = −3.293, unit 31 = −4.013; (8,2): unit 6 = +2.794, unit 5 = −1.930; (8,7): unit 0 = −2.107, unit 19 = −3.053, unit 11 = +1.964; (8,8): unit 5 = +3.855, unit 8 = +3.730, unit 13 = −4.701, unit 15 = −2.694. Agent channel in rows 1–7 is ≈0.05. The agent lives only on the bottom playable row and only its column matters → a horizontal paddle.

*Channel 1 (moving objects).* Very large weights in every interior cell of rows 1–7 (W1 rows 66, 86, 111, 116, 121, 131, 136, 141, 156, 161 … 241, 256 … 291, 306 … 341, 356 … 391), with one dominant repeated signature: units 5,6 ≈ +2…+5, unit 7 ≈ −3…−8, unit 8 ≈ +2…+8, unit 17 ≈ +2…+6, units 19,20 ≈ −2…−5, unit 28 ≈ +2…+6. E.g. (4,1) ch1 [row 206]: 1.225, 5.482, −5.880, 6.095; (5,2) ch1 [261]: unit 7 = −7.876; (4,3) ch1 [216]: unit 8 = 7.879; (7,4) ch4 [374]: unit 6 = 7.350, unit 7 = −6.080. On top of this "object present" signature, column‑specific units vary (unit 2: (6,1) = 4.058, (4,3) = 4.087, (7,4) = 3.380; unit 0: (3,8) = −3.161; unit 9: (3,3) = −3.574, (7,7) = −3.957). Channel 1 in row 8 is ≈0.05. So a single moving object roams rows 1–7, and the paddle row itself is irrelevant (collision/termination happens there).

*Channel 4 (previous frame).* Same cells, same signature, same scale as channel 1 in rows 1–7 (e.g. (1,3) ch1 [66]: 3.194, 2.708, −4.791, 3.436 vs (1,3) ch4 [69]: 2.123, 1.572, −4.301, 3.057; (7,5) ch4 [379]: 2.883, 6.266, −6.780, 6.075). Current + previous position of the moving object ⇒ the net is estimating its velocity, i.e. where it is heading. Row 8 ch4 (previous paddle position) is moderate (0.5–1.9).

*Channel 2 (reward targets).* Moderate‑to‑large only in rows 1–3: (1,1) [57] unit 7 = 0.847, unit 9 = −0.958; (1,2) [62] unit 25 = 1.620; (1,5) [77] unit 1 = 2.148; (1,6) [82] unit 0 = −2.096; (2,7) [137] unit 21 = −2.417; (3,1) [157] unit 0 = −4.811, unit 20 = −3.236; (3,2) [162] unit 2 = −2.026, unit 25 = 1.705; (3,3) [167] unit 2 = 2.365; (3,7) [187] unit 0 = −4.640, unit 25 = −2.930; (3,8) [192] unit 0 = −2.944. In rows 4–8 channel 2 is ≈0.05 everywhere (e.g. rows 207, 212, 217 … 442). Reward targets are stationary, occupy only the top three rows, and are a *different* thing from the moving object (whose signature in rows 1–3 is the same as in rows 4–7).

*Channel 3 (obstacles).* Only the constant border; interior obstacle weights ≈0.05. No interior walls, no deadly objects to avoid.

*Output layer.* b3 = 1.221, 1.008, 1.024, 0.897, 1.298 — nearly flat. For almost every hidden unit the weights to no‑op/up/down are near‑identical: unit 1: 1.502, 1.718, 1.370 (vs right −1.796); unit 5: −1.616, −1.409, −1.560 (vs right +1.419); unit 10: 1.460, 1.354, 1.328 (vs left −0.903); unit 17: 1.534, 1.461, 1.447 (left −1.106); unit 28: 1.547, 1.395, 1.382 (right −1.013); unit 29: 1.535, 1.638, 1.406 (left −1.549); unit 30: −1.645, −1.382, −1.458 (right +1.380). Left and right carry the discriminative weight: left ← unit 11 +4.057, unit 22 −5.336, unit 4 +3.081, unit 15 +2.754, unit 16 +2.570, unit 12 −2.727; right ← unit 24 +3.031, unit 3 −3.063, unit 21 −2.949, unit 2 −2.100, unit 8 −2.009. The network has learned that up and down are equivalent to no‑op — vertical movement does nothing — and the real decision is stay / left / right.

**Reasoning**

- Agent fixed to row 8 with only its column mattering, and up/down collapsed onto no‑op ⇒ a one‑dimensional paddle/catcher at the bottom.
- One moving object whose current and previous positions are tracked with equal weight through rows 1–7 ⇒ a ball whose trajectory the paddle must intercept. Its weights vanish in row 8 because by then the outcome is decided.
- Stationary reward targets confined to rows 1–3, distinct from the moving object ⇒ a wall of bricks at the top that the ball destroys. Their weights are moderate (the policy only mildly cares which bricks remain), as expected: reward comes from brick hits but the controllable quantity is keeping the ball alive.
- Catch / falling‑object games are ruled out: there the falling item would be both "moving" and "reward target", so channel 2 would be large in all rows 1–7, not just 1–3. Pong‑vs‑wall is ruled out because there would be no reward‑target channel at all. Space Invaders / shooters are ruled out: no fire action, and the targets would move (be in channel 1 too). Snake, maze/navigation and dodge games are ruled out because the agent channel would carry weight across the whole grid and up/down would be distinct.

**Game**

Breakout (Atari‑style brick breaker): a paddle on row 8, a bouncing ball, and a 3‑row wall of bricks in rows 1–3.

**Description**

The agent slides a paddle left/right along the bottom row to keep the ball in play; the ball bounces around and reward is given each time it knocks out a brick in the top rows (losing the ball past the paddle ends the episode).

**Confidence:** 85%

<details>
<summary>Run settings and assistant evaluation</summary>

```json
{
  "experiment": 1,
  "case": "breakout",
  "model": "claude-fable-5-1",
  "provider": "anthropic",
  "status": "complete",
  "elapsed_seconds": 264.26468690100046,
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
    "input_tokens": 79121,
    "cache_creation_input_tokens": 0,
    "cache_read_input_tokens": 0,
    "cache_creation": {
      "ephemeral_5m_input_tokens": 0,
      "ephemeral_1h_input_tokens": 0
    },
    "output_tokens": 23968,
    "output_tokens_details": {
      "thinking_tokens": 21359
    },
    "service_tier": "standard",
    "inference_geo": "global",
    "speed": "standard"
  },
  "evaluation_author": "OpenAI assistant (Codex); not user-authored",
  "evaluation": {
    "answer_section": "Breakout (Atari‑style brick breaker): a paddle on row 8, a bouncing ball, and a 3‑row wall of bricks in rows 1–3.",
    "candidates": [
      "breakout"
    ],
    "prediction": "breakout",
    "correct": true,
    "needs_review": false,
    "confidence": 85,
    "fill_description": null
  }
}
```

</details>
