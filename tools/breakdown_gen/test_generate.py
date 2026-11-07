"""Regression check: regenerate v1.2 and compare with Vedant's hand-made breakdown.
Run: python -m pytest test_generate.py   (or: python test_generate.py)"""
import subprocess
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).parent
REFERENCE = HERE.parent.parent / "maven" / "metadata_template" / "genesis_dc_breakdown.yaml"  # Vedant's v1.2 breakdown
sys.path.insert(0, str(HERE))
from compare_breakdowns import check_rules, compare  # noqa: E402


def test_v12_matches_reference():
    out = HERE / "genesis_dc_v1.2_breakdown.generated.yaml"
    subprocess.run([sys.executable, str(HERE / "generate_breakdown.py"), str(HERE / "config_v1.2.yaml")], check=True)
    gen = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert check_rules(gen) == []
    score, rows, g, r = compare(gen, yaml.safe_load(REFERENCE.read_text(encoding="utf-8")))
    assert not rows["only in reference"] and not rows["only in generated"]  # same 379 fields
    assert score["value"][0] == score["value"][1]                           # every placeholder value
    assert score["conditional"][0] == score["conditional"][1]               # every one-of block
    assert score["required"][0] / score["required"][1] >= 0.95              # rest are Vedant's own calls
    assert score["type"][0] / score["type"][1] >= 0.95                      # rest are vocabularies he did not use


def test_examples_after_eg_are_not_a_vocabulary():
    from generate_breakdown import comment_vocab
    # v2.0 known_issues: the colons inside the timestamp must not end the 'e.g.'
    assert comment_vocab("Be explicit. e.g., drift after 2023-06-01T12:00:00Z | Sensor drift | not_applicable") is None
    assert comment_vocab("select one from list: Open | Restricted") == ["Open", "Restricted"]
    # v2.0 hpc_environment: a list match must not start inside a version number
    assert comment_vocab("e.g., Orion: python/3.10, openmpi/4.1 | Summit: python/3.9") is None


def test_v20_has_no_discriminators():
    # Vedant (2026-11-05): no agent_type and no discriminator keys; organization blocks have no description / options
    from compare_breakdowns import fields
    out = HERE / "genesis_dc_v2.0_breakdown.generated.yaml"
    subprocess.run([sys.executable, str(HERE / "generate_breakdown.py"), str(HERE / "config_v2.0.yaml")], check=True)
    f = fields(yaml.safe_load(out.read_text(encoding="utf-8")))
    assert not [p for p, n in f.items() if p.endswith(".agent_type") or "conditional_context" in n
                or "condition_discriminator" in n or "Fill in only if" in n["description"]]
    org = [p for p in f if ".organization" in p]
    assert len(org) == 18 and all(f[p]["description"] == "" and not f[p]["visible"] for p in org)
    assert all(f[p]["options"] is None for p in org if not isinstance(f[p]["value"], dict))
    # required nests through the person block to its group: contact is required, additional_contacts is not
    assert f["discoverability.contact.person.given_name"]["required"] is True
    extra = f["discoverability.additional_contacts.person.given_name"]
    assert extra["required"] is False and extra["description"].startswith("Required if an entry is added.")
    # related_resources.software is itself a list (not a one-of sub-block): its fields keep the list note
    assert f["interoperability.related_resources.software.name"]["description"].startswith("Required if an entry is added.")
    facility = yaml.safe_load(out.read_text(encoding="utf-8"))["discoverability"]["value"]["facilities"]["value"]["name"]
    is_intermediate = yaml.safe_load(out.read_text(encoding="utf-8"))["discoverability"]["value"]["workflow"]["value"]["is_intermediate"]
    assert (is_intermediate["type"], is_intermediate["options"]) == ("dropdown", ["Yes", "No"])  # from __"Yes|No"__
    assert facility["description"].strip() ==("Required if an entry is added. Human-readable name or local string "
                                               "key for the entity.")


def test_v20_uses_vedants_field_format():
    from compare_breakdowns import check_rules
    out = HERE / "genesis_dc_v2.0_breakdown.generated.yaml"
    subprocess.run([sys.executable, str(HERE / "generate_breakdown.py"), str(HERE / "config_v2.0.yaml")], check=True)
    tree = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert check_rules(tree) == []
    datacard = tree["discoverability"]["value"]["datacard"]
    assert list(datacard) == ["description", "visible", "value"]  # a parent has no type / required
    keywords = tree["discoverability"]["value"]["dataset_description"]["value"]["keywords"]
    # Vedant (2026-11-05): leaf sub-fields in this order, mapping right under visible
    assert list(keywords) == ["description", "visible", "mapping", "type", "options", "length", "required", "value"]
    assert {k: keywords[k] for k in ("type", "options", "length", "required", "value", "mapping")} == \
        {"type": "list", "options": None, "length": 3, "required": True, "value": [], "mapping": None}
    # Vedant (2026-11-05): the supports_* flags are not shown and are always Yes
    flags = [k for k in tree if k.startswith("supports_")]
    assert len(flags) == 6 and all((tree[k]["type"], tree[k]["visible"], tree[k]["value"]) == ("dropdown", False, "Yes") for k in flags)


def test_v20_excluded_fields_are_gone():
    # Vedant's removal list (2026-11-05), config `exclude`
    from compare_breakdowns import fields
    out = HERE / "genesis_dc_v2.0_breakdown.generated.yaml"
    subprocess.run([sys.executable, str(HERE / "generate_breakdown.py"), str(HERE / "config_v2.0.yaml")], check=True)
    paths = fields(yaml.safe_load(out.read_text(encoding="utf-8")))
    assert not [p for p in paths if p.rsplit(".", 1)[-1] in ("orcid", "ror_id") or p.startswith("discoverability.contributors")
                or ".software.identifier" in p or ".ai_model.identifier" in p or p.startswith("reusability.integrity")]
    assert {p.split(".")[2] for p in paths if p.startswith("discoverability.authors.")
            and not isinstance(paths[p]["value"], str) and p.count(".") == 2} == {"person", "organization"}
    assert "interoperability.provenance.source_data.identifier.type" in paths  # identifiers elsewhere stay


def test_v20_single_value_fields():
    # Vedant (2026-11-05, part 3): these are one value, not a list (the LinkML schema still says multivalued)
    from compare_breakdowns import fields
    out = HERE / "genesis_dc_v2.0_breakdown.generated.yaml"
    subprocess.run([sys.executable, str(HERE / "generate_breakdown.py"), str(HERE / "config_v2.0.yaml")], check=True)
    f = fields(yaml.safe_load(out.read_text(encoding="utf-8")))
    single = [p for p in f if p.endswith(".role")] + [
        "discoverability.datacard.sensitivity.classification_category",
        "governed_use.non_sensitivity_governance_metadata.privacy.privacy_control_basis"]
    assert len(single) == 22 and all(f[p]["type"] == "dropdown"
                                     and isinstance(f[p]["value"], str) for p in single)
    assert f["discoverability.datacard.created_by.contribution_date"]["type"] == "string"  # hidden, still typed
    for block in ("discoverability.contact.person", "interoperability.provenance.source_data",
                  "accessibility.access.intended_repositories"):  # single blocks (de-listed in Vedant's template)
        assert isinstance(f[block]["value"], dict)


def test_v20_hidden_prefilled_and_mapped():
    # Vedant (2026-11-05, part 4): hidden fields, pre-filled values, mappings
    from compare_breakdowns import fields
    out = HERE / "genesis_dc_v2.0_breakdown.generated.yaml"
    subprocess.run([sys.executable, str(HERE / "generate_breakdown.py"), str(HERE / "config_v2.0.yaml")], check=True)
    f = fields(yaml.safe_load(out.read_text(encoding="utf-8")))
    hidden = lambda p: not f[p]["visible"]
    assert all(hidden(p) for p in f if ".organization" in p)
    assert all(hidden(p) for p in f if p.startswith(("discoverability.datacard.created_by", "reusability.data_quality")))
    assert (f["xCard.card_type"]["value"], hidden("xCard.card_type")) == ("dataset", True)
    assert f["discoverability.datacard.template_version"]["value"] == "2.0.0"
    assert f["discoverability.datacard.sensitivity.cui_status"]["mapping"] == "discoverability.sensitivity.cui_status"
    assert f["discoverability.datacard.created_by.creator.person.affiliation.name"]["mapping"] == \
        "discoverability.contact.person.affiliation.name"
    assert hidden("discoverability.contact.organization.name") and not hidden("discoverability.contact.person.given_name")
    assert not hidden("discoverability.contact.person.email") and not hidden("discoverability.sensitivity.cui_status")
    # Vedant (2026-11-06): every hidden field has an empty description and options null, but keeps its type
    for p, n in f.items():
        if hidden(p):
            assert n["description"] == "" and n.get("options") is None, p
            if not isinstance(n["value"], dict):
                assert n["type"] in ("int", "float", "string", "list", "dropdown"), p
    assert f["discoverability.datacard.filename"]["type"] == "string" and f["discoverability.datacard.filename"]["value"] == ""
    assert (f["discoverability.datacard.template_version"]["type"], f["discoverability.datacard.template_version"]["value"]) == ("int", "2.0.0")  # Vedant: int (2026-11-06)
    # identification.project is visible and empty; tags.project is hidden, empty and copied from it (2026-11-06)
    ip, tp = f["discoverability.identification.project"], f["discoverability.dataset_description.tags.project"]
    assert (ip["visible"], ip["value"], ip["mapping"]) == (True, "", None)
    assert (tp["visible"], tp["value"], tp["mapping"]) == (False, "", "discoverability.identification.project")
    # contact.valid_until is back, hidden and empty like additional_contacts.valid_until (2026-11-06)
    assert f["discoverability.contact.valid_until"] == f["discoverability.additional_contacts.valid_until"]
    assert (f["discoverability.contact.valid_until"]["visible"], f["discoverability.contact.valid_until"]["value"]) == (False, "")
    # several values each: type list, length 3 (2026-11-06)
    for k in ("authorization_required", "intended_partner_classes", "approved_environments"):
        n = f[f"accessibility.access_policy.{k}"]
        assert (n["visible"], n["type"], n["options"], n["length"], n["value"]) == (True, "list", None, 3, [])
    at = f["governed_use.non_sensitivity_governance_metadata.rights_release_records.agreement_type"]
    assert (at["type"], at["options"], at["length"], at["value"]) == ("list", None, 3, [])
    ru = f["accessibility.dataset_scale.record_unit"]
    assert (ru["type"], ru["options"], ru["value"]) == ("string", None, "")  # free text (2026-11-06)
    # a dropdown shows its options, so its description no longer lists them (2026-11-06); text after the list stays
    assert not [p for p, n in f.items() if n.get("type") == "dropdown" and "Allowed values" in n["description"]]
    assert f["discoverability.sensitivity.source_marking_scheme"]["description"].endswith(
        "governance purposes. If the data is open (public), select None.")
    assert f["discoverability.release_status"]["description"].endswith("readiness for use.")
    assert f["discoverability.datacard.created_by.creator.ai_model.role"]["value"] == "Writing_Original_Draft"  # value kept


def test_v20_description_notes():
    # Vedant (2026-11-05, part 6): notes added to the template text, which stays verbatim
    from compare_breakdowns import fields
    out = HERE / "genesis_dc_v2.0_breakdown.generated.yaml"
    subprocess.run([sys.executable, str(HERE / "generate_breakdown.py"), str(HERE / "config_v2.0.yaml")], check=True)
    f = fields(yaml.safe_load(out.read_text(encoding="utf-8")))
    p = "discoverability.sensitivity.source_marking_string"
    assert f[p]["description"].startswith("Exact marking/banner/control text")
    assert f[p]["description"].endswith("OFFICIAL USE ONLY. If the data is open (public), enter None.")
    assert f["discoverability.datacard.sensitivity.source_marking_string"]["description"] == ""  # hidden + mapped
    assert f["discoverability.dataset_description.task_category"]["description"].startswith("A task category is")
    assert "DATA CARD" in f["discoverability.sensitivity"]["description"]


def test_v20_repeated_blocks_are_lists():
    # Vedant (2026-11-06): the block with the template dash ('- person:') is a list; '- name: ...' makes the block itself
    # a list; every list (blocks and leaves) has length 3 for now; other blocks (e.g. affiliation) get no type
    from compare_breakdowns import fields
    out = HERE / "genesis_dc_v2.0_breakdown.generated.yaml"
    subprocess.run([sys.executable, str(HERE / "generate_breakdown.py"), str(HERE / "config_v2.0.yaml")], check=True)
    f = fields(yaml.safe_load(out.read_text(encoding="utf-8")))
    blocks = {p for p, n in f.items() if isinstance(n["value"], dict) and "type" in n}
    assert {"discoverability.additional_contacts.person", "discoverability.authors.person",
            "discoverability.sponsor_organizations", "governed_use.review_provenance_companion"} <= blocks and len(blocks) == 12
    assert all((f[p]["type"], f[p]["length"]) == ("list", 3) for p in blocks)  # hidden ones too (2026-11-06)
    assert list(f["discoverability.authors.person"]) == ["description", "visible", "type", "length", "value"]
    assert "type" not in f["discoverability.authors"] and "type" not in f["discoverability.authors.person.affiliation"]
    assert all(n["length"] == 3 for n in f.values() if not isinstance(n["value"], dict) and n.get("type") == "list")


def test_hidden_parent_hides_children():
    # Vedant (2026-11-05): if a parent is not visible, its children are not visible either
    from compare_breakdowns import check_v2_rules
    from generate_breakdown import apply_hidden_and_mapping
    leaf = lambda: {"description": "", "visible": True, "type": "string", "options": None, "length": None,  # noqa: E731
                    "required": False, "value": "", "mapping": None}
    tree = {"a": {"description": "", "visible": False, "value": {"b": {"description": "", "visible": True,
                                                                         "value": {"c": leaf()}}}}}
    assert check_v2_rules(tree)  # a visible child under a hidden parent is reported
    apply_hidden_and_mapping(tree)  # parent hidden by an override, not by `hidden`
    assert tree["a"]["value"]["b"]["visible"] is False and tree["a"]["value"]["b"]["value"]["c"]["visible"] is False
    assert check_v2_rules(tree) == []


def test_stale_hidden_path_stops_the_run():
    from generate_breakdown import apply_hidden_and_mapping
    tree = {"a": {"description": "", "visible": True, "value": {"b": {"description": "", "visible": True, "value": ""}}}}
    try:
        apply_hidden_and_mapping(tree, ["a.no_such"])
        raise AssertionError("stale hidden path accepted")
    except KeyError:
        pass


def test_stale_exclude_pattern_stops_the_run():
    from generate_breakdown import apply_exclude, parse_template
    nodes, _ = parse_template("a:  # x\n  b: __B__  # y\n  c: __C__  # z\n")
    kept, _, _ = apply_exclude(nodes, ["*.b"])
    assert [n["path"] for n in kept] == ["a", "a.c"]
    for bad in (["*.no_such"], ["a.b", "a.c"]):  # unknown pattern; a block left without children
        try:
            apply_exclude(nodes, bad)
            raise AssertionError(bad)
        except (KeyError, ValueError):
            pass


def test_unknown_override_paths_are_listed():
    # a new template version that renames fields must name every stale override, not crash on the first
    cfg = yaml.safe_load((HERE / "config_v2.0.yaml").read_text(encoding="utf-8"))
    cfg["overrides"].update({"discoverability.no_such_field": {"required": True}, "no_such_section.x": {"required": True}})
    tmp, out = HERE / "config_test_stale_override.yaml", HERE / "stale_override.generated.yaml"
    tmp.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
    try:
        r = subprocess.run([sys.executable, str(HERE / "generate_breakdown.py"), str(tmp), "-o", str(out)],
                           capture_output=True, text=True)
    finally:
        tmp.unlink()
    assert r.returncode != 0 and not out.exists()
    assert "override paths not in the template" in r.stderr
    assert "discoverability.no_such_field" in r.stderr and "no_such_section.x" in r.stderr


if __name__ == "__main__":
    test_v12_matches_reference()
    test_examples_after_eg_are_not_a_vocabulary()
    test_v20_has_no_discriminators()
    test_v20_uses_vedants_field_format()
    test_v20_excluded_fields_are_gone()
    test_v20_single_value_fields()
    test_v20_hidden_prefilled_and_mapped()
    test_v20_description_notes()
    test_v20_repeated_blocks_are_lists()
    test_hidden_parent_hides_children()
    test_stale_hidden_path_stops_the_run()
    test_stale_exclude_pattern_stops_the_run()
    test_unknown_override_paths_are_listed()
    print("ok")
