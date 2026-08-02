"""
Planet judge - the main LLM that decides, instead of arithmetic averaging.

WHAT IT DOES
    core.strength_tracks produces three deliberately UNRESOLVED tracks (bala /
    sambandha / adhikara) plus the conflicts between them. This module hands
    that evidence packet to an LLM and asks for the verdict directly - which
    track dominates, what the planet actually delivers in its dasha, and why.

    The LLM does the arbitration a numeric formula cannot: a 9th lord with full
    dig bala but a tight Mars conjunction from the 8th is not "average", and no
    weighted sum will ever say anything else.

WHAT IT IS NOT ALLOWED TO DO
    It may not introduce a placement, aspect or lordship that is not in the
    packet, and every claim must cite the fact ids it rests on. The astrology
    stays in Python; the LLM only weighs facts that Python already established.
    `_validate` drops any citation that is not a real fact id, so an invented
    reference cannot survive into the response.

CONSISTENCY (the user's requirement: two runs may differ in wording, but the
    content logic must match)
    Three mechanisms:
      1. temperature 0.1 - near-deterministic sampling.
      2. an in-process cache keyed by a hash of the packet, so the same chart
         asked twice returns the identical judgement rather than a fresh roll.
      3. mandatory fact citation - the substance is pinned to the deterministic
         layer, so only phrasing and emphasis can move between runs.
"""

import hashlib
import json
import os

from openai import OpenAI

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_MODEL = "llama-3.3-70b-versatile"

VALID_VERDICTS = ["strongly favourable", "favourable", "mixed",
                  "unfavourable", "strongly unfavourable"]
VALID_TRACKS = ["bala", "sambandha", "adhikara"]

_SYSTEM = """You are the judging engine of a Vedic astrology system. All chart
calculation has already been done for you. You never compute placements and you
never introduce a fact that is not in the packet.

You are given ONE planet, assessed on three separate tracks that have
deliberately NOT been combined into a single score:

  bala      - intrinsic capacity: exaltation, own sign, sthana bala, dig bala,
              combustion. Answers "can it act at all?"
  sambandha - the quality of its contacts: which planets aspect or conjoin it.
              Answers "what quality of result does it give?"
  adhikara  - the houses it owns. Answers "what areas does it govern?"

These tracks routinely contradict each other, and the contradiction is the
reading. Your job is to decide which one dominates for this planet, in this
chart. Do not average them.

The rules you must apply when weighing sambandha:
- An ASPECT is stronger than a conjunction.
- Redemption ranks, strongest first: a full Moon (last 3 days before purnima),
  then Jupiter, then Venus, then a Moon between panchami and dashami.
- A dark Moon has NO aspect power at all - it has no light. It can still
  afflict a planet it is conjunct with.
- An afflicting malefic does more damage from a dusthana (especially the 8th)
  than from an upachaya house (3, 6, 11). Mars in the 8th is far worse than
  Mars in the 3rd.
- When benefics redeem a planet that owns a bad house (6, 8, 12), that planet
  gives ONLY the good significations of the houses it owns - it does not stop
  owning them. Conversely an afflicted lord of a good house (5, 9) delivers
  that house's bad significations.

Every claim you make must cite the fact ids it rests on (e.g. "F3", "F7").
Never cite an id that is not in the packet.

Return ONLY JSON with exactly this shape:
{
  "verdict": "strongly favourable | favourable | mixed | unfavourable | strongly unfavourable",
  "dominant_track": "bala | sambandha | adhikara",
  "cited": ["F1", "F4"],
  "delivers": ["the specific significations this planet will actually give"],
  "withholds": ["what it will not give, or gives in damaged form"],
  "reasoning": "3-5 sentences naming the conflict and saying which side wins and why",
  "confidence": 0.0-1.0
}"""

_client = None
_cache = {}


def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not set")
        _client = OpenAI(base_url=GROQ_BASE_URL, api_key=api_key)
    return _client


def packet_hash(packet):
    """Stable hash of the evidence, used as the cache key. Sorting keys makes
    it insensitive to dict ordering."""
    blob = json.dumps(packet, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def _fact_ids(packet):
    ids = set()
    for track in packet.get("tracks", {}).values():
        for f in track.get("facts", []):
            ids.add(f["id"])
    return ids


def _validate(data, packet):
    """Coerce the model output into the contract, dropping anything invented."""
    verdict = (data.get("verdict") or "").strip().lower()
    if verdict not in VALID_VERDICTS:
        raise ValueError(f"invalid verdict: {verdict!r}")

    track = (data.get("dominant_track") or "").strip().lower()
    if track not in VALID_TRACKS:
        raise ValueError(f"invalid dominant_track: {track!r}")

    known = _fact_ids(packet)
    cited = [c for c in (data.get("cited") or []) if c in known]
    dropped = [c for c in (data.get("cited") or []) if c not in known]

    conf = data.get("confidence")
    try:
        conf = round(min(1.0, max(0.0, float(conf))), 2)
    except (TypeError, ValueError):
        conf = 0.5

    out = {
        "verdict": verdict,
        "dominant_track": track,
        "cited": cited,
        "delivers": [str(s) for s in (data.get("delivers") or [])],
        "withholds": [str(s) for s in (data.get("withholds") or [])],
        "reasoning": (data.get("reasoning") or "").strip(),
        "confidence": conf,
    }
    if dropped:
        out["dropped_citations"] = dropped
    return out


def judge(packet, model=None, use_cache=True):
    """Judge one evidence packet. Returns the validated verdict dict.

    Raises on LLM/parse failure so the caller can fall back to
    `deterministic_verdict`.
    """
    key = packet_hash(packet)
    if use_cache and key in _cache:
        return dict(_cache[key], cached=True)

    client = _get_client()
    resp = client.chat.completions.create(
        model=model or os.environ.get("GROQ_MODEL", DEFAULT_MODEL),
        temperature=0.1,
        max_tokens=900,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": json.dumps(packet, ensure_ascii=False)},
        ],
    )
    result = _validate(json.loads(resp.choices[0].message.content), packet)
    result["packet_hash"] = key
    result["source"] = "llm"
    if use_cache:
        _cache[key] = result
    return dict(result, cached=False)


def deterministic_verdict(packet):
    """Fallback when the LLM is unavailable.

    Deliberately crude - it applies the one rule that is unambiguous (sambandha
    decides what a planet delivers) and says so, rather than pretending to the
    nuance the LLM provides.
    """
    tracks = packet["tracks"]
    bala = tracks["bala"]["score"]
    samb = tracks["sambandha"]["score"]
    adhi = tracks["adhikara"]["score"]
    blended = 0.3 * bala + 0.5 * samb + 0.2 * adhi

    if blended >= 7.0:
        verdict = "strongly favourable"
    elif blended >= 5.75:
        verdict = "favourable"
    elif blended >= 4.25:
        verdict = "mixed"
    elif blended >= 3.0:
        verdict = "unfavourable"
    else:
        verdict = "strongly unfavourable"

    dominant = max(
        (("bala", abs(bala - 5)), ("sambandha", abs(samb - 5)),
         ("adhikara", abs(adhi - 5))),
        key=lambda kv: kv[1],
    )[0]

    return {
        "verdict": verdict,
        "dominant_track": dominant,
        "cited": sorted(_fact_ids(packet)),
        "delivers": packet["delivers"]["significations"],
        "withholds": [],
        "reasoning": (
            f"Deterministic fallback (no LLM): bala {bala}, sambandha {samb}, "
            f"adhikara {adhi}; sambandha decides the delivery side "
            f"({packet['delivers']['side']})."
        ),
        "confidence": 0.4,
        "packet_hash": packet_hash(packet),
        "source": "fallback",
    }


def judge_or_fallback(packet, model=None):
    """Judge with the LLM, falling back deterministically on any failure."""
    try:
        return judge(packet, model=model)
    except Exception as e:  # noqa: BLE001 - any failure must not break the API
        out = deterministic_verdict(packet)
        out["llm_error"] = str(e)
        return out
