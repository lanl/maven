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


def test_oneof_blocks_say_how_to_choose():
    out = HERE / "genesis_dc_v2.0_breakdown.generated.yaml"
    subprocess.run([sys.executable, str(HERE / "generate_breakdown.py"), str(HERE / "config_v2.0.yaml")], check=True)
    creator = yaml.safe_load(out.read_text(encoding="utf-8"))["discoverability"]["value"]["datacard"]["value"]["created_by"]["value"]["creator"]["value"]
    assert creator["organization"]["description"].strip() == ("An organization or group of individuals. Fill in only if the "
                                                      "creator is an organization; leave person, ai_model and software empty.")
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
    assert {k: keywords[k] for k in ("type", "options", "length", "required", "value", "mapping")} == \
        {"type": "list", "options": None, "length": 0, "required": True, "value": [], "mapping": None}
    assert tree["supports_reusability"]["type"] == "dropdown" and tree["supports_reusability"]["value"] == ""


def test_v20_excluded_fields_are_gone():
    # Vedant's removal list (2026-11-05), config `exclude`
    from compare_breakdowns import fields
    out = HERE / "genesis_dc_v2.0_breakdown.generated.yaml"
    subprocess.run([sys.executable, str(HERE / "generate_breakdown.py"), str(HERE / "config_v2.0.yaml")], check=True)
    paths = fields(yaml.safe_load(out.read_text(encoding="utf-8")))
    assert not [p for p in paths if p.rsplit(".", 1)[-1] in ("orcid", "ror_id") or p.startswith("discoverability.contributors")
                or ".software.identifier" in p or ".ai_model.identifier" in p or p.startswith("reusability.integrity")]
    assert paths["discoverability.authors.agent_type"]["options"] == ["person", "organization"]
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
    assert len(single) == 22 and all(f[p]["type"] == "dropdown" and isinstance(f[p]["value"], str) for p in single)
    assert f["discoverability.datacard.created_by.contribution_date"]["type"] == "string"
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
    assert (f["discoverability.contact.agent_type"]["value"], hidden("discoverability.contact.agent_type")) == ("person", True)
    assert not hidden("discoverability.contact.person.email") and not hidden("discoverability.sensitivity.cui_status")


def test_v20_description_notes():
    # Vedant (2026-11-05, part 6): notes added to the template text, which stays verbatim
    from compare_breakdowns import fields
    out = HERE / "genesis_dc_v2.0_breakdown.generated.yaml"
    subprocess.run([sys.executable, str(HERE / "generate_breakdown.py"), str(HERE / "config_v2.0.yaml")], check=True)
    f = fields(yaml.safe_load(out.read_text(encoding="utf-8")))
    for p in ("discoverability.sensitivity.source_marking_string", "discoverability.datacard.sensitivity.source_marking_string"):
        assert f[p]["description"].startswith("Exact marking/banner/control text")
        assert f[p]["description"].endswith("OFFICIAL USE ONLY. If the data is open (public), enter None.")
    assert f["discoverability.dataset_description.task_category"]["description"].startswith("A task category is")
    assert "DATA CARD" in f["discoverability.sensitivity"]["description"]


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
    test_oneof_blocks_say_how_to_choose()
    test_v20_uses_vedants_field_format()
    test_v20_excluded_fields_are_gone()
    test_v20_single_value_fields()
    test_v20_hidden_prefilled_and_mapped()
    test_v20_description_notes()
    test_stale_hidden_path_stops_the_run()
    test_stale_exclude_pattern_stops_the_run()
    test_unknown_override_paths_are_listed()
    print("ok")
