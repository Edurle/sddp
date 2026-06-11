from __future__ import annotations

from typing import Optional

import typer

from sdd_cli.client import APIError, get_client
from sdd_cli.output import print_response

app = typer.Typer(help="Task management", no_args_is_help=True)


@app.command("get")
def get_task(id: int) -> None:
    try:
        client = get_client()
        data = client.get(f"/tasks/{id}")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("create")
def create_task(
    requirement: int = typer.Option(..., "--requirement", "-r"),
    title: str = typer.Option(..., "--title", "-t"),
    description: Optional[str] = typer.Option(None, "--description", "-d"),
    assignee: Optional[int] = typer.Option(None, "--assignee", "-a"),
) -> None:
    try:
        client = get_client()
        body: dict = {"requirement_id": requirement, "title": title}
        if description:
            body["description"] = description
        if assignee is not None:
            body["assignee_id"] = assignee
        data = client.post("/tasks", json=body)
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("update")
def update_task(
    id: int,
    title: Optional[str] = typer.Option(None, "--title", "-t"),
    description: Optional[str] = typer.Option(None, "--description", "-d"),
    assignee: Optional[int] = typer.Option(None, "--assignee", "-a"),
) -> None:
    try:
        client = get_client()
        body: dict = {}
        if title:
            body["title"] = title
        if description:
            body["description"] = description
        if assignee is not None:
            body["assignee_id"] = assignee
        data = client.put(f"/tasks/{id}", json=body)
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("delete")
def delete_task(id: int) -> None:
    try:
        client = get_client()
        data = client.delete(f"/tasks/{id}")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("patch")
def patch_task(
    id: int,
    status: Optional[str] = typer.Option(None, "--status", "-s"),
    title: Optional[str] = typer.Option(None, "--title", "-t"),
    description: Optional[str] = typer.Option(None, "--description", "-d"),
) -> None:
    try:
        client = get_client()
        body: dict = {"status": status, "title": title, "description": description}
        data = client.patch(f"/tasks/{id}", json=body)
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("start-coding")
def start_coding(id: int) -> None:
    try:
        client = get_client()
        data = client.post(f"/tasks/{id}/start-coding")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("start-testing")
def start_testing(id: int) -> None:
    try:
        client = get_client()
        data = client.post(f"/tasks/{id}/start-testing")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("complete")
def complete_task(id: int) -> None:
    try:
        client = get_client()
        data = client.post(f"/tasks/{id}/complete")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("git-info")
def update_git_info(
    id: int,
    branch: Optional[str] = typer.Option(None, "--branch", "-b"),
    sha: Optional[str] = typer.Option(None, "--sha"),
    pr: Optional[str] = typer.Option(None, "--pr"),
    artifact: Optional[str] = typer.Option(None, "--artifact"),
    message: Optional[str] = typer.Option(None, "--message", "-m"),
    author: Optional[str] = typer.Option(None, "--author"),
    committed_at: Optional[str] = typer.Option(None, "--committed-at"),
) -> None:
    try:
        client = get_client()
        body: dict = {}
        if branch:
            body["git_branch"] = branch
        if sha:
            body["commit_sha"] = sha
        if pr:
            body["pr_url"] = pr
        if artifact:
            body["artifact_url"] = artifact
        if message:
            body["message"] = message
        if author:
            body["author"] = author
        if committed_at:
            body["committed_at"] = committed_at
        data = client.patch(f"/tasks/{id}/git-info", json=body)
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("commits")
def list_task_commits(id: int) -> None:
    try:
        client = get_client()
        data = client.get(f"/tasks/{id}/commits")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("test-executions")
def get_test_executions(id: int) -> None:
    try:
        client = get_client()
        data = client.get(f"/tasks/{id}/test-executions")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("create-test-record")
def create_test_record(
    id: int,
    test_case_id: Optional[int] = typer.Option(None, "--test-case-id"),
    status: Optional[str] = typer.Option("pending", "--status", "-s"),
    actual_result: Optional[str] = typer.Option(None, "--actual-result"),
    failure_reason: Optional[str] = typer.Option(None, "--failure-reason"),
) -> None:
    try:
        client = get_client()
        body: dict = {}
        if test_case_id is not None:
            body["test_case_id"] = test_case_id
        if status:
            body["status"] = status
        if actual_result:
            body["actual_result"] = actual_result
        if failure_reason:
            body["failure_reason"] = failure_reason
        data = client.post(f"/tasks/{id}/test-records", json=body)
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("create-test-round")
def create_test_round(
    id: int,
    test_case_id: Optional[int] = typer.Option(None, "--test-case-id"),
    status: Optional[str] = typer.Option("pending", "--status", "-s"),
    actual_result: Optional[str] = typer.Option(None, "--actual-result"),
    failure_reason: Optional[str] = typer.Option(None, "--failure-reason"),
) -> None:
    try:
        client = get_client()
        body: dict = {}
        if test_case_id is not None:
            body["test_case_id"] = test_case_id
        if status:
            body["status"] = status
        if actual_result:
            body["actual_result"] = actual_result
        if failure_reason:
            body["failure_reason"] = failure_reason
        data = client.post(f"/tasks/{id}/test-rounds", json=body)
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)
