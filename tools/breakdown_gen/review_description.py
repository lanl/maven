"""Print the lists to review by hand for `description` after generating a breakdown (checklist section 5).

Independent of the generator: uses validate_breakdown.py's own template reader.

Usage:
    python review_description.py TEMPLATE BREAKDOWN [CONFIG]
TEMPLATE may be a file or "archive.zip::path/inside/archive". With CONFIG (the generator config), fields whose
description is set in its `overrides` are marked "decided in overrides", so only new items need a look.

STEP 1  inventory                                   STEP 4  conditionally required, condition not stated (5.3)
STEP 2  empty, very short or shared generic text (5.1)   STEP 5  headings or text from other keys (5.4, 5.5)
STEP 3  one-of blocks (5.2)                          STEP 6  sections and top blocks: guide text? (5.6)
"""
import re
import sys
from collections import defaultdict

import yaml

from validate_breakdown import breakdown_fields, read_text, tags_of, template_comments, template_leaves

sys.stdout.reconfigure(encoding="utf-8")
SHORT = 25        # characters; below this a description rarely tells the user anything
SHARED = 3        # the same text on this many different keys is a generic schema sentence
CONDITION = re.compile(r"\b(required|if|when|only for)\b", re.I)
BLEED = re.compile(r"(-{3,}|#{2,}|\s#\s|(?:^|\s)-\s+\w+:|__[A-Z_|]+__)")  # headings, comment marks, YAML examples


def template_lines(text):
    """{path: template line number}."""
    out, stack = {}, []
    for no, raw in enumerate(text.splitlines(), 1):
        m = re.match(r"^(\s*)(-\s+)?([A-Za-z_]\w*):", raw)
        if m and not raw.strip().startswith("#"):
            ind = len(m.group(1)) + len(m.group(2) or "")
            while stack and stack[-1][0] >= ind:
                stack.pop()
            stack.append((ind, m.group(3)))
            out.setdefault(".".join(k for _, k in stack), no)
    return out


def main(template_spec, breakdown_path, config_path=None):
    text = read_text(template_spec)
    tmpl, comments, line_of = template_leaves(yaml.safe_load(text)), template_comments(text), template_lines(text)
    bd = breakdown_fields(yaml.safe_load(open(breakdown_path, encoding="utf-8")))
    cfg = (yaml.safe_load(open(config_path, encoding="utf-8")) or {}) if config_path else {}
    decided = {p for p, patch in (cfg.get("overrides") or {}).items() if "description" in (patch or {})}
    rows = {p: f for p, f in bd.items() if p in tmpl}
    desc = {p: " ".join(str(f.get("description") or "").split()) for p, f in rows.items()}

    def show(p, extra=""):
        print(f"   line {line_of.get(p, '?'):>5}  req={str(bool(rows[p].get('required'))):5}  {p}{extra}"
              + ("   <- decided in overrides" if p in decided else ""))

    print("STEP 1. Inventory")
    lengths = sorted(len(d) for d in desc.values())
    print(f"   {len(desc)} fields; description length median {lengths[len(lengths) // 2]}, "
          f"longest {lengths[-1]} characters; {sum(1 for d in desc.values() if not d)} empty")

    print(f"\nSTEP 2. Empty, very short (< {SHORT} characters) or shared generic text (checklist 5.1)")
    for p, d in desc.items():
        if len(d) < SHORT and not rows[p].get("conditional_context"):  # one-of blocks are in STEP 3
            show(p, f'   "{d}"')
    by_text = defaultdict(set)
    for p, d in desc.items():
        if d:
            by_text[d].add(p.rsplit(".", 1)[-1])
    for d, keys in sorted(by_text.items(), key=lambda kv: -len(kv[1])):
        if len(keys) >= SHARED:  # one sentence reused for unrelated keys says nothing specific about each one
            paths = [p for p, x in desc.items() if x == d]
            print(f'   x{len(paths):<3} "{d[:90]}"  keys: {sorted(keys)[:8]}')

    print("\nSTEP 3. One-of blocks: does the description say how the choice works? (checklist 5.2)")
    groups = defaultdict(list)
    for p, f in rows.items():
        if f.get("conditional_context"):
            groups[p.rpartition(".")[0]].append(p)
    for parent, blocks in groups.items():
        silent = [b.rsplit(".", 1)[-1] for b in blocks
                  if not re.search(r"agent_type|delete|choose|select|one of|fill in only", desc[b], re.I)]
        note = f"   <- no 'choose one' hint in {silent}" if silent else ""
        print(f"   line {line_of.get(parent, '?'):>5}  {parent}: "
              + "; ".join(f'{b.rsplit(".", 1)[-1]} "{desc[b][:28]}"' for b in blocks) + note)

    print("\nSTEP 4. Conditionally required but not required: is the condition in the description? (checklist 5.3)")
    for p, f in rows.items():
        tags = tags_of(comments.get(p))
        cond = [t for t in tags if t == "situational_required" or (" " in t and re.search(r"\brequired\b", t))]
        if cond and not f.get("required") and not CONDITION.search(desc[p]):
            show(p, f"   [{cond[0][:40]}]  <- CHECK: description never says when it is required")

    print("\nSTEP 5. Headings, comment marks or YAML examples inside the description (checklist 5.4, 5.5)")
    for p, d in desc.items():
        m = BLEED.search(d)
        if m:
            show(p, f'   "...{d[max(0, m.start() - 30):m.start() + 40]}..."')

    print("\nSTEP 6. Sections and top-level blocks: add the reference guide's text? (checklist 5.6, optional)")
    for p, d in desc.items():
        if p.count(".") <= 1 and isinstance(tmpl.get(p), dict):
            show(p, f'   "{d[:80]}"')


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    main(*sys.argv[1:])
