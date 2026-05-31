"""Tests for stage output schema validation."""
from __future__ import annotations

from flutter_agent.stage_schemas import validate_stage_output


class TestValidateStageOutput:
    def test_classify_valid(self):
        data = {
            "recommended_skills": ["flutter-mobile"],
            "platforms": ["mobile"],
            "complexity": "medium",
        }
        assert validate_stage_output("classify", data) is None

    def test_classify_empty_still_valid(self):
        # All fields have defaults, so even {} passes
        assert validate_stage_output("classify", {}) is None

    def test_classify_extra_fields_allowed(self):
        data = {
            "recommended_skills": ["flutter-mobile"],
            "platforms": ["mobile"],
            "extra_field": "whatever",
        }
        assert validate_stage_output("classify", data) is None

    def test_spec_valid(self):
        data = {
            "user_stories": [{"title": "US1"}],
            "functional_requirements": [{"id": "FR1"}],
        }
        assert validate_stage_output("spec", data) is None

    def test_architecture_valid(self):
        data = {
            "layers": ["presentation", "domain", "data"],
            "third_party": [{"package": "dio", "version": "^5.0.0"}],
            "state_management": "riverpod",
            "patterns": ["repository"],
        }
        assert validate_stage_output("architecture", data) is None

    def test_breakdown_valid(self):
        data = {"tasks": [{"name": "setup project"}]}
        assert validate_stage_output("breakdown", data) is None

    def test_acceptance_valid(self):
        data = {"criteria": ["user can log in"]}
        assert validate_stage_output("acceptance", data) is None

    def test_markdown_no_schema(self):
        # Markdown stage has no JSON schema
        assert validate_stage_output("markdown", {}) is None

    def test_unknown_stage_no_schema(self):
        assert validate_stage_output("nonexistent", {"a": 1}) is None

    def test_classify_wrong_type(self):
        # recommended_skills should be a list, not a string
        data = {"recommended_skills": "flutter-mobile"}
        result = validate_stage_output("classify", data)
        assert result is not None  # should return error string
