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


if __name__ == "__main__":
    test_v12_matches_reference()
    print("ok")
