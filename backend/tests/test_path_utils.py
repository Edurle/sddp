import pytest

from app.services.path_utils import (
    PathSyntaxError,
    PathNotFoundError,
    MultipleMatchError,
    set_by_path,
)


class TestParseAndNavigate:
    def test_dot_key(self):
        doc = {"a": {"b": 1}}
        result = set_by_path(doc, "a.b", 99)
        assert result == {"a": {"b": 99}}

    def test_array_index(self):
        doc = {"a": [10, 20, 30]}
        result = set_by_path(doc, "a[1]", 99)
        assert result == {"a": [10, 99, 30]}

    def test_negative_index(self):
        doc = {"a": [10, 20, 30]}
        result = set_by_path(doc, "a[-1]", 99)
        assert result == {"a": [10, 20, 99]}

    def test_nested_array_in_dict(self):
        doc = {"sections": [{"name": "x", "v": 1}, {"name": "y", "v": 2}]}
        result = set_by_path(doc, "sections[0].v", 99)
        assert result["sections"][0]["v"] == 99

    def test_name_match(self):
        doc = {"pages": [{"name": "list", "v": 1}, {"name": "detail", "v": 2}]}
        result = set_by_path(doc, "pages[name=list].v", 99)
        assert result["pages"][0]["v"] == 99

    def test_deep_path(self):
        doc = {"a": {"b": [{"c": {"d": 1}}]}}
        result = set_by_path(doc, "a.b[0].c.d", 99)
        assert result == {"a": {"b": [{"c": {"d": 99}}]}}

    def test_does_not_mutate_input(self):
        doc = {"a": {"b": 1}}
        set_by_path(doc, "a.b", 99)
        assert doc == {"a": {"b": 1}}


class TestErrors:
    def test_syntax_empty_brackets(self):
        doc = {"a": [1, 2]}
        with pytest.raises(PathSyntaxError) as e:
            set_by_path(doc, "a[]", 99)
        assert "[]" in str(e.value)
        assert "缺少下标或键值" in str(e.value)

    def test_syntax_double_dot(self):
        doc = {"a": {"b": 1}}
        with pytest.raises(PathSyntaxError) as e:
            set_by_path(doc, "a..b", 99)
        assert "a..b" in str(e.value)

    def test_missing_key_includes_existing_keys(self):
        doc = {"type_detail": {"severity": "high", "env": "prod"}}
        with pytest.raises(PathNotFoundError) as e:
            set_by_path(doc, "type_detail.reproduce_steps", 99)
        msg = str(e.value)
        assert "reproduce_steps" in msg
        assert "severity" in msg
        assert "env" in msg

    def test_array_out_of_range_includes_length(self):
        doc = {"a": [10, 20, 30]}
        with pytest.raises(PathNotFoundError) as e:
            set_by_path(doc, "a[5]", 99)
        msg = str(e.value)
        assert "a[5]" in msg
        assert "3" in msg

    def test_name_match_zero_includes_existing(self):
        doc = {"pages": [{"name": "list"}, {"name": "detail"}]}
        with pytest.raises(PathNotFoundError) as e:
            set_by_path(doc, "pages[name=nope].v", 99)
        msg = str(e.value)
        assert "nope" in msg
        assert "list" in msg and "detail" in msg

    def test_name_match_multiple(self):
        doc = {"pages": [{"name": "x"}, {"name": "x"}]}
        with pytest.raises(MultipleMatchError) as e:
            set_by_path(doc, "pages[name=x].v", 99)
        msg = str(e.value)
        assert "2" in msg
        assert "pages[0]" in msg

    def test_empty_path(self):
        doc = {"a": 1}
        with pytest.raises(PathSyntaxError):
            set_by_path(doc, "", 99)
