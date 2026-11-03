"""Conservative scoring of requested answer sections."""

import re

ALIASES = {
    "game": {
        "breakout": r"\bbreakout\b",
        "pong": r"\bpong\b",
        "pacman": r"\bpac[ -]?man\b",
        "freeway": r"\b(?:freeway|frogger)\b",
    },
    "shape": {
        "circle": r"\b(?:circles?|circular|discs?|disks?|round|ovals?)\b",
        "square": r"\b(?:squares?|rectangles?|rectangular|box|boxes)\b",
        "triangle": r"\b(?:triangles?|triangular|pyramids?|wedges?)\b",
    },
}


def section(text, name):
    # Handles both `**Images:** text` and a heading on its own line.
    plain = text.replace("**", "").replace("__", "")
    match = re.search(rf"(?im)^\s*(?:#+\s*)?{name}(?::[ \t]*|[ \t]*$)\s*", plain)
    if not match:
        return ""
    rest = plain[match.end() :]
    return re.split(
        r"(?im)^\s*(?:#+\s*)?(?:Observations|Reasoning|Game|Description|Images|Example|Confidence)(?::|[ \t]*$)",
        rest,
    )[0].strip()


def score(text, kind, truth):
    answer = section(text, "Game" if kind == "game" else "Images")
    normalized = answer.translate(
        str.maketrans({c: "-" for c in "\u2010\u2011\u2012\u2013\u2014\u2212"})
    )
    matches = [
        label
        for label, pattern in ALIASES[kind].items()
        if re.search(pattern, normalized, re.I)
    ]
    # Ambiguous/negated categories need human review, never silently choose the truth.
    negated = any(
        re.search(
            r"\b(?:not|rather than|instead of|either|unlikely)(?:\s+\w+){0,3}\s*$",
            normalized[: m.start()],
            re.I,
        )
        for pattern in ALIASES[kind].values()
        for m in re.finditer(pattern, normalized, re.I)
    )
    review = len(matches) != 1 or negated
    confidence = section(text, "Confidence")
    number = re.search(r"\b(\d{1,3})(?:\s*%)?", confidence)
    fill = None
    if kind == "shape":
        outline = bool(
            re.search(r"\b(?:outline\w*|hollow|rings?|black interior)\b", answer, re.I)
        )
        filled = bool(re.search(r"\b(?:filled|solid)\b", answer, re.I))
        fill = (
            "ambiguous"
            if outline and filled
            else "outline"
            if outline
            else "filled"
            if filled
            else "unspecified"
        )
    return {
        "answer_section": answer,
        "candidates": matches,
        "prediction": matches[0] if not review else None,
        "correct": matches[0] == truth if not review else None,
        "needs_review": review,
        "confidence": int(number[1]) if number and int(number[1]) <= 100 else None,
        "fill_description": fill,
    }
