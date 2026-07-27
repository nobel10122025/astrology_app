"""
Tools - the deterministic capabilities a main agent triggers.

Each tool is a small, named, individually-testable unit with a `run(...)` entry
point that wraps one core service. A main agent (e.g. ProfessionMainAgent) plans
which tools to run - based on the person's age/life stage - and wires their
outputs together. No tool calls an LLM; the LLM stays at the narration edge.

Tools:
    career_significators - who: planets connected to the career houses
    strength             - how good: checklist score 0-10
    timing               - when: PAST/ACTIVE/UPCOMING + age window
    dasha_favourability  - is the near-future dasha climate favourable
    career_arc           - the life-stage timeline of fields + shift detection
    field_resolver       - what field: significations -> specific fields
"""
