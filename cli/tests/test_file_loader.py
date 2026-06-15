import json


from sdd_cli.file_loader import load_value_from_file


class TestLoadValueFromFile:
    def test_json_file_parsed(self, tmp_path):
        f = tmp_path / "x.json"
        f.write_text(json.dumps(["a", "b"]), encoding="utf-8")
        assert load_value_from_file(str(f)) == ["a", "b"]

    def test_plain_text_kept_as_string(self, tmp_path):
        f = tmp_path / "x.md"
        f.write_text("# 标题\n正文", encoding="utf-8")
        assert load_value_from_file(str(f)) == "# 标题\n正文"

    def test_html_kept_as_string(self, tmp_path):
        f = tmp_path / "x.html"
        f.write_text("<div>hi</div>", encoding="utf-8")
        assert load_value_from_file(str(f)) == "<div>hi</div>"

    def test_invalid_json_falls_back_to_string(self, tmp_path):
        f = tmp_path / "x.txt"
        f.write_text("{not valid json", encoding="utf-8")
        assert load_value_from_file(str(f)) == "{not valid json"

    def test_utf8_content(self, tmp_path):
        f = tmp_path / "x.md"
        f.write_text("中文内容", encoding="utf-8")
        assert load_value_from_file(str(f)) == "中文内容"
