from __future__ import annotations

from typing import Optional

import typer

from sdd_cli.client import APIError, get_client
from sdd_cli.file_loader import load_value_from_file
from sdd_cli.output import print_response

app = typer.Typer(help="Test case commands", no_args_is_help=True)


@app.command("create")
def create_test_case(
    requirement: int = typer.Option(..., "--requirement", "-r"),
    title: str = typer.Option(..., "--title", "-t"),
    type: str = typer.Option(..., "--type"),
    precondition: Optional[str] = typer.Option(None, "--precondition"),
    steps: Optional[str] = typer.Option(None, "--steps"),
    expected: Optional[str] = typer.Option(None, "--expected"),
    related_api: Optional[str] = typer.Option(None, "--related-api"),
    related_element: Optional[str] = typer.Option(None, "--related-element"),
) -> None:
    try:
        client = get_client()
        body: dict = {"requirement_id": requirement, "title": title, "case_type": type}
        if precondition:
            body["precondition"] = precondition
        if steps:
            body["steps"] = steps
        if expected:
            body["expected"] = expected
        if related_api:
            body["related_api"] = related_api
        if related_element:
            body["related_element"] = related_element
        data = client.post("/test-cases", json=body)
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("update")
def update_test_case(
    id: int,
    title: Optional[str] = typer.Option(None, "--title", "-t"),
    type: Optional[str] = typer.Option(None, "--type"),
    precondition: Optional[str] = typer.Option(None, "--precondition"),
    steps: Optional[str] = typer.Option(None, "--steps"),
    expected: Optional[str] = typer.Option(None, "--expected"),
    related_api: Optional[str] = typer.Option(None, "--related-api"),
    related_element: Optional[str] = typer.Option(None, "--related-element"),
) -> None:
    try:
        client = get_client()
        body: dict = {}
        if title:
            body["title"] = title
        if type:
            body["case_type"] = type
        if precondition:
            body["precondition"] = precondition
        if steps:
            body["steps"] = steps
        if expected:
            body["expected_result"] = expected
        if related_api:
            body["related_api"] = related_api
        if related_element:
            body["related_element"] = related_element
        data = client.put(f"/test-cases/{id}", json=body)
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


_TC_FIELD_MAP = {
    "title": "title",
    "type": "case_type",
    "precondition": "precondition",
    "steps": "steps",
    "expected": "expected_result",
    "related_api": "related_api",
    "related_element": "related_element",
}


@app.command("set-field")
def set_test_case_field(
    id: int,
    field: str = typer.Argument(...),
    file: str = typer.Option(..., "--file", "-f"),
) -> None:
    try:
        if field not in _TC_FIELD_MAP:
            typer.echo(
                f"Error: 不支持的字段 '{field}'。支持：{list(_TC_FIELD_MAP.keys())}",
                err=True,
            )
            raise typer.Exit(code=1)
        value = load_value_from_file(file)
        client = get_client()
        data = client.put(f"/test-cases/{id}", json={_TC_FIELD_MAP[field]: value})
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("delete")
def delete_test_case(id: int) -> None:
    try:
        client = get_client()
        data = client.delete(f"/test-cases/{id}")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("deprecate")
def deprecate_test_case(id: int) -> None:
    """废弃测试用例（仅所属需求已过审时可用，不可恢复）。"""
    try:
        client = get_client()
        data = client.post(f"/test-cases/{id}/deprecate")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("execution-results")
def execution_results(
    requirement_id: int = typer.Option(..., "--requirement", "-r"),
) -> None:
    try:
        client = get_client()
        data = client.get(f"/test-cases/requirement/{requirement_id}/execution-results")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)
