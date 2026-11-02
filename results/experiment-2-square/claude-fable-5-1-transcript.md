# claude-fable-5-1 — experiment 2: square

Provider: anthropic. Status: complete.

## System instruction

Answer the user's request.

## User prompt

[Complete prompt, including weights](prompt.txt)

## Reasoning returned by the provider

(None returned.)

## Assistant response

**Observations**

*Border.* Inputs for row 0, row 11, column 0 and column 11 (W1 lines 0–11, 132–143, 12, 23, 24, 35, …) have only tiny weights (|w| ≲ 0.1), and the W3 columns for those pixels are likewise near zero for every unit. b3 is strongly negative there (corners −0.69/−0.71/−0.63/−0.69, edges −0.3…−0.5) and a group of often-active h2 units with large positive b2 (unit 7: b2 = 0.66, W3 row 7 is −0.1…−0.34 everywhere, especially the bottom row; units 33, 34, 45, 11) push them further down. The outer 1-pixel frame is never drawn on. The interior (rows 1–10, cols 1–10) has b3 ≈ −0.1…+0.1.

*First layer = axis-aligned stroke detectors.* Almost every strong W1 column is a 1-pixel-wide horizontal or vertical run:
- horizontal: unit 15 on row 1 (pixels 13–19: 0.296 0.398 0.394 0.306 0.305 0.280 0.184); unit 51 on row 2 (pixels 28–33: 0.261 0.360 0.383 0.385 0.376 0.320); unit 17 on row 2 (26–32, all ≈ −0.22…−0.34); unit 8 on row 4 (49–54: 0.14 0.32 0.38 0.39 0.36 0.24); unit 36 row 4 negative (51–57); unit 50 row 3 negative (38–44: −0.21…−0.40); unit 27 row 5 negative (62–69: −0.23…−0.42); unit 38 row 7 negative (87–92: −0.27…−0.39); unit 19 row 8 (100–104: 0.285 0.363 0.415 0.373 0.272) with unit 21 negative on the same pixels; unit 9 row 9 (112–117: 0.22 0.30 0.36 0.33 0.29 0.22); unit 42 row 9 negative; unit 57 row 10 (124–129: 0.22 0.27 0.27 0.27 0.24 0.16).
- vertical: unit 0 on cols 1–2, rows 2–6 (26: 0.428, 38: 0.412, 50: 0.369, 62: 0.336, 74: 0.323); unit 49 col 1 rows 3–9 (0.25 0.32 0.34 0.34 0.35 0.31 0.20); unit 54 col 2 rows 3–9 (0.215 0.302 0.377 0.412 0.377 0.317 0.233); unit 2 col 3 rows 3–9 (0.198 0.289 0.360 0.429 0.378 0.308 0.224); unit 6 col 4 negative (40–112: −0.21…−0.39); unit 35 col 5 negative; unit 34 col 6 negative; unit 20 col 7 rows 3–8 (0.217 0.346 0.361 0.363 0.250) with unit 26 negative there; unit 7 col 8 rows 4–9 (0.223 0.285 0.339 0.338 0.350 0.322) with unit 25 negative (−0.32…−0.42); unit 31 col 9 rows 1–8 (0.19 0.26 0.38 0.43 0.48 0.48 0.40 0.27); unit 14 col 10 rows 1–8 (0.157 0.287 0.380 0.373 0.367 0.352 0.312 0.207).
- *corner detectors*: unit 22 = row 10 cols 1–6 (0.367 0.423 0.351 0.310 0.270 0.222) **plus** col 1 rows 6–9 (0.155 0.182 0.191 0.274) → bottom-left corner; unit 43 = row 10 cols 6–10 (0.18 0.27 0.32 0.38 0.33) plus row 9 cols 7–10 and col 10 rows 7–8 → bottom-right; unit 40 = row 1 cols 7–10 (0.21 0.25 0.31 0.26) plus row 2 cols 8–10 and col 9–10 rows 3–4 → top-right; unit 24 / unit 15 = rows 1–3, cols 1–3 (0.145 0.189 0.184; 0.172 0.264 0.237; 0.162 0.255) → top-left; unit 63 = row 9 cols 4–8 plus cols 9–10 rows 8–9 (0.434, 0.322) → bottom-right.
- Time inputs dominate layer 1 (line 154: ±1.4; lines 145–148, 153, 155, 156: ±0.4…0.9), as expected.

*Output layer = painters/erasers of whole 1-pixel lines.*
- bright horizontal lines: unit 55 → row 1, pixels 14–22: 0.210 0.353 0.486 0.498 0.510 0.503 0.441 0.347 0.205; unit 29 → row 2 (25–33: 0.097 0.363 0.371 0.461 0.345 0.272 0.280 0.197 0.129); unit 47 → row 3 (37–46: 0.12 0.26 0.32 0.34 0.42 0.44 0.37 0.30 0.26 0.16); unit 46 → row 4 (51–57: 0.13 0.22 0.35 0.28 0.38 0.26 0.15); unit 62 → row 5 (62–70: 0.18 0.30 0.25 0.33 0.42 0.28 0.27 0.16 0.14); unit 44 → row 7 (85–94: 0.09 0.20 0.22 0.30 0.46 0.49 0.35 0.29 0.21 0.10); unit 36 → row 9 (109–115: 0.28 0.40 0.41 0.42 0.43 0.34 0.15); unit 20 → row 10 (121–129: 0.11 0.31 0.43 0.50 0.54 0.53 0.45 0.35 0.13).
- bright vertical lines: unit 42 → col 1 (13: 0.460, 25: 0.641, 37: 0.489, 49: 0.398, 61: 0.330, 73: 0.241, 85: 0.156); unit 14 → col 5 (29…125: 0.12 0.22 0.31 0.35 0.41 0.21 0.27 0.14 0.08) with cols 6–7 negative (−0.08…−0.19); unit 57 → col 8 (20…128: 0.12 0.22 0.36 0.37 0.36 0.42 0.40 0.28 0.19 0.10) with col 9 negative (−0.15…−0.24); unit 56 → col 10 (46…130: 0.20 0.27 0.37 0.43 0.46 0.45 0.44 0.31).
- dark (erasing) lines: unit 28 row 2 (−0.14…−0.35), unit 49 row 4 (−0.23 −0.46 −0.47 −0.45 −0.43 −0.36 −0.18), unit 39 row 6 (−0.16 −0.32 −0.46 −0.56 −0.55 −0.50 −0.34 −0.13), unit 2 row 9 (−0.19…−0.45), unit 40 row 10 (−0.36 −0.36 −0.41 −0.41 −0.32 −0.22); unit 15 col 1 (−0.27…−0.42), unit 19 col 2 (−0.12…−0.35), units 3/21/54 col 3 (down to −0.50), unit 5 cols 5–6, unit 48 col 7 (−0.22…−0.51), unit 18 cols 8–9, units 6/24 col 10 (−0.21…−0.49).
- corner painters: unit 0 puts 0.534 on pixel 64 (row 5, col 4) with 0.300/0.352/0.151 above/below it in col 4 and 0.247 0.215 0.138 to its right in row 5 — an L-shaped top-left corner; unit 53 erases an L (col 6 rows 5–7 ≈ −0.2 and row 8 cols 3–9: −0.20 −0.21 −0.36 −0.40 −0.21 −0.20).
- A few h2 rows (38, 41, 52, 59) are pure ±0.1 noise — dead units.

**Reasoning**

Everything the network detects and draws is a 1-pixel-thick, axis-aligned straight stroke, with explicit corner (L-shaped) detectors in layer 1 (units 22, 40, 43, 24/15, 63) and an L-shaped corner painter in W3 (unit 0). The painters for a given row/column have hump-shaped profiles (strong in the middle, tapering toward both ends), which is what you get when the stroke at that row has variable start/end positions — i.e. the edges of boxes of varying width. Bright line units are paired with dark flanks on the neighbouring row/column (unit 14: col 5 bright, cols 6–7 dark; unit 57: col 8 bright, col 9 dark; unit 56: col 10 bright, cols 1–4 dark), so the strokes are outlines with black on both sides, not the boundary of a filled region. The outermost frame is never touched (near-zero W1/W3 weights, strongly negative biases), so shapes live in the inner 10×10.

Ruled out: filled blobs/discs (no area painters dominate; only thin lines), diagonal or curved shapes (no diagonal weight structure anywhere), digits/letters (would need many mixed stroke combinations; here every horizontal and vertical position gets its own clean painter/eraser), centred crosses (the corner detectors sit at the image periphery — rows 1–3/cols 1–3, row 1/cols 7–10, row 10/cols 1–6, row 9–10/cols 7–10 — i.e. where box corners are, not where cross arms meet). Horizontal painters exist for rows 1, 2, 3, 4, 5, 7, 9, 10 and vertical ones for cols 1, 5, 8, 10, with erasers filling in the rest, which is exactly a model that picks a top/bottom row and left/right column and draws the frame between them. Detector run lengths (≈5–7 pixels) suggest typical side lengths of roughly 4–8, with extremes from ~3 up to the full 10.

**Images**

Each generated image is a single hollow rectangle (1-pixel-wide white outline on a black background), axis-aligned, with random position and random width/height. The rectangle always lies within rows 1–10 and columns 1–10, so a black 1-pixel margin surrounds it; sides are typically about 4–8 pixels long (range roughly 3–10), the interior is black, and the outer border of the image is always black.

**Example**

```
............
............
...#######..
...#.....#..
...#.....#..
...#.....#..
...#.....#..
...#.....#..
...#######..
............
............
............
```

**Confidence:** 65%

<details>
<summary>Run settings and assistant evaluation</summary>

```json
{
  "experiment": 2,
  "case": "square",
  "model": "claude-fable-5-1",
  "provider": "anthropic",
  "status": "complete",
  "elapsed_seconds": 337.52318187200035,
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
    "input_tokens": 108858,
    "cache_creation_input_tokens": 0,
    "cache_read_input_tokens": 0,
    "cache_creation": {
      "ephemeral_5m_input_tokens": 0,
      "ephemeral_1h_input_tokens": 0
    },
    "output_tokens": 30835,
    "output_tokens_details": {
      "thinking_tokens": 27109
    },
    "service_tier": "standard",
    "inference_geo": "global",
    "speed": "standard"
  },
  "evaluation_author": "OpenAI assistant (Codex); not user-authored",
  "evaluation": {
    "answer_section": "Each generated image is a single hollow rectangle (1-pixel-wide white outline on a black background), axis-aligned, with random position and random width/height. The rectangle always lies within rows 1–10 and columns 1–10, so a black 1-pixel margin surrounds it; sides are typically about 4–8 pixels long (range roughly 3–10), the interior is black, and the outer border of the image is always black.",
    "candidates": [
      "square"
    ],
    "prediction": "square",
    "correct": true,
    "needs_review": false,
    "confidence": 65,
    "fill_description": "outline"
  }
}
```

</details>
