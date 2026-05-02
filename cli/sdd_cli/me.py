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
