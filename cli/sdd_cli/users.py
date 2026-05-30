from __future__ import annotations

import typer

from sdd_cli.client import APIError, get_client
from sdd_cli.output import print_response

app = typer.Typer(help="User management", no_args_is_help=True)


@app.command("list")
def list_users(
    page_size: int = typer.Option(100, "--page-size"),
) -> None:
    try:
        client = get_client()
        data = client.get("/users", params={"page_size": page_size})
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)
