from __future__ import annotations

import typer

from sdd_cli.client import APIError, get_client
from sdd_cli.config import Config
from sdd_cli.output import print_response

app = typer.Typer(help="Authentication commands", no_args_is_help=True)


@app.command()
def login(
    email: str = typer.Option(..., "--email", "-e"),
    password: str = typer.Option(..., "--password", "-p", prompt=True, hide_input=True),
    remember: bool = typer.Option(False, "--remember"),
) -> None:
    try:
        client = get_client()
        data = client.post("/auth/login", json={"email": email, "password": password, "remember": remember})
        if remember and isinstance(data, dict) and data.get("access_token"):
            cfg = Config.load()
            cfg.api_key = data["access_token"]
            cfg.save()
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command()
def register(
    email: str = typer.Option(..., "--email", "-e"),
    password: str = typer.Option(..., "--password", "-p", prompt=True, hide_input=True),
    nickname: str = typer.Option(..., "--nickname", "-n"),
) -> None:
    try:
        client = get_client()
        data = client.post("/auth/register", json={"email": email, "password": password, "nickname": nickname})
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command()
def whoami() -> None:
    try:
        client = get_client()
        data = client.get("/users/me")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command()
def logout() -> None:
    cfg = Config.load()
    cfg.api_key = ""
    cfg.save()
    typer.echo("Logged out. API key removed from config.")
