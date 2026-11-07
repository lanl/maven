"""Tests for validate_breakdown.py: real breakdowns pass, deliberately broken copies are caught.
Run: python test_validate.py   (or: python -m pytest test_validate.py)"""
import copy
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from validate_breakdown import validate  # noqa: E402

TEMPLATES = HERE.parent.parent / "maven" / "metadata_template"
TEMPLATE = (TEMPLATES / "genesis_dc_v1.2_YAML.yaml").read_text(encoding="utf-8")
VEDANT = yaml.safe_load((TEMPLATES / "genesis_dc_breakdown.yaml").read_text(encoding="utf-8"))
GENERATED = yaml.safe_load((HERE / "genesis_dc_v1.2_breakdown.generated.yaml").read_text(encoding="utf-8"))


def errors(breakdown):
    return [f for f in validate(TEMPLATE, breakdown)[2] if f[0] == "ERROR"]


def warnings(breakdown):
    return [f for f in validate(TEMPLATE, breakdown)[2] if f[0] == "WARNING"]


def test_real_breakdowns_pass():
    assert errors(VEDANT) == []
    assert errors(GENERATED) == []
    assert warnings(GENERATED) == []


def test_annotation_warnings_find_known_v12_mistakes():
    found = {(p, m.split(" ")[1]) for _, _, p, m in warnings(VEDANT)}
    assert ("discoverability.datacard.sensitivity.classification_category", "'Top_Secret'") in found  # copy mistake


def test_option_typo_is_caught():
    # The 'Resourcesm' typo was fixed in the repo file (2026-11-04); put it back in a copy to keep the check.
    broken = copy.deepcopy(VEDANT)
    role = broken["discoverability"]["value"]["authors"]["value"]["person"]["value"]["role"]
    role["options"] = ["Resourcesm" if o == "Resources" else o for o in role["options"]]
    found = {(p, m.split(" ")[1]) for _, _, p, m in warnings(broken)}
    assert ("discoverability.authors.person.role", "'Resourcesm'") in found


def test_missing_key_is_caught():
    broken = copy.deepcopy(GENERATED)
    del broken["supports_reusability"]
    assert [p for _, _, p, m in errors(broken) if "missing" in m] == ["supports_reusability"]


def test_changed_value_is_caught():
    broken = copy.deepcopy(GENERATED)
    broken["discoverability"]["value"]["datacard"]["value"]["template_version"]["value"] = "9.9"
    assert any("template_version" in p and "value changed" in m for _, _, p, m in errors(broken))


def test_invented_key_is_caught():
    broken = copy.deepcopy(GENERATED)
    broken["discoverability"]["value"]["made_up"] = {"required": True, "description": "", "value": "__X__"}
    assert any(p == "discoverability.made_up" and "not in the template" in m for _, _, p, m in errors(broken))


def test_missing_block_is_caught_per_section():
    broken = copy.deepcopy(GENERATED)
    del broken["ai_usability"]["value"]["ai_usage"]
    missing = [p for _, sec, p, m in errors(broken) if sec == "ai_usability" and "missing" in m]
    assert "ai_usability.ai_usage.training_use_status" in missing and len(missing) == 11


def test_v20_hidden_dropdown_value_is_checked():
    # a hidden dropdown has options null (2026-11-06): its pre-filled value is checked against the template's list
    tmpl = (HERE / "templates" / "genesis_datacard_v2.0.0_vedant.yaml").read_text(encoding="utf-8")
    bd = yaml.safe_load((HERE / "genesis_dc_v2.0_breakdown.generated.yaml").read_text(encoding="utf-8"))
    cfg = yaml.safe_load((HERE / "config_v2.0.yaml").read_text(encoding="utf-8"))
    gone = cfg["exclude"] + cfg["exclude_top_level"]
    assert [f for f in validate(tmpl, bd, gone)[2] if f[0] == "ERROR"] == []
    role = bd["discoverability"]["value"]["datacard"]["value"]["created_by"]["value"]["creator"]["value"]["ai_model"]["value"]["role"]
    role["value"] = "Not_A_Role"
    assert [p for s, _, p, m in validate(tmpl, bd, gone)[2] if s == "ERROR"] == [
        "discoverability.datacard.created_by.creator.ai_model.role"]


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok ", name)
