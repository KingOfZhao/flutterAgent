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

    def test_implementation_valid(self):
        data = {
            "files": [
                {
                    "path": "lib/features/auth/login_page.dart",
                    "purpose": "登录页",
                    "public_api": ["LoginPage"],
                    "skeleton": "class LoginPage extends StatelessWidget { /* TODO */ }",
                }
            ],
            "test_stubs": [{"path": "test/login_page_test.dart", "covers": "lib/.../login_page.dart"}],
        }
        assert validate_stage_output("implementation", data) is None

    def test_implementation_empty_files_still_valid(self):
        # files defaults to [], so {} passes the loose schema
        assert validate_stage_output("implementation", {}) is None

    def test_implementation_file_requires_path(self):
        # each file entry must have a path
        data = {"files": [{"purpose": "missing path"}]}
        result = validate_stage_output("implementation", data)
        assert result is not None

    def test_implementation_files_wrong_type(self):
        # files must be a list of objects, not a string
        result = validate_stage_output("implementation", {"files": "lib/main.dart"})
        assert result is not None

    def test_review_valid(self):
        data = {
            "summary": "骨架就绪,有一处错误处理待补",
            "findings": [
                {
                    "path": "lib/features/auth/login_service.dart",
                    "severity": "major",
                    "category": "error-handling",
                    "issue": "登录失败未建模为返回值",
                    "suggestion": "返回 Result<User> 而非抛裸异常",
                }
            ],
            "checklist": [{"item": "失败路径已建模", "status": "fail"}],
            "blocking": True,
        }
        assert validate_stage_output("review", data) is None

    def test_review_empty_findings_still_valid(self):
        assert validate_stage_output("review", {"findings": [], "blocking": False}) is None

    def test_review_finding_requires_issue(self):
        data = {"findings": [{"path": "lib/x.dart", "severity": "minor"}]}
        result = validate_stage_output("review", data)
        assert result is not None

    def test_review_findings_wrong_type(self):
        result = validate_stage_output("review", {"findings": "looks good"})
        assert result is not None

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
