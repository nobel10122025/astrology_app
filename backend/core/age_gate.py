"""
Age gate + timing engine.

Two jobs:
1. Turn DOB + today into a current age and PAST/ACTIVE/UPCOMING tags over the
   Vimshottari dasha timeline (`tag_timeline`).
2. Given a set of "activator" planets for a life domain, find WHEN that domain
   is timed to fire and return an age window (`TimingResolver`).

This is the genuinely new layer the existing repo did not have: it converts raw
dasha periods into age-aware timing that agents can attach to a prediction.
"""

from datetime import date, datetime


def _parse(d):
    return datetime.strptime(d, "%Y-%m-%d").date()


def compute_age(dob, on=None):
    """Whole-years age of `dob` as of `on` (default today)."""
    on = on or date.today()
    return on.year - dob.year - ((on.month, on.day) < (dob.month, dob.day))


def _age_on(dob, d):
    """Fractional age (rounded to whole years) reached on date `d`."""
    return round((d - dob).days / 365.25)


def tag_timeline(dashas, today=None):
    """Tag each Mahadasa period PAST / ACTIVE / UPCOMING relative to today."""
    today = today or date.today()
    tagged = []
    for maha in dashas or []:
        start, end = _parse(maha["start_date"]), _parse(maha["end_date"])
        if start <= today < end:
            tag = "ACTIVE"
        elif start > today:
            tag = "UPCOMING"
        else:
            tag = "PAST"
        tagged.append(
            {
                "lord": maha["lord"],
                "start_date": maha["start_date"],
                "end_date": maha["end_date"],
                "tag": tag,
            }
        )
    return tagged


class TimingResolver:
    """Resolve a domain's timing from the dasha timeline.

    A domain "fires" during the dasha/antardasha of any of its activator lords
    (e.g. career activates in the periods of the 10th lord, 2nd lord, or a
    career karaka). We scan antardasha-level windows for the finest actionable
    range, then pick the representative window: the one active now, else the
    next upcoming one, else the most recent past one.
    """

    @staticmethod
    def resolve(activators, dashas, dob, today=None):
        blank = {"timing": "GENERAL", "age_range": None, "dasa_context": None}
        if not activators or not dashas or dob is None:
            return blank

        today = today or date.today()
        candidates = []  # (start, end, maha_lord, antar_lord)
        for maha in dashas:
            ml = maha["lord"]
            for antar in maha.get("antardashas", []):
                al = antar["lord"]
                if ml in activators or al in activators:
                    candidates.append(
                        (_parse(antar["start_date"]), _parse(antar["end_date"]), ml, al)
                    )
        if not candidates:
            return blank

        active = [c for c in candidates if c[0] <= today < c[1]]
        upcoming = sorted([c for c in candidates if c[0] > today])
        past = sorted([c for c in candidates if c[1] <= today])

        if active:
            chosen, timing = active[0], "ACTIVE"
        elif upcoming:
            chosen, timing = upcoming[0], "UPCOMING"
        else:
            chosen, timing = past[-1], "PAST"

        start, end, ml, al = chosen
        return {
            "timing": timing,
            "age_range": f"age {_age_on(dob, start)}–{_age_on(dob, end)}",
            "dasa_context": f"{ml.title()} Mahadasa / {al.title()} Antardasa",
        }
