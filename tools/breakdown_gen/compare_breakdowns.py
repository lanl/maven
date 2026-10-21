"""Compare a generated breakdown with a reference breakdown (e.g. Vedant's v1.2) and check MAVEN's rules.

Usage:
    python compare_breakdowns.py generated.yaml [--reference reference.yaml] [--diff diff.md]

Without --reference it only runs the rule checks.
"""
import argparse
import sys
from difflib import SequenceMatcher

import yaml

sys.stdout.reconfigure(encoding="utf-8")


def fields(tree, path=""):
    out = {}
    for k, v in tree.items():
        if isinstance(v, dict) and "required" in v:
            p = f"{path}.{k}" if path else k
            out[p] = v
            if isinstance(v.get("value"), dict):
                out.update(fields(v["value"], p))
    return out


def check_rules(tree):
    """MAVEN's form rules (app.py render_tier1_yaml_form / get_conditional_info / flattened_tier1_fields)."""
    errs = []
    f = fields(tree)
    for p, n in f.items():
        for key in ("required", "description", "value"):
            if key not in n:
                errs.append(f"{p}: missing '{key}'")
        if "type" in n:
            if n["type"] not in ("dropdown", "radio"):
                errs.append(f"{p}: unsupported type {n['type']!r}")
            if not isinstance(n.get("options"), list) or not n["options"]:
                errs.append(f"{p}: type without an options list")
        if isinstance(n.get("value"), list) and n["value"] and isinstance(n["value"][0], dict):
            errs.append(f"{p}: folder value is a list (must be a dict)")
        if n.get("conditional_context") == "one_of_alternatives":
            parent, _, key = p.rpartition(".")
            disc = f.get(f"{parent}.{n.get('condition_discriminator')}")
            if disc is None:
                errs.append(f"{p}: discriminator {n.get('condition_discriminator')!r} is not a sibling")
            elif key not in (disc.get("options") or []):
                errs.append(f"{p}: block name not in discriminator options")
    for top in tree:
        if not top.startswith("supports_") and isinstance(tree[top].get("value"), dict) and f"supports_{top}" not in tree:
            errs.append(f"{top}: top-level section without a supports_{top} key (form KeyError)")
    return errs


norm = lambda s: " ".join(str(s).split()).strip(" \"'").lower()


def compare(gen, ref):
    g, r = fields(gen), fields(ref)
    common = [p for p in r if p in g]
    rows = {"only in reference": [p for p in r if p not in g], "only in generated": [p for p in g if p not in r]}
    score = {}
    for name, same in {
        "required": lambda a, b: bool(a["required"]) == bool(b["required"]),
        "value": lambda a, b: isinstance(a["value"], dict) == isinstance(b["value"], dict) and (
            isinstance(a["value"], dict) or norm(a["value"]) == norm(b["value"])),
        "type": lambda a, b: a.get("type") == b.get("type"),
        "options": lambda a, b: {norm(str(x).split(":")[0]) for x in a.get("options", [])}
        == {norm(str(x).split(":")[0]) for x in b.get("options", [])},
        "conditional": lambda a, b: a.get("condition_discriminator") == b.get("condition_discriminator"),
        "description (>=0.8 similar)": lambda a, b: SequenceMatcher(None, norm(a["description"]),
                                                                     norm(b["description"])).ratio() >= 0.8,
    }.items():
        diff = [p for p in common if not same(g[p], r[p])]
        score[name] = (len(common) - len(diff), len(common))
        rows[f"{name} differs"] = diff
    return score, rows, g, r


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("generated")
    ap.add_argument("--reference")
    ap.add_argument("--diff", help="write a per-field difference list (markdown)")
    a = ap.parse_args()
    gen = yaml.safe_load(open(a.generated, encoding="utf-8"))
    errs = check_rules(gen)
    print(f"MAVEN rule check: {len(errs)} problem(s)")
    for e in errs:
        print("  -", e)
    if not a.reference:
        return
    ref = yaml.safe_load(open(a.reference, encoding="utf-8"))
    score, rows, g, r = compare(gen, ref)
    print(f"\nfields: reference {len(r)}, generated {len(g)}, in both {score['required'][1]}")
    for k, (ok, tot) in score.items():
        print(f"  {k:30} {ok}/{tot} ({100 * ok / tot:.0f}%)")
    print(f"  only in reference: {len(rows['only in reference'])}, only in generated: {len(rows['only in generated'])}")
    if a.diff:
        out = ["# Generated vs reference breakdown", ""]
        for k, ps in rows.items():
            out += [f"## {k} ({len(ps)})", ""]
            for p in ps:
                detail = ""
                if p in g and p in r:
                    key = k.split(" ")[0]
                    pick = {"required": "required", "value": "value", "type": "type", "options": "options",
                            "conditional": "condition_discriminator", "description": "description"}.get(key)
                    if pick:
                        detail = f": generated `{str(g[p].get(pick))[:120]}` / reference `{str(r[p].get(pick))[:120]}`"
                out.append(f"- `{p}`{detail}")
            out.append("")
        open(a.diff, "w", encoding="utf-8").write("\n".join(out))
        print(f"\nper-field differences written to {a.diff}")


if __name__ == "__main__":
    main()
