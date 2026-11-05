"""Print the lists to review by hand for `required` after generating a breakdown (checklist section 3).

Independent of the generator: uses validate_breakdown.py's own template reader.

Usage:
    python review_required.py TEMPLATE BREAKDOWN [CONFIG]
TEMPLATE may be a file or "archive.zip::path/inside/archive". With CONFIG (the generator config), fields already
decided in its `overrides` are marked "decided in overrides", so only new items need a look.
"""
import re
import sys
from collections import Counter, defaultdict

import yaml

from validate_breakdown import breakdown_fields, read_text, tags_of, template_comments, template_leaves

sys.stdout.reconfigure(encoding="utf-8")
DEFAULT_BLOCKS = ["person", "organization", "ai_model", "software"]  # used when no config is given
DEFAULT_KEYS = ["given_name", "family_name", "name", "version", "affiliation", "type", "value"]
KNOWN = re.compile(r"^(required|\w+_required|\w+_if_applicable|if_applicable|recommended|situational_required)$")


def kind(tag):
    if tag in ("required", "situational_required") or (tag.endswith("_required") and " " not in tag):
        return "1 required" if tag != "situational_required" else "3 conditional"
    if tag.endswith("if_applicable") or tag == "recommended":
        return "2 optional"
    if re.search(r"\brequired\b", tag):
        return "3 conditional"
    return "5 unknown"


def main(template_spec, breakdown_path, config_path=None):
    text = read_text(template_spec)
    tmpl, comments = template_leaves(yaml.safe_load(text)), template_comments(text)
    bd = breakdown_fields(yaml.safe_load(open(breakdown_path, encoding="utf-8")))
    line_of = {}
    stack = []
    for no, raw in enumerate(text.splitlines(), 1):  # template line number of each key
        m = re.match(r"^(\s*)(-\s+)?([A-Za-z_]\w*):", raw)
        if m and not raw.strip().startswith("#"):
            ind = len(m.group(1)) + len(m.group(2) or "")
            while stack and stack[-1][0] >= ind:
                stack.pop()
            stack.append((ind, m.group(3)))
            line_of.setdefault(".".join(k for _, k in stack), no)

    rows = [(p, f, tags_of(comments.get(p))) for p, f in bd.items() if p in tmpl]
    decided = set((yaml.safe_load(open(config_path, encoding="utf-8")) or {}).get("overrides") or {}) if config_path else set()
    show = lambda p, f, extra="": print(f"   line {line_of.get(p, '?'):>5}  required={str(bool(f.get('required'))):5}  {p}{extra}"
                                        + ("   <- decided in overrides" if p in decided else ""))

    print("STEP 1. Tag inventory: every tag in the template and how the breakdown set `required`")
    table = defaultdict(Counter)
    for p, f, tags in rows:
        for t in tags or ["(no tag)"]:
            table[(kind(t) if tags else "4 no tag", t)][bool(f.get("required"))] += 1
    for (k, t), n in sorted(table.items()):
        print(f"   [{k:13}] {t[:55]:57} true={n[True]:3}  false={n[False]:3}")

    groups = {k: [] for k in ("1 required", "2 optional", "3 conditional", "4 no tag", "5 unknown")}
    for p, f, tags in rows:
        kinds = {kind(t) for t in tags} or {"4 no tag"}
        for k in kinds:
            groups[k].append((p, f, tags))

    print("\nSTEP 2. Required tag but required: false (expected only inside an optional parent block)")
    for p, f, tags in groups["1 required"]:
        if not f.get("required"):
            parent = next((q for q in (p.rsplit(".", i)[0] for i in range(1, p.count(".") + 1))
                           if q in bd and not bd[q].get("required")), None)
            show(p, f, f"   <- parent `{parent}` is optional" if parent else "   <- CHECK: no optional parent")

    print("\nSTEP 3. Optional tag but required: true (expected only inside one-of blocks, i.e. 'required if chosen')")
    for p, f, tags in groups["2 optional"]:
        if f.get("required") and "1 required" not in {kind(t) for t in tags}:
            inside = any(bd.get(q, {}).get("conditional_context") for q in (p.rsplit(".", i)[0] for i in range(1, p.count(".") + 1)))
            show(p, f, "   <- inside a one-of block" if inside else "   <- CHECK: not in a one-of block")

    print("\nSTEP 4. Conditional tags: should be required: false, and the condition should still be in the description")
    for p, f, tags in groups["3 conditional"]:
        cond = next(t for t in tags if kind(t) == "3 conditional")
        squash = lambda s: re.sub(r"[\s\"']+", "", s.lower())
        blocks = p.split(".")[:-1]
        enforced = f.get("required") and any(cond == f"required for {b}" for b in blocks)  # MAVEN enforces it when the block is chosen
        kept = enforced or cond == "situational_required" or squash(cond) in squash(str(f.get("description", "")))
        show(p, f, f"   [{cond[:50]}]" + ("" if kept else "   <- condition NOT in description"))

    print("\nSTEP 5. No tag, optional placeholder __…__, next to a ${…} sibling: possible wrong placeholder")
    for p, f, tags in groups["4 no tag"]:
        v = str(tmpl.get(p))
        parent = p.rpartition(".")[0]
        siblings = [q for q in tmpl if q.rpartition(".")[0] == parent and q != p]
        if v.startswith("__") and any(str(tmpl[q]).startswith("${") for q in siblings) and not f.get("required"):
            show(p, f, f"   value {v}")

    print("\nSTEP 6. Unknown tags: read their definition in the template's FIELD ANNOTATIONS")
    for t in sorted({t for _, _, tags in groups["5 unknown"] for t in tags if kind(t) == "5 unknown"}):
        print(f"   [{t}]")

    cfg = (yaml.safe_load(open(config_path, encoding="utf-8")) or {}) if config_path else {}
    alt = cfg.get("alternatives") or {}
    known = set(alt.get("blocks") or DEFAULT_BLOCKS)
    identifying = set(alt.get("required_keys") or DEFAULT_KEYS) | {"title", "label"}
    children = defaultdict(list)
    for p in tmpl:
        children[p.rpartition(".")[0]].append(p.rpartition(".")[2])

    print(f"\nSTEP 7. One-of block names (checklist 3.4): known blocks {sorted(known)}")
    for parent, kids in children.items():
        groups_here = [k for k in kids if k in known and isinstance(tmpl.get(f"{parent}.{k}"), dict)]
        if not groups_here:
            continue
        disc = next((k for k in kids if k in ("agent_type", "type")), None)
        listed = re.findall(r"[a-z_]+", (comments.get(f"{parent}.{disc}") or "").split("#")[0]) if disc else []
        new = [n for n in listed if n not in known and n in kids]           # a discriminator choice that is a block
        others = [k for k in kids if k not in known and isinstance(tmpl.get(f"{parent}.{k}"), dict)]
        note = f"   <- CHECK: new block name(s) {new}" if new else (
            "   <- only one block: a normal block, not a one-of choice" if len(groups_here) < 2 else (
                f"   <- look: other sub-block(s) {others} next to them; are they alternatives too?" if others else ""))
        print(f"   line {line_of.get(parent, '?'):>5}  {parent}: blocks {groups_here}"
              f"{f', chosen by `{disc}`' if disc else ', no discriminator (one is added)' if len(groups_here) > 1 else ''}{note}")

    print("\nSTEP 8. Fields inside one-of blocks that are NOT required (checklist 3.5): should none be required when chosen?")
    inside = defaultdict(list)
    for p, f in bd.items():
        parents = [p.rsplit(".", i)[0] for i in range(1, p.count(".") + 1)]
        if any(bd.get(q, {}).get("conditional_context") for q in parents) and not f.get("required") \
                and not isinstance(f.get("value"), dict):
            inside[p.rsplit(".", 1)[-1]].append(p)
    for key, paths in sorted(inside.items()):
        flag = "   <- CHECK: identifying field, usually required when the block is chosen" if key in identifying else ""
        print(f"   {key:20} x{len(paths):<3}{flag}")
        if flag:
            for p in paths:
                # an optional group between the field and its one-of block explains the `false`
                between = []
                for q in (p.rsplit(".", i)[0] for i in range(1, p.count(".") + 1)):
                    if bd.get(q, {}).get("conditional_context"):
                        break
                    between.append(q)
                opt = next((q for q in between if q in bd and not bd[q].get("required")), None)
                show(p, bd[p], f"   <- inside optional `{opt.rsplit('.', 1)[-1]}` "
                               f"[{', '.join(tags_of(comments.get(opt))) or 'no tag'}]" if opt else "")


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    main(*sys.argv[1:])
