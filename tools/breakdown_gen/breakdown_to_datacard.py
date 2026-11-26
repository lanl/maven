"""Write a plain datacard YAML from a v2 breakdown, in the layout of the template (Vedant, 2026-11-06).

The keys, their order and the list items ('- person:', '- name:') come from the template itself; a key the breakdown
does not have (removed by the config `exclude`) is left out. Each value is the breakdown's pre-set value (or the value
of the field it is mapped from); every other value is blank: '' or [] for a list field. A list block keeps the
template's single example entry.

Usage: python breakdown_to_datacard.py config_v2.0.yaml   (writes the config's `datacard_output`)
"""
import sys
from pathlib import Path

import yaml

from compare_breakdowns import fields
from generate_breakdown import read_source


def to_datacard(template, bd):
    """template: the parsed template YAML; bd: path -> breakdown field (compare_breakdowns.fields).
    Returns (datacard, template paths left out)."""
    used, dropped = set(), []

    def value(p):
        f = bd[p]
        v = f["value"]
        if v in ("", []) and f.get("mapping"):
            v = bd[f["mapping"]]["value"]
        if v in ("", []):
            return [] if f["type"] == "list" else ""
        return v

    def walk(node, path):
        out = {}
        for k, t in node.items():
            p = f"{path}.{k}" if path else k
            if p not in bd:
                dropped.append(p)
                continue
            used.add(p)
            if isinstance(t, list) and t and isinstance(t[0], dict):  # a template list block: one blank entry
                out[k] = [walk(t[0], p)]
            elif isinstance(t, dict):
                out[k] = walk(t, p)
            else:
                out[k] = value(p)
        return out

    card = walk(template, "")
    missing = sorted(set(bd) - used)
    if missing:  # every breakdown field must have a place in the template
        raise KeyError(f"breakdown fields not found in the template: {missing}")
    return card, dropped


def main():
    cfg_path = Path(sys.argv[1]).resolve()
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    base = cfg_path.parent
    template = yaml.safe_load(read_source(cfg["template"], base))
    bd = fields(yaml.safe_load((base / cfg["output"]).read_text(encoding="utf-8")))
    card, dropped = to_datacard(template, bd)
    head = ["# Datacard written from the breakdown (tools/breakdown_gen/breakdown_to_datacard.py); do not edit by hand.",
            f"# Layout of {cfg['template']}; pre-set values filled in, every other value blank.", "---"]
    body = yaml.safe_dump(card, sort_keys=False, allow_unicode=True, width=float("inf"))
    text = "\n".join(head) + "\n" + body
    assert yaml.safe_load(text) == card  # the output must read back as the same data
    out = base / cfg["datacard_output"]
    out.write_text(text, encoding="utf-8")
    print(f"wrote {out} ({len(bd)} breakdown fields; {len(dropped)} template keys left out: removed by the config)")


if __name__ == "__main__":
    main()
