from __future__ import annotations

import json
from typing import Optional

import typer

from sdd_cli.client import APIError, get_client
from sdd_cli.output import print_response

app = typer.Typer(help="Requirement management", no_args_is_help=True)


@app.command("list")
def list_requirements(
    status: Optional[str] = typer.Option(None, "--status", "-s"),
    iteration: Optional[int] = typer.Option(None, "--iteration", "-i"),
    offset: int = typer.Option(0, "--offset"),
    limit: int = typer.Option(50, "--limit", "-l"),
) -> None:
    try:
        client = get_client()
        params: dict = {"offset": offset, "limit": limit}
        if status:
            params["status"] = status
        if iteration is not None:
            params["iteration_id"] = iteration
        data = client.get("/requirements", params=params)
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("get")
def get_requirement(id: int) -> None:
    try:
        client = get_client()
        data = client.get(f"/requirements/{id}")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("create")
def create_requirement(
    title: str = typer.Option(..., "--title", "-t"),
    type: str = typer.Option("feature", "--type"),
    priority: int = typer.Option(0, "--priority", "-p"),
    description: Optional[str] = typer.Option(None, "--description", "-d"),
    type_detail: Optional[str] = typer.Option(None, "--type-detail"),
    iteration: Optional[int] = typer.Option(None, "--iteration", "-i"),
) -> None:
    try:
        client = get_client()
        body: dict = {"title": title, "type": type, "priority": priority}
        body["description"] = description
        body["type_detail"] = json.loads(type_detail) if type_detail else None
        if iteration is not None:
            body["iteration_id"] = iteration
        data = client.post("/requirements", json=body)
        print_response(data)
    except json.JSONDecodeError:
        typer.echo("Error: --type-detail must be valid JSON", err=True)
        raise typer.Exit(code=1)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("update")
def update_requirement(
    id: int,
    title: Optional[str] = typer.Option(None, "--title", "-t"),
    type: Optional[str] = typer.Option(None, "--type"),
    priority: Optional[int] = typer.Option(None, "--priority", "-p"),
    description: Optional[str] = typer.Option(None, "--description", "-d"),
    type_detail: Optional[str] = typer.Option(None, "--type-detail"),
) -> None:
    try:
        client = get_client()
        body: dict = {
            "title": title,
            "req_type": type,
            "priority": priority,
            "description": description,
            "type_detail": json.loads(type_detail) if type_detail else None,
        }
        data = client.put(f"/requirements/{id}", json=body)
        print_response(data)
    except json.JSONDecodeError:
        typer.echo("Error: --type-detail must be valid JSON", err=True)
        raise typer.Exit(code=1)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("delete")
def delete_requirement(id: int) -> None:
    try:
        client = get_client()
        data = client.delete(f"/requirements/{id}")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("patch")
def patch_requirement(
    id: int,
    status: Optional[str] = typer.Option(None, "--status", "-s"),
    title: Optional[str] = typer.Option(None, "--title", "-t"),
    description: Optional[str] = typer.Option(None, "--description", "-d"),
    type_detail: Optional[str] = typer.Option(None, "--type-detail"),
) -> None:
    try:
        client = get_client()
        body: dict = {
            "status": status,
            "title": title,
            "description": description,
            "type_detail": json.loads(type_detail) if type_detail else None,
        }
        data = client.patch(f"/requirements/{id}", json=body)
        print_response(data)
    except json.JSONDecodeError:
        typer.echo("Error: --type-detail must be valid JSON", err=True)
        raise typer.Exit(code=1)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("approve")
def approve_requirement(id: int) -> None:
    try:
        client = get_client()
        data = client.post(f"/requirements/{id}/approve")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("full-context")
def full_context(id: int) -> None:
    try:
        client = get_client()
        data = client.get(f"/requirements/{id}/full-context")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("submit-review")
def submit_review(
    id: int,
    reviewer: int = typer.Option(..., "--reviewer", "-r"),
) -> None:
    try:
        client = get_client()
        data = client.post(f"/requirements/{id}/submit-review", json={"reviewer_id": reviewer})
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("review")
def review_requirement(
    id: int,
    action: str = typer.Option(..., "--action", "-a"),
    comment: Optional[str] = typer.Option(None, "--comment", "-c"),
) -> None:
    try:
        client = get_client()
        data = client.post(f"/requirements/{id}/review", json={"action": action, "comment": comment})
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("test-stats")
def test_statistics(id: int) -> None:
    try:
        client = get_client()
        data = client.get(f"/requirements/{id}/test-statistics")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("spec")
def get_spec(id: int) -> None:
    try:
        client = get_client()
        data = client.get(f"/requirements/{id}/specification")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("save-spec")
def save_spec(
    id: int,
    content: str = typer.Option(..., "--content", "-c"),
) -> None:
    try:
        client = get_client()
        parsed = json.loads(content)
        data = client.put(f"/requirements/{id}/specification", json={"content": parsed})
        print_response(data)
    except json.JSONDecodeError:
        typer.echo("Error: --content must be valid JSON", err=True)
        raise typer.Exit(code=1)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("save-spec-direct")
def save_spec_direct(
    id: int,
    content: str = typer.Option(..., "--content", "-c"),
) -> None:
    try:
        client = get_client()
        parsed = json.loads(content)
        data = client.post(f"/requirements/{id}/spec", json={"content": parsed})
        print_response(data)
    except json.JSONDecodeError:
        typer.echo("Error: --content must be valid JSON", err=True)
        raise typer.Exit(code=1)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("spec-versions")
def spec_versions(id: int) -> None:
    try:
        client = get_client()
        data = client.get(f"/requirements/{id}/specification/versions")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("spec-version")
def spec_version(
    id: int,
    version: int,
) -> None:
    try:
        client = get_client()
        data = client.get(f"/requirements/{id}/specification/versions/{version}")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("submit-spec-review")
def submit_spec_review(
    id: int,
    reviewer: int = typer.Option(..., "--reviewer", "-r"),
) -> None:
    try:
        client = get_client()
        data = client.post(f"/requirements/{id}/submit-spec-review", json={"reviewer_id": reviewer})
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("approve-spec")
def approve_spec(id: int) -> None:
    try:
        client = get_client()
        data = client.post(f"/requirements/{id}/approve-spec")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("submit-tests-review")
def submit_tests_review(
    id: int,
    reviewer: int = typer.Option(..., "--reviewer", "-r"),
) -> None:
    try:
        client = get_client()
        data = client.post(f"/requirements/{id}/submit-tests-review", json={"reviewer_id": reviewer})
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("test-cases")
def list_test_cases(
    id: int,
    case_type: Optional[str] = typer.Option(None, "--case-type"),
    offset: int = typer.Option(0, "--offset"),
    limit: int = typer.Option(50, "--limit", "-l"),
) -> None:
    try:
        client = get_client()
        params: dict = {"offset": offset, "limit": limit}
        if case_type:
            params["case_type"] = case_type
        data = client.get(f"/requirements/{id}/test-cases", params=params)
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("create-test-case")
def create_test_case(
    id: int,
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
        body: dict = {"title": title, "case_type": type}
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
        data = client.post(f"/requirements/{id}/test-cases", json=body)
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("tasks")
def list_tasks(
    id: int,
    status: Optional[str] = typer.Option(None, "--status", "-s"),
    assignee: Optional[int] = typer.Option(None, "--assignee", "-a"),
    offset: int = typer.Option(0, "--offset"),
    limit: int = typer.Option(50, "--limit", "-l"),
) -> None:
    try:
        client = get_client()
        params: dict = {"offset": offset, "limit": limit}
        if status:
            params["status"] = status
        if assignee is not None:
            params["assignee_id"] = assignee
        data = client.get(f"/requirements/{id}/tasks", params=params)
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("create-task")
def create_task(
    id: int,
    title: str = typer.Option(..., "--title", "-t"),
    description: Optional[str] = typer.Option(None, "--description", "-d"),
    assignee: Optional[int] = typer.Option(None, "--assignee", "-a"),
) -> None:
    try:
        client = get_client()
        body: dict = {"title": title}
        if description:
            body["description"] = description
        if assignee is not None:
            body["assignee_id"] = assignee
        data = client.post(f"/requirements/{id}/tasks", json=body)
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)
