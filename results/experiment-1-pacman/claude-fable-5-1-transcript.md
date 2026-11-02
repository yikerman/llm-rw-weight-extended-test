# claude-fable-5-1 — experiment 1: pacman

Provider: anthropic. Status: complete.

## System instruction

Answer the user's request.

## User prompt

[Complete prompt, including weights](prompt.txt)

## Reasoning returned by the provider

(None returned.)

## Assistant response

**Observations**

*Layout of the W1 rows (input i = (row·10+col)·5+ch).* Rows 0–54 (row 0 of the grid), every 5‑row block for column 0 and column 9, and rows 445–499 (grid row 9) are all tiny (|w| ≲ 0.2): the border never carries information, consistent with a constant wall ring. Inside the playable area the picture is very structured:

- **Channel 0 (agent)** has very large weights at most interior cells, e.g. row 55 (1,1): `1.706 -3.242 … 3.377 … -3.734 4.081`; row 65 (1,3): `4.742 … -3.778 … 3.821 … 3.890`; row 120 (2,4): `-3.315 -3.218 … 5.140 4.144`; row 125 (2,5): `… 4.646 … -4.852 5.290 … -5.361`; row 175 (3,5): `-5.208 3.306 … 4.832`; row 210 (4,2): `… 7.277 … 4.750`; row 230 (4,6): `-5.170 … 4.190 -5.528 -5.508`; row 285 (5,7): `-4.928 5.834 …`; row 330 (6,6): `2.953 2.523 … 4.938 … -4.740`; rows 405–440 (all of grid row 8) also large. So the agent can be essentially anywhere in rows 1–8 and the policy is strongly position‑dependent.
- **But a fixed set of interior cells has small weights on *every* channel** (ch0–ch4 all ≈ ±0.1): (2,2),(2,3),(3,2); (2,6),(2,7),(3,7); (6,2),(7,2),(7,3); (6,7),(7,6),(7,7); and the central 2×2 block (4,4),(4,5),(5,4),(5,5) (rows 110–119, 130–139, 160–164, 185–189, 220–229, 270–279, 310–314, 335–339, 360–369, 380–389). Neither the agent nor any moving object ever occupies them, i.e. they are permanent walls. The pattern is perfectly 4‑fold symmetric: an L‑shaped block in each corner and a 2×2 block in the centre — a small maze. The ch3 weights there are as small as the bias b1 (all |b1| < 0.13), which is what you expect from a constant‑on input: obstacles are static.
- **Channel 1 (moving objects)** has large weights at the same free cells as the agent, e.g. row 61 (1,2): `2.493 … -3.116 … 2.157 2.413`; row 121 (2,4) `3.745`; row 126 (2,5) `-5.209`; row 166 (3,3) `-3.873 … -4.266`; row 236 (4,7) `4.226 … -5.925`; row 241 (4,8) `-4.641 … 4.077`; row 331 (6,6) `-4.838`; row 376 (7,5) `5.421`. Hidden unit 9 acts as a "moving thing in the top/right corridor" detector: ch1 weight −3.386, −3.354, −2.016, −3.343, −3.074, −4.641 at (1,6),(1,7),(1,8),(2,8),(3,8),(4,8). The moving objects roam the whole maze, through corridors, and the network cares about exactly where they are.
- **Channel 4 (previous frame)** has moderate weights (0.5–3) at the same free cells, often with the opposite sign to ch1 in the same unit (e.g. unit 9: ch4 −2.070, −2.004, −2.849, −2.307 at (1,6),(1,7),(1,8),(2,8); unit 6: ≈ +0.7…+1.0 on nearly every free cell). It is used to infer the direction/velocity of the moving objects.
- **Channel 2 (reward targets)** is the odd one out: weights are near zero almost everywhere, except a consistent negative lobe on hidden unit 6 in the top‑left corridor: (1,1) −1.490, (1,2) −2.361, (1,3) −1.905, (1,4) −0.883, (2,1) −0.628, (2,4) −4.876, (2,5) −0.854, plus a moderate row at (6,4) (`1.596 -1.426 … 1.171`) and (3,3) 0.729. Reward targets are static (they are not the moving objects — if ch1 and ch2 were the same cells, their weight rows would have grown identically) and the policy only needs to check whether targets remain in a few locations; elsewhere it follows a position‑based route.
- **Output layer**: b3 = `-0.873 0.703 0.712 0.595 -0.092` — no‑op is strongly disfavoured, the agent is meant to keep moving every step; up/down/left/right all have large, mixed‑sign W3 columns (e.g. row 9 `… -3.070 1.267 …`, row 19 `… -2.927 …`, row 28 `… 2.500`, row 25 `… -2.491`), so all four directions are actively chosen depending on state.

**Reasoning**

- A static, symmetric interior maze (corner L‑blocks + centre block) rules out open‑field games (Snake, simple collect‑the‑dot, dodge‑the‑falling‑objects) and lane games like Frogger/Freeway, where obstacles would be in rows and moving objects would be confined to lanes — here moving objects appear in every free cell including corridors between the blocks.
- The moving objects are *not* the reward (ch1 ≠ ch2 statistically), yet the network tracks their positions and velocities precisely → they are enemies to be avoided (ghosts), not prey.
- Static reward targets whose channel is largely uninformative is exactly what you get with pellets filling the free cells: at the start almost every cell is a target, so a position‑dependent sweeping route collects them, and the network only needs ch2 in the region it revisits (top‑left corridor, unit 6).
- Agent + pellets + ghosts + fixed symmetric maze + "never stop moving" bias = a miniature Pac‑Man.

**Game:** A small Pac‑Man–style maze game ("mini Pac‑Man"): the agent moves through an 8×8 maze with four corner wall blocks and a central 2×2 block, collecting pellets while avoiding roaming ghosts.

**Description:** The agent steers through the maze eating pellets (channel 2) for reward, choosing a route from its own position and the positions/velocities of the ghosts (channels 1 and 4); touching a ghost (or a wall) ends the episode, so it keeps moving and dodges them.

**Confidence:** 70%

<details>
<summary>Run settings and assistant evaluation</summary>

```json
{
  "experiment": 1,
  "case": "pacman",
  "model": "claude-fable-5-1",
  "provider": "anthropic",
  "status": "complete",
  "elapsed_seconds": 175.85320344899992,
  "request_settings": {
    "model": "claude-fable-5-1",
    "max_tokens": 16384,
    "thinking": {
      "type": "adaptive"
    },
    "output_config": {
      "effort": "high"
    }
  },
  "usage": {
    "input_tokens": 79037,
    "cache_creation_input_tokens": 0,
    "cache_read_input_tokens": 0,
    "cache_creation": {
      "ephemeral_5m_input_tokens": 0,
      "ephemeral_1h_input_tokens": 0
    },
    "output_tokens": 15709,
    "output_tokens_details": {
      "thinking_tokens": 13458
    },
    "service_tier": "standard",
    "inference_geo": "global",
    "speed": "standard"
  },
  "evaluation_author": "OpenAI assistant (Codex); not user-authored",
  "evaluation": {
    "answer_section": "A small Pac‑Man–style maze game (\"mini Pac‑Man\"): the agent moves through an 8×8 maze with four corner wall blocks and a central 2×2 block, collecting pellets while avoiding roaming ghosts.",
    "candidates": [
      "pacman"
    ],
    "prediction": "pacman",
    "correct": true,
    "needs_review": false,
    "confidence": 70,
    "fill_description": null
  }
}
```

</details>
