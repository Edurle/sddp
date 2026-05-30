from __future__ import annotations

from typing import Optional

import typer

from sdd_cli.client import APIError, get_client
from sdd_cli.output import print_response

app = typer.Typer(help="Invitation management", no_args_is_help=True)


@app.command("pending")
def get_pending() -> None:
    try:
        client = get_client()
        data = client.get("/invitations/pending")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("handle")
def handle_invitation(
    id: int,
    action: str = typer.Option(..., "--action", "-a"),
) -> None:
    try:
        client = get_client()
        data = client.put(f"/invitations/{id}", json={"action": action})
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)
