import pytest
from pathlib import Path
import yaml

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"


def test_rico_template_exists():
    rico_dir = TEMPLATES_DIR / "compliance-red-teamer"
    assert rico_dir.exists()
    assert (rico_dir / "manifest.yaml").exists()
    assert (rico_dir / "soul.md").exists()
    assert (rico_dir / "test-suite.yaml").exists()


def test_rico_manifest_valid():
    manifest_path = TEMPLATES_DIR / "compliance-red-teamer" / "manifest.yaml"
    with open(manifest_path) as f:
        data = yaml.safe_load(f)
    assert data["name"] == "Rico"
    assert data["risk_class"] == "high"
    assert data["budget"]["monthly_limit_eur"] == 140
    assert data["compliance"]["test_mode"] is True


def test_rico_soul_not_empty():
    soul_path = TEMPLATES_DIR / "compliance-red-teamer" / "soul.md"
    content = soul_path.read_text()
    assert len(content) > 100
    assert "Red-Teamer" in content or "red-teamer" in content.lower()


def test_rico_test_suite_has_sections():
    suite_path = TEMPLATES_DIR / "compliance-red-teamer" / "test-suite.yaml"
    with open(suite_path) as f:
        data = yaml.safe_load(f)
    sections = data["test_suite"]["sections"]
    assert len(sections) >= 17
    section_ids = [s["id"] for s in sections]
    assert "01_installation" in section_ids
    assert "09_pii" in section_ids
    assert "17_subagents" in section_ids


def test_rico_test_suite_has_tests():
    suite_path = TEMPLATES_DIR / "compliance-red-teamer" / "test-suite.yaml"
    with open(suite_path) as f:
        data = yaml.safe_load(f)
    total_tests = sum(len(s.get("tests", [])) for s in data["test_suite"]["sections"])
    assert total_tests >= 70  # 84 actual tests in suite
