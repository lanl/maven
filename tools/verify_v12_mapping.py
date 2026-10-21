"""Verify how genesis_dc_v1.2_breakdown.yaml was derived from its inputs.

Step 0  Compare Vedant's template (genesis_dc_v1.2_YAML.yaml) with the original template in the
        data-cards tarball, and classify every difference.
Step 1  Parse the annotated template: field path -> value, comment, [tag].
Step 2  Parse the breakdown: field path -> node (required / description / value / type / options).
Step 3  Walk the LinkML schema from the root class: field path -> required, multivalued, range, enum.
Step 4  Compare every breakdown node with the three sources and print match counts.
Step 5  Print the details behind the mismatches (required, dropdown options, enums with no dropdown).

Read-only: the tarball is read in memory and nothing in it is executed.

Usage:
    python verify_v12_mapping.py --template genesis_dc_v1.2_YAML.yaml \
        --breakdown genesis_dc_v1.2_breakdown.yaml --tar data-cards-v1.2.0.tar.gz [--json out.json]
"""
import argparse
import difflib
import json
import re
import sys
import tarfile
from collections import Counter
from pathlib import Path

import yaml

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
TEMPLATES = HERE.parent / "maven" / "metadata_template"
ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--template", default=str(TEMPLATES / "genesis_dc_v1.2_YAML.yaml"))
ap.add_argument("--breakdown", default=str(TEMPLATES / "genesis_dc_breakdown.yaml"))
ap.add_argument("--tar", default=str(HERE / "breakdown_gen" / "inputs" / "data-cards-v1.2.0.tar.gz"))
ap.add_argument("--json", help="optional: write per-field results here")
args = ap.parse_args()

tar = tarfile.open(args.tar)
read_tar = lambda name: tar.extractfile("data-cards-v1.2.0/" + name).read().decode("utf-8")
schema = yaml.safe_load(read_tar("datacard_schema/src/genesis_datacard/schema/genesis_datacard.yaml"))
guide = read_tar("template/latest/data_card_field_reference_guide.md")
original_template = read_tar("template/latest/genesis_datacard_merged_shared.yaml")
norm = lambda s: " ".join(str(s).replace("\u2014", "-").split()).strip(" \"'").lower()

# ---------------------------------------------------------------- Step 0
print("== Step 0: original template (tarball) vs Vedant's template")
a = original_template.splitlines()
b = open(args.template, encoding="utf-8").read().splitlines()
kinds = Counter()
for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
    if op == "equal":
        continue
    flattened = {re.sub(r"^(\s*)- ", r"\1  ", x).strip() for x in a[i1:i2]}
    if all(x.strip() in flattened for x in b[j1:j2]):
        kinds["list item flattened ('- ' removed, re-indented)"] += 1
    else:
        kinds["other (re-indent or wording)"] += 1
        print(f"   original L{i1 + 1}: {a[i1:i2][:1]} -> {b[j1:j2][:1]}")
for k, v in kinds.items():
    print(f"   {k}: {v} chunk(s)")

# ---------------------------------------------------------------- Step 1: template
tmpl, stack, last = {}, [], None
for no, raw in enumerate(b, 1):
    s = raw.strip()
    if not s:
        continue
    if s.startswith("#"):
        if last and raw.index("#") > 30:  # continuation comment aligned to the right
            tmpl[last]["comment"] += " " + s.lstrip("#").strip()
        continue
    m = re.match(r"^(\s*)(-\s+)?([A-Za-z_]\w*):(.*)$", raw)
    if not m:
        continue
    ind = len(m[1]) + (len(m[2]) if m[2] else 0)
    while stack and stack[-1][0] >= ind:
        stack.pop()
    stack.append((ind, m[3]))
    path = ".".join(k for _, k in stack)
    val, com = (m[4].split(" #", 1) + [""])[:2] if " #" in m[4] else (m[4], "")
    tmpl[path] = {"line": no, "value": val.strip(), "comment": com.strip()}
    last = path
for n in tmpl.values():
    t = re.match(r"\[([^\]]*)\]", n["comment"])
    n["tag"] = t.group(1) if t else ""
    n["text"] = n["comment"][t.end():].strip() if t else n["comment"]

# ---------------------------------------------------------------- Step 2: breakdown
bd = {}


def walk(node, path):
    for k, v in node.items():
        if isinstance(v, dict) and "required" in v:  # a field node
            p = f"{path}.{k}" if path else k
            bd[p] = v
            if isinstance(v.get("value"), dict):
                walk(v["value"], p)


walk(yaml.safe_load(open(args.breakdown, encoding="utf-8")), "")

# ---------------------------------------------------------------- Step 3: LinkML schema
classes, slots, enums = schema["classes"], schema.get("slots", {}), schema.get("enums", {})


def class_slots(cname):
    """All slots of a class, including inherited ones, with slot_usage overrides applied."""
    c = classes.get(cname, {})
    out = {}
    if c.get("is_a"):
        out.update(class_slots(c["is_a"]))
    for mixin in c.get("mixins", []) or []:
        out.update(class_slots(mixin))
    for s in c.get("slots", []) or []:
        out[s] = dict(slots.get(s) or {})
    for s, d in (c.get("attributes") or {}).items():
        out[s] = {**out.get(s, {}), **(d or {})}
    for s, d in (c.get("slot_usage") or {}).items():
        out[s] = {**out.get(s, slots.get(s) or {}), **(d or {})}
    return out


sch = {}


def schema_walk(cname, path, depth=0):
    if depth > 12:
        return
    for s, d in class_slots(cname).items():
        p = f"{path}.{s}" if path else s
        rng = d.get("range") or schema.get("default_range", "string")
        sch[p] = {"required": bool(d.get("required")), "multivalued": bool(d.get("multivalued")),
                  "range": rng, "description": d.get("description", ""),
                  "enum": list((enums.get(rng) or {}).get("permissible_values", {}) or []) if rng in enums else None}
        if rng in classes:
            schema_walk(rng, p, depth + 1)


schema_walk("GenesisDatacardClass", "")

# ---------------------------------------------------------------- Step 4: compare
EXTRA = {"none", "not_applicable", "unknown", "other", "n/a", "no"}
stats, rows = Counter(), []
for p, n in bd.items():
    t, s = tmpl.get(p), sch.get(p)
    leaf = not isinstance(n.get("value"), dict)
    r = {"path": p, "leaf": leaf}
    stats["breakdown nodes"] += 1
    stats["path found in template"] += t is not None
    stats["path found in schema"] += s is not None
    if t and leaf:
        tv = t["value"].strip().strip('"').strip("'")
        r["value_eq_template"] = tv == str(n["value"]).strip() or (tv == "[]" and n["value"] == [])
        stats["leaves with a template value"] += 1
        stats["  leaf value == template value"] += r["value_eq_template"]
    if t:
        tag_req = any(x.strip().endswith("_required") or x.strip() == "required" for x in t["tag"].split(","))
        r["required_eq_tag"] = bool(n["required"]) == tag_req
        stats["  required == template tag rule"] += r["required_eq_tag"]
        r["desc_contains_template_comment"] = bool(t["text"]) and norm(t["text"])[:60] in norm(n.get("description", ""))
        stats["  description contains template comment"] += r["desc_contains_template_comment"]
    if s:
        r["required_eq_schema"] = bool(n["required"]) == s["required"]
        stats["  required == schema required"] += r["required_eq_schema"]
        sd = norm(s["description"])
        stats["  description contains schema description"] += bool(sd) and sd[:60] in norm(n.get("description", ""))
    d = norm(n.get("description", ""))
    stats["  description contains reference-guide text"] += bool(d) and any(
        len(c) > 40 and c in norm(guide) for c in (d[:80], d[-80:]))
    if "options" in n:
        stats["dropdown/radio fields"] += 1
        if s and s["enum"]:
            bo = {norm(str(o).split(":")[0]) for o in n["options"]}
            se = {norm(e) for e in s["enum"]}
            r["options_vs_enum"] = "equal" if bo - EXTRA == se - EXTRA else ("breakdown+extras" if se <= bo else "differs")
            stats["  dropdowns whose slot has a schema enum"] += 1
            stats["    options == schema enum (ignoring None/Other...)"] += r["options_vs_enum"] != "differs"
    elif s and s["enum"]:
        stats["schema enum but NO dropdown in breakdown"] += 1
        r["missed_enum"] = s["range"]
    rows.append(r)

print("\n== Step 4: match counts")
for k, v in stats.items():
    print(f"   {k:55} {v}")

# ---------------------------------------------------------------- Step 5: details
R = {r["path"]: r for r in rows}
print("\n== Step 5a: required differs from the template-tag rule  (path | breakdown | tag | schema)")
for p, r in R.items():
    if r.get("required_eq_tag") is False:
        print(f"   {p} | {bd[p]['required']} | [{tmpl[p]['tag']}] | {sch.get(p, {}).get('required')}")
print("\n== Step 5b: dropdown options differ from the schema enum  (breakdown options | template comment)")
for p, r in R.items():
    if r.get("options_vs_enum") == "differs":
        print(f"   {p}: {bd[p]['options']}\n      comment: {tmpl[p]['comment'][:110]}")
print("\n== Step 5c: schema has an enum, breakdown has no dropdown")
for p, r in R.items():
    if r.get("missed_enum"):
        print(f"   {p}  ({r['missed_enum']}, multivalued={sch[p]['multivalued']})")

if args.json:
    json.dump({"stats": stats, "rows": rows}, open(args.json, "w", encoding="utf-8"), indent=1)
    print(f"\nper-field results written to {args.json}")
