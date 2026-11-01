"""Generate a MAVEN machine-readable breakdown YAML from a datacard template (+ reference guide, + optional schema).

Default (as the v1.2 breakdown was made by hand): the annotated template decides everything. `required` comes
from [*_required] tags and ${...} placeholders, dropdown options from the vocabulary written in comments,
descriptions from the comments. If the config sets `schema`, the LinkML schema decides `required` and options
instead (decision A). Every judgment call is written to a review report instead of being silently guessed.

Usage:
    python generate_breakdown.py config.yaml [-o breakdown.yaml] [--report report.md]

Inputs in the config may be plain paths or archive members: "data-cards-v1.2.0.tar.gz::path/in/archive".
"""
import argparse
import re
import tarfile
import textwrap
import zipfile
from itertools import accumulate
from pathlib import Path

import yaml

FIELD_KEYS = ("required", "description", "conditional_context", "condition_discriminator", "type", "options", "value")
NONE_LIKE = {"none", "not_applicable", "n/a", "na", "no", "other", "unknown"}
YAML_BOOLISH = {"yes", "no", "true", "false", "on", "off", "y", "n", "null", "~"}


# ----------------------------------------------------------------------------- inputs
def read_source(spec, base: Path):
    """Read a file or an archive member ("archive.tar.gz::member"). Archives are read in memory only."""
    if not spec:
        return None
    path, _, member = str(spec).partition("::")
    p = Path(path) if Path(path).is_absolute() else base / path
    if not member:
        return p.read_text(encoding="utf-8")
    if p.suffix == ".zip":
        with zipfile.ZipFile(p) as z:
            return z.read(member).decode("utf-8")
    with tarfile.open(p) as t:
        return t.extractfile(member).read().decode("utf-8")


# ----------------------------------------------------------------------------- template parser
KEY_RE = re.compile(r"^(?P<ind>\s*)(?P<dash>-\s+)?(?P<key>[A-Za-z_][\w]*):(?P<rest>.*)$")
SEPARATOR_RE = re.compile(r"^[#=\-\s]*$")
TITLE_RE = re.compile(r"^[A-Z0-9 &/_()\-]+(\[[^\]]*\])?\s*$")


def split_comment(rest):
    """Split 'value  # comment' at the first '#' that is outside quotes and preceded by whitespace."""
    q = None
    for i, ch in enumerate(rest):
        if ch in "\"'" and (q is None or q == ch):
            q = None if q else ch
        elif ch == "#" and q is None and (i == 0 or rest[i - 1].isspace()):
            return rest[:i].strip(), rest[i + 1:].strip()
    return rest.strip(), ""


def parse_template(text):
    """Annotated template -> ordered list of nodes. Lists ('- item') are flattened: the first item's keys
    become children of the list key (later items are ignored), matching how the v1.2 breakdown was made."""
    nodes, by_path, stack = [], {}, []  # stack: (indent, key)
    pending, last = [], None
    for no, raw in enumerate(text.splitlines(), 1):
        s = raw.strip()
        if not s or s == "---":
            continue
        if s.startswith("#"):
            col = raw.index("#")
            body = s.lstrip("#").strip()
            if last is not None and col >= last["indent"] + 8 and col >= 20:
                last["comment"] += " " + body  # continuation comment aligned to the right of its key
            else:
                pending.append(body)
                last = None
            continue
        m = KEY_RE.match(raw)
        if not m:
            item = re.match(r"^\s*-\s+(.+)$", raw)
            if item and nodes and nodes[-1]["raw_value"] == "" and not nodes[-1].get("item_value"):
                # 'role:' followed by '- __ROLE__': keep the first scalar list item as the field's value
                val, com = split_comment(item.group(1))
                nodes[-1]["raw_value"], nodes[-1]["item_value"] = val, True
                if com and not nodes[-1]["comment"]:
                    nodes[-1]["comment"] = com
                last = nodes[-1]
                continue
            last = None
            continue
        indent = len(m["ind"]) + (len(m["dash"]) if m["dash"] else 0)
        while stack and stack[-1][0] >= indent:
            stack.pop()
        if m["dash"] and stack:
            by_path[".".join(k for _, k in stack)]["is_list"] = True
        stack.append((indent, m["key"]))
        path = ".".join(k for _, k in stack)
        value, comment = split_comment(m["rest"])
        if path in by_path:  # a later list item repeats keys already seen
            last = None
            pending = []
            continue
        node = {"path": path, "key": m["key"], "line": no, "indent": indent, "raw_value": value,
                "comment": comment, "above": [p for p in pending if p and not SEPARATOR_RE.match(p)],
                "is_list": False}
        nodes.append(node)
        by_path[path] = node
        pending, last = [], node
    for n in nodes:
        c = n["comment"]
        tags = re.match(r"\[([^\]]*)\]\s*", c)
        n["tags"] = [t.strip() for t in tags.group(1).split(",")] if tags else []
        text_ = c[tags.end():] if tags else c
        n["text"] = re.sub(r"^###-+.*?-+###\s*", "", text_).strip()
        n["has_children"] = False
    for n in nodes:
        parent = n["path"].rpartition(".")[0]
        if parent in by_path:
            by_path[parent]["has_children"] = True
    return nodes, by_path


# ----------------------------------------------------------------------------- LinkML schema
def load_schema(text, root_class=None):
    """LinkML schema -> {field path: slot info}. Walks classes from the tree root (is_a, mixins,
    attributes and slot_usage are applied)."""
    if not text:
        return {}
    s = yaml.safe_load(text)
    classes, slots, enums = s.get("classes", {}), s.get("slots", {}) or {}, s.get("enums", {}) or {}
    root = root_class or next((c for c, d in classes.items() if (d or {}).get("tree_root")), None)
    if root is None:
        raise SystemExit("schema: no tree_root class found; set root_class in the config")

    def class_slots(cname, seen=()):
        c = classes.get(cname) or {}
        out = {}
        for parent in ([c["is_a"]] if c.get("is_a") else []) + list(c.get("mixins") or []):
            if parent not in seen:
                out.update(class_slots(parent, seen + (cname,)))
        for sl in c.get("slots") or []:
            out[sl] = dict(slots.get(sl) or {})
        for sl, d in (c.get("attributes") or {}).items():
            out[sl] = {**out.get(sl, {}), **(d or {})}
        for sl, d in (c.get("slot_usage") or {}).items():
            out[sl] = {**out.get(sl, dict(slots.get(sl) or {})), **(d or {})}
        return out

    info = {}

    def walk(cname, path, seen):
        for sl, d in class_slots(cname).items():
            p = f"{path}.{sl}" if path else sl
            rng = d.get("range") or s.get("default_range", "string")
            ranges = [rng] + [a.get("range") for a in d.get("any_of") or [] if a.get("range")]
            enum = next((r for r in ranges if r in enums), None)
            pv = (enums.get(enum) or {}).get("permissible_values") or {} if enum else None
            pvs = None if pv is None else [str(x) for x in (pv.keys() if isinstance(pv, dict) else pv)]
            subsets = [str(x) for x in d.get("in_subset") or []]
            # capability requirements are expressed as subsets (e.g. discoverability_required), not only `required`
            req = bool(d.get("required")) or any(x == "required" or (x.endswith("_required") and x != "situational_required")
                                                 for x in subsets)
            info[p] = {"required": req, "multivalued": bool(d.get("multivalued")), "subsets": subsets,
                       "range": rng, "enum": enum, "values": pvs, "description": d.get("description", "")}
            for r in ranges:
                if r in classes and r not in seen:
                    walk(r, p, seen | {r})

    walk(root, "", {root})
    return info


# ----------------------------------------------------------------------------- reference guide
def load_guide_table(text):
    """Rows like '| `key` | values | description |' -> {key: (values, description)}."""
    rows = {}
    for ln in (text or "").splitlines():
        m = re.match(r"^\|\s*`([\w.]+)`\s*\|(.*)\|\s*$", ln)
        if m:
            cells = [c.strip() for c in m.group(2).split("|")]
            rows.setdefault(m.group(1), (cells[0] if len(cells) > 1 else "", cells[-1]))  # first table wins
    return rows


# ----------------------------------------------------------------------------- field rules
ITEM = r'(?:"[^"|]+"|[\w\-]+)'
PIPE_LIST_RE = re.compile(rf"{ITEM}(?:\s*\|\s*{ITEM})+")
# an 'e.g.' still applies unless a label colon ('values: ') or ';' follows it; '12:00:00Z' is not a label
EG_BEFORE_RE = re.compile(r"(e\.g\.|example)(?:(?!:\s|;).)*$", re.I)
BULLET_RE = re.compile(r"(?:^|\s)-\s+\"?([A-Z][\w\-]*)\"?(?::\s*([^.]*))?")
ROW_RE = re.compile(r"\b([A-Z]\w*)(?:\s{2,}([^\s—][^—]*?))?\s+—")  # codes are capitalized: 'Draft —', 'GD  Genome… —' 


def comment_vocab(text):
    """Controlled vocabulary written in a template comment, in the forms the v1.2 breakdown used:
    'A | B | "C d"' anywhere in the comment ('select one from list: ...', 'use vocabulary: ...');
    a bullet list '- A: meaning. - B: meaning.'; or aligned rows 'GD  Genome/Genetic Data  — ...'."""
    allowed = re.search(r"Allowed values:\s*([^|]+(?:\|[^|]+)+)", text)  # v2.0: items may be several words
    if allowed:
        vals = [v.strip().strip('"').strip(".") for v in allowed.group(1).split("|")]
        vals[-1] = re.split(r"\.\s|\s{2,}", vals[-1])[0].strip()  # the list ends at the next sentence
        return vals
    for m in PIPE_LIST_RE.finditer(text):
        before = text[:m.start()].rstrip()
        if EG_BEFORE_RE.search(before) or re.search(r"\w$", before):
            continue  # 'e.g., a b | c d' lists examples of free text, not a vocabulary
        if re.search(r"(#|-\s+\w+:)\s*$", before):
            continue  # inside a commented-out YAML example ('- type: a | b', '  # a | b'), not this field's vocabulary
        return [v.strip().strip('"') for v in m.group(0).split("|")]
    for rx, fmt in ((BULLET_RE, "{}: {}"), (ROW_RE, "{}: {}")):
        rows = rx.findall(text)
        first = rx.search(text)
        if first and EG_BEFORE_RE.search(text[:first.start()].rstrip()):
            continue  # 'e.g., - "NOFORN" - "CNWDI"' lists examples of free text, not a vocabulary
        if len(rows) >= 2:
            return [fmt.format(k, d.strip()) if d and d.strip() else k for k, d in rows]
    return None


def is_required_tag(tags):
    return any(t == "required" or (t.endswith("_required") and t != "situational_required") for t in tags)


class Builder:
    def __init__(self, cfg, nodes, by_path, schema, guide):
        self.cfg, self.nodes, self.by_path, self.schema, self.guide = cfg, nodes, by_path, schema, guide
        alt = cfg.get("alternatives") or {}
        self.alt_blocks = alt.get("blocks", [])
        self.disc_keys = alt.get("discriminator_keys", [])
        self.synth = alt.get("synthesize_as")
        self.block_required_keys = set(alt.get("required_keys", []))
        self.hint = alt.get("choice_hint")
        self.extra = cfg.get("extra_option", "None")
        self.no_extra = set(cfg.get("no_extra_option", []))
        self.report = {k: [] for k in ("required_schema_vs_tag", "options_schema_vs_comment", "extra_option_added",
                                       "multivalued_dropdown", "fallback_to_comment", "not_in_schema",
                                       "discriminator", "no_description", "excluded", "overrides")}
        self.conditional = {}  # alt block path -> discriminator key
        self._req, self._own = {}, {}

    def find_alternatives(self):
        children = {}
        for n in self.nodes:
            parent = n["path"].rpartition(".")[0]
            children.setdefault(parent, []).append(n)
        self.children = children
        self.synthetic = {}
        for parent, kids in children.items():
            alts = [k for k in kids if k["key"] in self.alt_blocks and k["has_children"]]
            if len(alts) < 2 and not any(k["key"] in self.disc_keys for k in kids):
                continue
            if not alts:
                continue
            disc = next((k["key"] for k in kids if k["key"] in self.disc_keys), None)
            if disc is None and self.synth and len(alts) >= 2:
                disc = self.synth
                self.synthetic[parent] = (disc, [a["key"] for a in alts])
                self.report["discriminator"].append(f"`{parent}`: added `{disc}` "
                                                    f"(options {[a['key'] for a in alts]}); not in the template")
            if disc and len(alts) >= 2:
                for a in alts:
                    self.conditional[a["path"]] = disc

    def choice_hint(self, n):
        """'Fill in only if the creator is a person; leave organization empty.' (no discriminator name: it may
        not be in the template). Only blocks that have a sibling alternative get here."""
        parent = n["path"].rpartition(".")[0]
        role = self.hint["roles"].get(parent.rpartition(".")[2], "this entry")
        others = [a for a in self.alt_blocks if a != n["key"] and f"{parent}.{a}" in self.conditional]
        listed = others[0] if len(others) == 1 else ", ".join(others[:-1]) + " and " + others[-1]
        return f"Fill in only if {role} is {self.hint['kinds'][n['key']]}; leave {listed} empty."

    def inside_alternative(self, path):
        """True when an ancestor is an agent block (person / organization / ...), chosen or not."""
        parts = path.split(".")
        return any(parts[i] in self.alt_blocks for i in range(len(parts) - 1))

    def required(self, n):
        """Requirements nest: MAVEN enforces a required leaf whenever its capability is "Yes", whatever its
        parents say, so a field inside an optional block is marked required only if that block is required.
        Exception: inside a one-of block MAVEN enforces it only when the discriminator selects that block
        (app.py render_tier1_yaml_form), i.e. only once the user chose to fill it in, so nesting stops there."""
        if n["path"] in self._req:
            return self._req[n["path"]]
        req = self.own_required(n)
        parent = n["path"].rpartition(".")[0]
        while req and parent in self.by_path:
            if parent in self.conditional:  # selected one-of block: required is enforced only when chosen
                break
            pnode = self.by_path[parent]
            if pnode["key"] not in self.alt_blocks:  # a lone agent block (no alternatives) is skipped over
                req = self.required(pnode)
                break
            parent = parent.rpartition(".")[0]
        self._req[n["path"]] = req
        return req

    def own_required(self, n):
        if n["path"] not in self._own:
            self._own[n["path"]] = self._own_required(n)
        return self._own[n["path"]]

    def _own_required(self, n):
        sch = self.schema.get(n["path"])
        tag_req = is_required_tag(n["tags"])
        parent = n["path"].rpartition(".")[0]
        if n["key"] in self.disc_keys and any(f"{parent}.{b}" in self.by_path for b in self.alt_blocks):
            return True  # a discriminator is required whenever its block is present
        if not self.schema:
            # template only (as the v1.2 breakdown was made): a [*_required] tag or a ${...} placeholder, unless
            # a 'required if ...' tag makes it conditional; a folder is required when any child is required,
            # except an agent block, which its discriminator selects
            cond = any(t.startswith("required if") for t in n["tags"])
            req = tag_req or (not cond and n["raw_value"].strip('"').startswith("${"))
            if n["has_children"] and n["path"] not in self.conditional and not n["tags"]:  # a tag decides for itself
                req = req or any(self.own_required(c) for c in self.children.get(n["path"], [])
                                 if c["path"] not in self.conditional and c["key"] not in self.disc_keys)
        elif sch is None:
            req = tag_req
            if self.schema:
                self.report["not_in_schema"].append(f"`{n['path']}` (template line {n['line']}): required from tag")
        else:
            req = sch["required"]
            if req != tag_req and n["tags"] and "situational_required" not in n["tags"]:
                self.report["required_schema_vs_tag"].append(
                    f"`{n['path']}`: schema says {req}, template tag [{', '.join(n['tags'])}]")
        # v1.2 convention: inside a one-of alternative, required means "required if this block is chosen".
        # A '[required for ai_model]' tag on a field inside the ai_model block says the same thing in words.
        blocks = [b for b in n["path"].split(".")[:-1] if b in self.alt_blocks]
        if not req and self.inside_alternative(n["path"]) and (
                "situational_required" in n["tags"] or tag_req or n["raw_value"].strip('"').startswith("${")
                or n["key"] in self.block_required_keys
                or any(t == f"required for {b}" for t in n["tags"] for b in blocks)):
            req = True
        return bool(req)

    def options(self, n, req):
        sch = self.schema.get(n["path"]) or {}
        # v2.0 writes the choices only in the placeholder: ${"Yes|No"} (required) or __"Yes|No"__ (optional)
        placeholder = re.fullmatch(r'(?:\$\{|__)"([^"]+\|[^"]+)"(?:\}|__)', n["raw_value"])
        vocab = placeholder.group(1).split("|") if placeholder else comment_vocab(n["text"])
        vals = sch.get("values")
        if vals and vocab and {v.lower() for v in vals} != {v.lower() for v in vocab}:
            self.report["options_schema_vs_comment"].append(f"`{n['path']}`: schema {vals} vs comment {vocab}")
        if not vals and vocab:
            vals = vocab
            if self.schema:  # without a schema, the comment is the normal source, not a fallback
                self.report["fallback_to_comment"].append(f"`{n['path']}`: options from comment {vocab}")
        if not vals:
            return None, None
        if sorted(vals) == ["No", "Yes"]:
            return "radio", ["Yes", "No"]
        vals = list(vals)
        if req and not ({v.lower() for v in vals} & NONE_LIKE) and n["path"] not in self.no_extra and self.extra:
            vals.append(self.extra)
            self.report["extra_option_added"].append(f"`{n['path']}`: added `{self.extra}`")
        if sch.get("multivalued"):
            self.report["multivalued_dropdown"].append(f"`{n['path']}`: list field shown as single-choice dropdown")
        return "dropdown", vals

    def description(self, n):
        text = n["text"]
        if not text and n["above"]:
            text = " ".join(a for a in n["above"] if not TITLE_RE.match(a) and not re.match(r"^-?\s*\w+:\s", a))
        if self.cfg.get("guide_for_top_level") and "." not in n["path"] and n["path"] in self.guide:
            text = f"{self.guide[n['path']][1]} {text}".strip()
        if not text:
            sch = self.schema.get(n["path"]) or {}
            text = sch.get("description", "")
            self.report["no_description"].append(f"`{n['path']}`: " + ("used schema description" if text else "empty"))
        # Conditions written in the tag ('[required if X = "Yes"]', '[either A or B is required]') are not
        # enforced by MAVEN, so keep them in front of the text; 'required for <block>' inside that block is enforced.
        blocks = n["path"].split(".")[:-1]
        conds = [t for t in n["tags"] if re.search(r"\brequired\b", t) and " " in t
                 and not any(t == f"required for {b}" for b in blocks)]
        if conds:
            text = " ".join(c[0].upper() + c[1:] + "." for c in conds) + " " + text
        return " ".join(text.split())

    def build(self):
        self.find_alternatives()
        excluded = set(self.cfg.get("exclude_top_level", []))
        root = {}
        made = {"": root}
        for n in self.nodes:
            parent, _, _ = n["path"].rpartition(".")
            if n["path"].split(".")[0] in excluded:
                if "." not in n["path"]:
                    self.report["excluded"].append(f"`{n['path']}` (template line {n['line']})")
                continue
            if parent not in made:
                continue
            if parent in self.synthetic and parent + "." + self.synthetic[parent][0] not in made:
                disc, alts = self.synthetic[parent]
                made[parent][disc] = {"required": self.by_path[parent] is not None and self.required(self.by_path[parent]),
                                      "description": f" {' | '.join(alts)}. Selects which agent block applies.",
                                      "type": "dropdown", "options": alts, "value": "${TYPE}"}
                made[parent + "." + disc] = None
            req = self.required(n)
            field = {"required": req, "description": self.description(n)}
            # '[situational_required]' in an optional list item: MAVEN cannot enforce "required once an entry
            # exists", so say it in the description unless the comment already says 'required'
            # ('if' / 'when' are not enough: "the date when the AI model was accessed" states no condition)
            if (not req and "situational_required" in n["tags"] and self.by_path.get(parent, {}).get("is_list")
                    and not any(a in self.conditional for a in accumulate(n["path"].split("."), lambda x, y: f"{x}.{y}"))
                    and not re.search(r"\brequired\b", field["description"], re.I)):
                field["description"] = f"Required if an entry is added. {field['description']}"
            if n["path"] in self.conditional:
                field["conditional_context"] = "one_of_alternatives"
                field["condition_discriminator"] = self.conditional[n["path"]]
                if self.hint:
                    field["description"] = f"{field['description']} {self.choice_hint(n)}".strip()
            if n["has_children"]:
                field["value"] = {}
                made[n["path"]] = field["value"]
            else:
                if n["key"] in self.disc_keys and parent + "." + next(
                        (k for k in self.alt_blocks if parent + "." + k in self.by_path), "") in self.conditional:
                    alts = [k for k in self.alt_blocks if parent + "." + k in self.by_path]
                    typ, opts = "dropdown", alts
                elif "." not in n["path"]:
                    typ, opts = None, None  # top-level flags: MAVEN always renders them as a Yes/No radio itself
                else:
                    typ, opts = self.options(n, req)
                if typ:
                    field["type"], field["options"] = typ, opts
                field["value"] = RawValue(n["raw_value"])
            made[parent][n["key"]] = field
        for path, patch in (self.cfg.get("overrides") or {}).items():
            node = root
            for part in path.split("."):
                node = node[part] if node is root else node["value"][part]
            node.update(patch)
            self.report["overrides"].append(f"`{path}`: {patch}")
        unknown = sorted(self.no_extra - set(self.by_path))  # a renamed field would otherwise silently get `None` back
        if unknown:
            raise KeyError(f"no_extra_option paths not in the template: {unknown}")
        return root


class RawValue(str):
    """A template value written back verbatim (it already is valid YAML in the template)."""


# ----------------------------------------------------------------------------- writer
def quote_desc(text):
    text = " " + text.strip() if text.strip() else ""
    if '"' in text:
        return "'" + text.replace("'", "''") + "'"
    return '"' + text.replace("\\", "\\\\") + '"'


def scalar(v):
    s = str(v)
    if s.lower() in YAML_BOOLISH or not re.match(r"^[\w\-./()]+$", s):
        return '"' + s.replace('"', '\\"') + '"'
    return s


def emit(tree, indent=0, out=None, width=100):
    out = [] if out is None else out
    pad = " " * indent
    for key, f in tree.items():
        out.append(f"{pad}{key}:")
        p2 = pad + "  "
        out.append(f"{p2}required: {'true' if f['required'] else 'false'}")
        desc = quote_desc(f["description"])
        lines = textwrap.wrap(desc, width=width - len(p2) - 13, break_long_words=False, break_on_hyphens=False) or ['""']
        out.append(f"{p2}description: {lines[0]}")
        out.extend(f"{p2}  {ln}" for ln in lines[1:])
        for k in ("conditional_context", "condition_discriminator"):
            if k in f:
                out.append(f'{p2}{k}: "{f[k]}"')
        if "type" in f:
            out.append(f"{p2}type: {f['type']}")
            out.append(f"{p2}options: [{', '.join(scalar(o) for o in f['options'])}]")
        v = f["value"]
        if isinstance(v, dict):
            out.append(f"{p2}value:")
            emit(v, indent + 4, out, width)
        else:
            out.append(f"{p2}value: {v if str(v) != '' else chr(34) * 2}")
        if indent == 0:
            out.append("")
    return out


def write_report(rep, path, cfg_name):
    titles = {
        "required_schema_vs_tag": "`required` taken from the schema, but the template tag disagrees",
        "options_schema_vs_comment": "Dropdown options: schema enum differs from the template comment (schema used)",
        "extra_option_added": "Extra 'nothing applies' option added to a required dropdown (Vedant's rule 2)",
        "multivalued_dropdown": "List fields rendered as a single-choice dropdown (MAVEN has no multiselect)",
        "fallback_to_comment": "No schema enum; options taken from the template comment",
        "not_in_schema": "Field not found in the schema; `required` taken from the template tag",
        "discriminator": "Discriminators added for one-of blocks",
        "no_description": "No template comment; description fallback",
        "excluded": "Top-level blocks excluded by config",
        "overrides": "Manual overrides applied from the config",
    }
    lines = [f"# Breakdown generation review: {cfg_name}", "",
             "Items below are where the generator had to choose. Check them, then record any change in the "
             "config `overrides:` so the next run reproduces it.", ""]
    for k, title in titles.items():
        lines += [f"## {title} ({len(rep[k])})", ""] + [f"- {x}" for x in rep[k]] + [""]
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config")
    ap.add_argument("-o", "--output")
    ap.add_argument("--report")
    a = ap.parse_args()
    cfg_path = Path(a.config).resolve()
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    base = cfg_path.parent
    tmpl_text = read_source(cfg["template"], base)
    nodes, by_path = parse_template(tmpl_text)
    schema = load_schema(read_source(cfg.get("schema"), base), cfg.get("root_class"))
    guide = load_guide_table(read_source(cfg.get("guide"), base))
    b = Builder(cfg, nodes, by_path, schema, guide)
    tree = b.build()
    header = [f"# {cfg.get('title', 'Generated breakdown')}",
              "# GENERATED by tools/breakdown_gen/generate_breakdown.py; do not edit by hand.",
              "# Change the config (overrides) and regenerate instead.", "---"]
    text = "\n".join(header + emit(tree)) + "\n"
    yaml.safe_load(text)  # the output must be valid YAML
    out = Path(a.output or base / cfg.get("output", "breakdown.generated.yaml"))
    out.write_text(text, encoding="utf-8")
    rep = Path(a.report or out.with_suffix(".review.md"))
    write_report(b.report, rep, cfg_path.name)
    print(f"wrote {out} ({sum(1 for _ in by_path)} template fields) and {rep}")
    for k, v in b.report.items():
        if v:
            print(f"  review {k}: {len(v)}")


if __name__ == "__main__":
    main()
