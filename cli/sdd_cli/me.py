from __future__ import annotations

from typing import Optional

import typer

from sdd_cli.client import APIError, get_client
from sdd_cli.output import print_response

app = typer.Typer(help="Current user info")


@app.callback(invoke_without_command=True)
def me_default(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is not None:
        return
    try:
        client = get_client()
        data = client.get("/users/me")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command()
def tasks(
    status: Optional[str] = typer.Option(None, "--status", "-s"),
    offset: Optional[int] = typer.Option(None, "--offset"),
    limit: int = typer.Option(50, "--limit", "-l"),
) -> None:
    try:
        client = get_client()
        params: dict = {"limit": limit}
        if status is not None:
            params["status"] = status
        if offset is not None:
            params["offset"] = offset
        data = client.get("/users/me/tasks", params=params)
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command(name="pending")
def pending_items() -> None:
    try:
        client = get_client()
        data = client.get("/users/me/pending")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command(name="pending-reviews")
def pending_reviews() -> None:
    try:
        client = get_client()
        data = client.get("/users/me/pending-reviews")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command(name="my-work")
def my_work(
    work_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter: reviews, tasks, drafts"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    try:
        client = get_client()
        data = client.get("/users/me/work")

        if json_output:
            print_response(data)
            return

        if work_type == "reviews":
            _print_reviews(data.get("pending_reviews", []))
        elif work_type == "tasks":
            _print_tasks(data.get("assigned_tasks", []))
        elif work_type == "drafts":
            _print_drafts(data.get("draftable_items", []))
        else:
            _print_reviews(data.get("pending_reviews", []))
            _print_tasks(data.get("assigned_tasks", []))
            _print_drafts(data.get("draftable_items", []))
            summary = data.get("summary", {})
            typer.echo(f"\n摘要: {summary.get('reviews_waiting', 0)}个审核 | {summary.get('tasks_in_progress', 0)}个任务 | {summary.get('items_to_draft', 0)}个待起草")

    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


def _print_reviews(items: list) -> None:
    if not items:
        return
    typer.echo(typer.style("\n📋 待审核", fg=typer.colors.CYAN, bold=True))
    for item in items:
        typer.echo(f"  #{item.get('requirement_id')} {item.get('requirement_title', '')} [{item.get('review_type', '')}]")


def _print_tasks(items: list) -> None:
    if not items:
        return
    typer.echo(typer.style("\n🔨 我的任务", fg=typer.colors.CYAN, bold=True))
    for item in items:
        status = item.get("status", "")
        req_title = item.get("requirement_title", "")
        typer.echo(f"  #{item.get('id')} {item.get('title', '')} [{status}]" + (f" → {req_title}" if req_title else ""))


def _print_drafts(items: list) -> None:
    if not items:
        return
    typer.echo(typer.style("\n✏️ 待起草", fg=typer.colors.CYAN, bold=True))
    for item in items:
        typer.echo(f"  #{item.get('id')} {item.get('title', '')} [{item.get('status', '')}] → {item.get('next_action', '')}")


@app.command(name="update-profile")
def update_profile(
    nickname: Optional[str] = typer.Option(None, "--nickname"),
    avatar: Optional[str] = typer.Option(None, "--avatar"),
) -> None:
    try:
        client = get_client()
        body: dict = {}
        if nickname is not None:
            body["nickname"] = nickname
        if avatar is not None:
            body["avatar"] = avatar
        if not body:
            typer.echo("Error: at least one of --nickname or --avatar is required", err=True)
            raise typer.Exit(code=1)
        data = client.put("/users/me", json=body)
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command(name="change-password")
def change_password(
    old_password: str = typer.Option(..., "--old-password", prompt=True),
    new_password: str = typer.Option(..., "--new-password", prompt=True),
) -> None:
    try:
        client = get_client()
        data = client.put("/users/me/password", json={
            "old_password": old_password,
            "new_password": new_password,
        })
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command(name="projects-tree")
def projects_tree() -> None:
    try:
        client = get_client()
        data = client.get("/users/me/projects-tree")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)
