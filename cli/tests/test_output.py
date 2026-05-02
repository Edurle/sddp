import json

from sdd_cli.output import print_response


class TestFormatJson:
    def test_simple_dict(self, capsys):
        print_response({"name": "test", "value": 42}, format="json")
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert parsed == {"name": "test", "value": 42}

    def test_list(self, capsys):
        data = [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]
        print_response(data, format="json")
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert parsed == data

    def test_nested_dict(self, capsys):
        data = {"user": {"name": "test", "email": "test@example.com"}}
        print_response(data, format="json")
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert parsed == data


class TestFormatTable:
    def test_list_table(self, capsys):
        data = [
            {"id": 1, "name": "alice"},
            {"id": 2, "name": "bob"},
        ]
        print_response(data, format="table")
        out = capsys.readouterr().out
        assert "id" in out
        assert "name" in out
        assert "alice" in out
        assert "bob" in out

    def test_empty_list(self, capsys):
        print_response([], format="table")
        out = capsys.readouterr().out
        assert "(empty)" in out

    def test_dict_table(self, capsys):
        data = {"name": "test", "status": "active"}
        print_response(data, format="table")
        out = capsys.readouterr().out
        assert "name" in out
        assert "test" in out
        assert "status" in out
        assert "active" in out
