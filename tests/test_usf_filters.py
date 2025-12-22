"""Tests for Dolibarr Universal Search Filter (USF) syntax builders."""

import pytest
from dolibarr_mcp.tools.projects import _build_usf_like_filter, _build_usf_eq_filter, _sanitize_search


class TestUSFFilterBuilders:
    """Test Universal Search Filter (USF) format compliance.
    
    USF Format: (field:operator:value)
    References:
    - docs/developer/DOLIBARR_USF_SYNTAX.md
    - https://wiki.dolibarr.org/index.php/Universal_Search_Filter_Syntax
    """

    def test_like_filter_basic(self) -> None:
        """Test basic like-filter construction."""
        result = _build_usf_like_filter("t.ref", "PRJ")
        assert result == "(t.ref:like:'%PRJ%')"

    def test_like_filter_with_wildcards(self) -> None:
        """Test that like-filter wraps value in wildcards."""
        result = _build_usf_like_filter("t.title", "Software")
        # Wildcards should be added automatically
        assert result == "(t.title:like:'%Software%')"
        assert "%" in result
        assert ":like:" in result

    def test_like_filter_multiple_fields(self) -> None:
        """Test like-filter with different field names."""
        ref_filter = _build_usf_like_filter("t.ref", "test")
        title_filter = _build_usf_like_filter("t.title", "test")
        
        assert "t.ref" in ref_filter
        assert "t.title" in title_filter
        assert ref_filter != title_filter

    def test_eq_filter_integer(self) -> None:
        """Test equality filter with integer value."""
        result = _build_usf_eq_filter("t.fk_soc", 135)
        assert result == "(t.fk_soc:=:135)"
        assert ":=:" in result
        assert "'" not in result  # No quotes for numbers

    def test_eq_filter_string(self) -> None:
        """Test equality filter with string value."""
        result = _build_usf_eq_filter("t.status", "draft")
        assert result == "(t.status:=:draft)"
        assert ":=:" in result

    def test_eq_filter_correct_field_for_customer(self) -> None:
        """Test that customer filter uses fk_soc (not socid).
        
        This is a common mistake that causes "Bad syntax" errors.
        """
        result = _build_usf_eq_filter("t.fk_soc", 135)
        assert "fk_soc" in result
        # Make sure it's not the old (wrong) format
        assert "socid" not in result
        assert result == "(t.fk_soc:=:135)"

    def test_sanitize_search_removes_special_chars(self) -> None:
        """Test that dangerous special characters are removed."""
        # Sanitize removes SQL-dangerous chars like single quotes
        result = _sanitize_search("test'; DROP TABLE")
        assert "'" not in result
        assert ";" not in result
        # Capital letters are kept (OK for our allowed chars regex)
        assert "test" in result.lower()

    def test_sanitize_search_preserves_allowed_chars(self) -> None:
        """Test that allowed special characters are preserved."""
        result = _sanitize_search("PRJ-2025_Test")
        assert "PRJ" in result
        assert "-" in result
        assert "_" in result

    def test_sanitize_search_max_length(self) -> None:
        """Test that sanitize_search respects max length."""
        long_string = "a" * 100
        result = _sanitize_search(long_string)
        assert len(result) <= 80

    def test_like_filter_with_sanitized_input(self) -> None:
        """Test like-filter with already-sanitized input."""
        query = _sanitize_search("PRJ-2025")
        result = _build_usf_like_filter("t.ref", query)
        assert ":like:" in result
        assert "%PRJ" in result
        assert "%" in result

    def test_filter_format_not_like_sql(self) -> None:
        """Verify filters use USF format, not raw SQL.
        
        Common mistake: (t.socid=135) ❌
        Correct: (t.fk_soc:=:135) ✅
        """
        result = _build_usf_eq_filter("t.fk_soc", 135)
        
        # Should NOT be SQL format
        assert result != "(t.fk_soc=135)"
        assert result != "(fk_soc=135)"
        
        # Should be USF format
        assert result == "(t.fk_soc:=:135)"
        assert ":=:" in result

    def test_multiple_filters_can_be_joined(self) -> None:
        """Test that filters can be combined with 'and'."""
        filter1 = _build_usf_eq_filter("t.fk_soc", 135)
        filter2 = _build_usf_like_filter("t.ref", "PRJ")
        
        combined = f"{filter1} and {filter2}"
        
        # Both filters should be present
        assert "t.fk_soc:=:135" in combined
        assert "t.ref:like:'%PRJ%'" in combined
        # Should use lowercase 'and' (Dolibarr USF requirement)
        assert " and " in combined


class TestUSFErrorCases:
    """Test that old/broken patterns are NOT produced."""

    def test_no_sql_syntax(self) -> None:
        """Ensure we never generate raw SQL '=' operator."""
        result = _build_usf_eq_filter("t.fk_soc", 135)
        # Raw SQL would be (t.fk_soc=135)
        # USF should be (t.fk_soc:=:135)
        # There's exactly one '=' in the `:=:` operator
        assert ":=:" in result
        assert result == "(t.fk_soc:=:135)"

    def test_no_socid_field_for_projects(self) -> None:
        """Ensure projects use fk_soc, not socid.
        
        This was the root cause of the bug:
        "Bad syntax of the search string: (t.socid=135)"
        """
        # This is what was generated before (WRONG)
        wrong = "(t.socid=135)"
        
        # This is what should be generated (CORRECT)
        correct = _build_usf_eq_filter("t.fk_soc", 135)
        
        assert wrong != correct
        assert correct == "(t.fk_soc:=:135)"
        assert "fk_soc" in correct
        assert "socid" not in correct
