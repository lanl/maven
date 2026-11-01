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


def test_oneof_blocks_say_how_to_choose():
    out = HERE / "genesis_dc_v2.0_breakdown.generated.yaml"
    subprocess.run([sys.executable, str(HERE / "generate_breakdown.py"), str(HERE / "config_v2.0.yaml")], check=True)
    creator = yaml.safe_load(out.read_text(encoding="utf-8"))["discoverability"]["value"]["datacard"]["value"]["created_by"]["value"]["creator"]["value"]
    assert creator["organization"]["description"].strip() == ("An organization or group of individuals. Fill in only if the "
                                                      "creator is an organization; leave person, ai_model and software empty.")
    facility = yaml.safe_load(out.read_text(encoding="utf-8"))["discoverability"]["value"]["facilities"]["value"]["name"]
    is_intermediate = yaml.safe_load(out.read_text(encoding="utf-8"))["discoverability"]["value"]["workflow"]["value"]["is_intermediate"]
    assert (is_intermediate["type"], is_intermediate["options"]) == ("radio", ["Yes", "No"])  # from __"Yes|No"__
    assert facility["description"].strip() ==("Required if an entry is added. Human-readable name or local string "
                                               "key for the entity.")


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
    test_unknown_override_paths_are_listed()
    print("ok")
