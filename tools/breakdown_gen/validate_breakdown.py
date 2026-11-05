"""Validate a MAVEN breakdown against the datacard template it was made from.

Independent of how the breakdown was produced (by hand, by an LLM, or by generate_breakdown.py): this script
does not use the generator's code. It reads the template with plain yaml.safe_load and its own comment reader,
then checks, section by section, that nothing was lost or invented in the conversion.

Checks:
  ERROR    1. Completeness   every template key is in the breakdown at the same path, and no key was invented
  ERROR    2. Values         every leaf keeps the template's placeholder value (v2 format: or is empty, or fills a
                             placeholder with a value that is one of its dropdown options)
  ERROR    3. MAVEN rules    the breakdown can be rendered by MAVEN's Tier 1 form (compare_breakdowns.check_rules)
  WARNING  4. Annotations    a [*_required] tag is not required; a vocabulary in the comment has no dropdown;
                             a dropdown option does not appear in the template comment

Expected differences are reported, not counted as errors: template blocks tagged [reference_only...],
blocks named with --allow-missing, and a discriminator the generator adds next to one-of blocks (--allow-extra-key).

Usage:
    python validate_breakdown.py TEMPLATE BREAKDOWN [--allow-missing xCard] [--allow-missing-from CONFIG] [--report report.md]
TEMPLATE may be a file or "archive.zip::path/inside/archive". Exit code 1 if there is any ERROR.
"""
import argparse
import re
import sys
import tarfile
import zipfile
from fnmatch import fnmatch
from pathlib import Path

import yaml

from compare_breakdowns import check_rules

sys.stdout.reconfigure(encoding="utf-8")
PLACEHOLDER = re.compile(r"\$\{.*\}|__.*__|\[\]")  # ${X}, __X__ or an empty list in the template
NONE_LIKE = {"none", "not_applicable", "n/a", "na", "no", "other", "unknown"}
KEY_LINE = re.compile(r"^(\s*)(-\s+)?([A-Za-z_]\w*):(.*)$")
VOCAB_RE = re.compile(r"(?:vocabulary|select one(?: from)?(?: list)?|select from|select all that apply|list all that apply|"
                      r"allowed values|select one of|select the single best-fit)\s*:\s*(.+)", re.I)


def read_text(spec):
    path, _, member = str(spec).partition("::")
    if not member:
        return Path(path).read_text(encoding="utf-8")
    if path.endswith(".zip"):
        with zipfile.ZipFile(path) as z:
            return z.read(member).decode("utf-8")
    with tarfile.open(path) as t:
        return t.extractfile(member).read().decode("utf-8")


# ----------------------------------------------------------------------------- template side
def template_leaves(node, path="", out=None):
    """Template (yaml.safe_load) -> {path: value} for every key. Lists of dicts are merged, as MAVEN does
    (app.py get_children); a list holding one scalar counts as that scalar."""
    out = {} if out is None else out
    for k, v in node.items():
        p = f"{path}.{k}" if path else k
        if isinstance(v, list) and v and all(isinstance(i, dict) for i in v):
            merged = {}
            for item in v:
                merged.update({ik: iv for ik, iv in item.items() if ik not in merged})
            v = merged
        if isinstance(v, dict) and v:
            out[p] = {}
            template_leaves(v, p, out)
        else:
            out[p] = v
    return out


def template_comments(text):
    """{path: comment text} from the raw template, read line by line (own reader, not the generator's).
    A key's comment is the text after '#' on its line plus the comment-only lines that follow it."""
    out, stack, last = {}, [], None
    for raw in text.splitlines():
        s = raw.strip()
        if s.startswith("#"):
            if last:
                out[last] += " " + s.lstrip("#").strip()
            continue
        m = KEY_LINE.match(raw)
        if not m:
            continue
        indent = len(m.group(1)) + len(m.group(2) or "")
        while stack and stack[-1][0] >= indent:
            stack.pop()
        stack.append((indent, m.group(3)))
        path = ".".join(k for _, k in stack)
        if path in out:  # a later list item repeats keys already seen
            last = None
            continue
        rest = m.group(4)
        hit = re.search(r"\s#\s?(.*)$", rest)
        out[path] = hit.group(1) if hit else ""
        last = path
    return out


def tags_of(comment):
    m = re.match(r"\s*\[([^\]]*)\]", comment or "")
    return [t.strip() for t in m.group(1).split(",")] if m else []


def vocabulary(comment):
    """A choice list written after a keyword ('use vocabulary:', 'select one from list:', 'Allowed values:', …),
    or at the start of the comment ('doi | ark | …'). Lists after 'e.g.' are examples, not vocabularies."""
    text = re.sub(r"^\s*\[[^\]]*\]\s*", "", comment or "")
    m = VOCAB_RE.search(text) or re.match(r"^\s*((?:\"?[\w\-]+\"?\s*\|\s*)+\"?[\w\-]+\"?)", text)
    if not m or re.search(r"e\.g\.[^:]*$", text[:m.start(1)], re.I):
        return None
    items = [i.strip().strip('"').strip(".") for i in m.group(1).split("|")]
    items[-1] = items[-1].split()[0].strip('"') if items[-1].split() else ""
    items = [i for i in items if i]
    return items if len(items) >= 2 else None


# ----------------------------------------------------------------------------- breakdown side
def breakdown_fields(tree, path="", out=None):
    out = {} if out is None else out
    for k, v in tree.items():
        if isinstance(v, dict) and "description" in v:  # v2 format: parents have no `required`
            p = f"{path}.{k}" if path else k
            out[p] = v
            if isinstance(v.get("value"), dict):
                breakdown_fields(v["value"], p, out)
    return out


def same_value(t, b):
    norm = lambda x: x[0] if isinstance(x, list) and len(x) == 1 and not isinstance(x[0], (dict, list)) else x
    t, b = norm(t), norm(b)
    if isinstance(t, list) or isinstance(b, list):
        return t == b
    return str(t).strip() == str(b).strip()


# ----------------------------------------------------------------------------- validation
def validate(template_text, breakdown, allow_missing=(), allow_extra_keys=("agent_type",)):
    tmpl = template_leaves(yaml.safe_load(template_text))
    comments = template_comments(template_text)
    bd = breakdown_fields(breakdown)
    findings = []  # (severity, section, path, message)

    def add(sev, p, msg):
        findings.append((sev, section_of(p), p, msg))

    for p in tmpl:
        if p in bd:
            continue
        top = p.split(".")[0]
        reason = next((q for q in (p.rsplit(".", i)[0] for i in range(p.count(".") + 1))
                       if any("reference_only" in t for t in tags_of(comments.get(q)))), None)
        if reason or top in allow_missing or any(fnmatch(p, a) or fnmatch(p, a + ".*") for a in allow_missing):
            add("EXPECTED", p, "not in breakdown: " + (f"[reference_only] block ({reason})" if reason else "excluded by --allow-missing"))
        else:
            add("ERROR", p, "missing from the breakdown")
    for p in bd:
        if p in tmpl:
            continue
        parent, _, key = p.rpartition(".")
        if key in allow_extra_keys and any(f"{parent}.{b}" in bd and bd[f"{parent}.{b}"].get("conditional_context")
                                           for b in bd[p].get("options") or []):
            add("EXPECTED", p, "discriminator added for the one-of blocks " + str(bd[p].get("options")))
        else:
            add("ERROR", p, "in the breakdown but not in the template")

    for p, tv in tmpl.items():
        if p not in bd or isinstance(tv, dict):
            continue
        bv = bd[p].get("value")
        if isinstance(bv, dict):
            add("ERROR", p, "template has a value, breakdown has a group")
        elif "visible" in bd[p] and bv in ("", []):
            pass  # v2 format: leaf values start empty
        elif "visible" in bd[p] and bd[p].get("type") == "dropdown" and bv not in bd[p].get("options", []):
            add("ERROR", p, f"pre-filled value {bv!r} is not one of the options")
        elif "visible" in bd[p] and PLACEHOLDER.fullmatch(str(tv).strip()) and not same_value(tv, bv):
            add("EXPECTED", p, f"pre-filled: template {tv!r} -> breakdown {bv!r}")  # v2: a placeholder may be filled in
        elif not same_value(tv, bv):
            add("ERROR", p, f"value changed: template {tv!r} -> breakdown {bv!r}")

    for err in check_rules(breakdown):
        add("ERROR", err.split(":")[0], "MAVEN rule: " + err.split(":", 1)[-1].strip())

    for p, f in bd.items():
        if p not in tmpl or isinstance(tmpl[p], dict):
            continue
        tags = tags_of(comments.get(p))
        if any(t == "required" or (t.endswith("_required") and t != "situational_required") for t in tags) \
                and not f.get("required"):
            parents = [p.rsplit(".", i)[0] for i in range(1, p.count(".") + 1)]
            optional = next((q for q in parents if q in bd and bd[q].get("required") is False), None)
            add("WARNING", p, f"tagged [{', '.join(tags)}] but required: false"
                + (f" (inside optional block `{optional}`; MAVEN would otherwise force it)" if optional else ""))
        vocab = vocabulary(comments.get(p))
        if vocab and f.get("type") not in ("dropdown", "radio") and "." in p:  # top-level supports_* are drawn as Yes/No by MAVEN itself
            add("WARNING", p, f"comment lists choices {vocab[:6]}{'…' if len(vocab) > 6 else ''} but there is no dropdown")
        text = ((comments.get(p) or "") + " " + str(tmpl[p])).lower()  # choices may sit in the placeholder: ${"Yes|No"}
        for o in f.get("options") or []:
            code = str(o).split(":")[0].strip().strip('"')
            if code.lower() not in NONE_LIKE and code.lower() not in text and f.get("type") in ("dropdown", "radio") and p in comments \
                    and not any(code == b for b in ("person", "organization", "ai_model", "software")):
                add("WARNING", p, f"option {code!r} does not appear in the template comment")
    return tmpl, bd, findings


def section_of(path):
    top = path.split(".")[0]
    return "intended capabilities (supports_*)" if top.startswith("supports_") else top


def summarize(tmpl, bd, findings):
    sections = {}
    for p in tmpl:
        sections.setdefault(section_of(p), [0, 0, 0, 0, 0])[0] += 1
    for p in bd:
        sections.setdefault(section_of(p), [0, 0, 0, 0, 0])[1] += 1
    col = {"ERROR": 2, "WARNING": 3, "EXPECTED": 4}
    for sev, sec, _, _ in findings:
        sections.setdefault(sec, [0, 0, 0, 0, 0])[col[sev]] += 1
    return sections


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("template")
    ap.add_argument("breakdown")
    ap.add_argument("--allow-missing", nargs="*", default=[],
                    help="template blocks deliberately left out (e.g. xCard); '*' matches any part of a path")
    ap.add_argument("--allow-missing-from", metavar="CONFIG",
                    help="also allow the generator config's exclude_top_level and exclude lists")
    ap.add_argument("--report", help="write the full findings as markdown")
    a = ap.parse_args()
    if a.allow_missing_from:  # reads only the two lists; the generator's code is still not used
        cfg = yaml.safe_load(Path(a.allow_missing_from).read_text(encoding="utf-8"))
        a.allow_missing += (cfg.get("exclude_top_level") or []) + (cfg.get("exclude") or [])
    tmpl, bd, findings = validate(read_text(a.template), yaml.safe_load(Path(a.breakdown).read_text(encoding="utf-8")),
                                  a.allow_missing)
    rows = summarize(tmpl, bd, findings)
    head = f"{'section':38} {'template':>8} {'breakdown':>9} {'errors':>6} {'warnings':>8} {'expected':>8}"
    lines = [head, "-" * len(head)]
    for sec, (t, b, e, w, x) in rows.items():
        lines.append(f"{sec:38} {t:8} {b:9} {e:6} {w:8} {x:8}   {'OK' if not e else 'FAIL'}")
    n_err = sum(1 for f in findings if f[0] == "ERROR")
    lines.append(f"\n{len(tmpl)} template keys, {len(bd)} breakdown fields: "
                 f"{n_err} error(s), {sum(1 for f in findings if f[0] == 'WARNING')} warning(s)")
    print("\n".join(lines))
    for sev in ("ERROR", "WARNING"):
        for s, sec, p, msg in findings:
            if s == sev:
                print(f"  {sev:7} {p}: {msg}")
    if a.report:
        md = ["# Breakdown validation", "", f"- Template: `{a.template}`", f"- Breakdown: `{a.breakdown}`", "",
              "| Section | Template keys | Breakdown fields | Errors | Warnings | Expected |", "|---|---|---|---|---|---|"]
        md += [f"| {sec} | {t} | {b} | {e} | {w} | {x} |" for sec, (t, b, e, w, x) in rows.items()]
        for sev in ("ERROR", "WARNING", "EXPECTED"):
            hits = [f for f in findings if f[0] == sev]
            md += ["", f"## {sev} ({len(hits)})", ""] + [f"- `{p}`: {msg}" for _, _, p, msg in hits]
        Path(a.report).write_text("\n".join(md) + "\n", encoding="utf-8")
        print(f"\nreport written to {a.report}")
    sys.exit(1 if n_err else 0)


if __name__ == "__main__":
    main()
