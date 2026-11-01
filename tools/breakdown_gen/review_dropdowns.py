"""Print the lists to review by hand for dropdowns (`type` / `options`) after generating a breakdown
(checklist section 4).

Independent of the generator: uses validate_breakdown.py's own template reader.

Usage:
    python review_dropdowns.py TEMPLATE BREAKDOWN [CONFIG]
TEMPLATE may be a file or "archive.zip::path/inside/archive". With CONFIG (the generator config), fields already
decided in its `overrides` are marked "decided in overrides", so only new items need a look.

STEP 1  inventory                          STEP 4  list fields shown as single-choice (4.4)
STEP 2  vocabulary but no dropdown (4.1, 4.2)   STEP 5  options not found in the template (4.5)
STEP 3  single-value lists (4.3)           STEP 6  the extra None option (4.6)
"""
import re
import sys
from collections import Counter

import yaml

from validate_breakdown import breakdown_fields, read_text, template_comments, template_leaves

sys.stdout.reconfigure(encoding="utf-8")
NONE_LIKE = {"none", "not_applicable", "n/a", "na", "no", "other", "unknown"}
VOCAB_HINT = re.compile(r"vocabular|allowed values|select one|select from|select all|list all that apply|"
                        r"one of:|enum", re.I)
LIST_HINT = re.compile(r"all that apply|list all|each as a separate entry", re.I)


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
    decided = set(cfg.get("overrides") or {})
    no_extra = set(cfg.get("no_extra_option") or [])
    leaves = {p: f for p, f in bd.items() if p in tmpl and not isinstance(tmpl[p], dict) and "." in p
              and not (isinstance(tmpl[p], list) and tmpl[p] and isinstance(tmpl[p][0], dict))}  # skip list-of-block containers
    norm = lambda s: re.sub(r"[\s_\-]+", " ", str(s).lower())

    def show(p, extra=""):
        f = bd[p]
        kind = f.get("type") or "text"
        print(f"   line {line_of.get(p, '?'):>5}  {kind:8} req={str(bool(f['required'])):5}  {p}{extra}"
              + ("   <- decided in overrides" if p in decided else ""))

    def snippet(p, rx):
        c = comments.get(p) or ""
        m = rx.search(c)
        return " ".join(c[max(0, m.start() - 10):m.start() + 90].split()) if m else ""

    print("STEP 1. Inventory: field types in the breakdown")
    kinds = Counter(f.get("type") or "text" for f in leaves.values())
    with_none = sum(1 for f in leaves.values() if "None" in (f.get("options") or []))
    print(f"   {len(leaves)} leaf fields: " + ", ".join(f"{k} {n}" for k, n in kinds.most_common())
          + f"; {with_none} dropdowns carry a `None` option")

    print("\nSTEP 2. The comment mentions a vocabulary, but the field is free text (checklist 4.1, 4.2)")
    for p, f in leaves.items():
        c = comments.get(p) or ""
        if "type" not in f and VOCAB_HINT.search(c):
            why = "4.1 list after e.g." if re.search(r"e\.g\.|for example", c, re.I) else (
                "4.3 single value" if re.search(r"allowed values:\s*\w+\s*$", c.strip(), re.I) else "4.2 named only / not listed")
            show(p, f'   [{why}]  "{snippet(p, VOCAB_HINT)}"')

    print("\nSTEP 3. A choice list with a single value: no dropdown is made (checklist 4.3)")
    for p, f in leaves.items():
        m = re.search(r"allowed values:\s*([^|.]+?)\s*(?:\.|$)", comments.get(p) or "", re.I)
        if "type" not in f and m and "|" not in m.group(1) and len(m.group(1).split()) <= 3:
            show(p, f'   "Allowed values: {m.group(1).strip()}"')

    print("\nSTEP 4. List fields shown as a single-choice dropdown: MAVEN has no multi-select (checklist 4.4)")
    multi = [p for p, f in leaves.items() if f.get("type") == "dropdown"
             and (isinstance(tmpl[p], list) or LIST_HINT.search(comments.get(p) or ""))]
    for key, n in Counter(p.rsplit(".", 1)[-1] for p in multi).most_common():
        print(f"   {key:32} x{n}")
    print(f"   total {len(multi)}   <- known limitation (Q4); no action unless MAVEN gets multi-select")

    print("\nSTEP 5. Dropdown options that do not appear in the template comment: typo, copy mistake or false dropdown (checklist 4.5)")
    for p, f in leaves.items():
        if f.get("type") not in ("dropdown", "radio"):
            continue
        text_ = norm((comments.get(p) or "") + " " + str(tmpl[p]))
        names = [str(o).split(":")[0].strip() for o in f.get("options") or []]
        missing = [o for o in names if o.lower() not in NONE_LIKE and norm(o) not in text_]
        if missing and p.rsplit(".", 1)[-1] != "agent_type":  # agent_type may be synthesized (block names)
            show(p, f"   not in comment: {missing[:6]}")
            continue
        c = comments.get(p) or ""
        first = next((c.find(o) for o in names if o.lower() not in NONE_LIKE and o in c), -1)
        # options taken from examples: an 'e.g.' before them with no label colon ('values: ') in between
        if first > 0 and re.search(r"(e\.g\.|example)(?:(?!:\s|;).)*$", c[:first], re.I | re.S):
            show(p, f"   <- CHECK: options come after 'e.g.' (examples?): {names[:6]}")

    print("\nSTEP 6. The extra `None` option (checklist 4.6): rule = required dropdowns without a 'nothing applies' choice")
    for p, f in leaves.items():
        opts = [str(o).lower() for o in f.get("options") or []]
        if f.get("type") != "dropdown":
            continue
        has_none = "none" in opts
        in_template = "none" in ((comments.get(p) or "").lower())
        if has_none and not in_template and not f["required"]:
            show(p, "   <- CHECK: `None` added to an OPTIONAL dropdown (rule adds it to required ones only)")
        elif not has_none and f["required"] and not (set(opts) & NONE_LIKE):
            if p in no_extra:
                show(p, "   no `None`: listed in config `no_extra_option`")
            elif any(q.rpartition(".")[0] == p.rpartition(".")[0] and g.get("condition_discriminator") == p.rsplit(".", 1)[-1]
                     for q, g in bd.items()):
                show(p, "   no `None`: one-of discriminator (a block must be chosen)")
            else:
                show(p, "   <- CHECK: required dropdown with no 'nothing applies' choice and no `None`")
        elif has_none and not in_template:
            show(p, "   `None` added (required dropdown)")


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    main(*sys.argv[1:])
