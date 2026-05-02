from __future__ import annotations

from typing import Optional

import typer

from sdd_cli.client import APIError, get_client
from sdd_cli.output import print_response

app = typer.Typer(help="Admin commands", no_args_is_help=True)


@app.command("users")
def list_users(
    search: str = typer.Option("", "--search", "-s"),
    page: int = typer.Option(1, "--page"),
    page_size: int = typer.Option(20, "--page-size"),
) -> None:
    try:
        client = get_client()
        params: dict = {"page": page, "page_size": page_size, "search": search}
        data = client.get("/admin/users", params=params)
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("create-user")
def create_user(
    email: str = typer.Option(..., "--email", "-e"),
    nickname: str = typer.Option(..., "--nickname", "-n"),
    password: str = typer.Option(..., "--password", "-p"),
) -> None:
    try:
        client = get_client()
        data = client.post("/admin/users", json={"email": email, "nickname": nickname, "password": password})
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("toggle-user")
def toggle_user(
    id: int,
    active: bool = typer.Option(..., "--active/--no-active"),
) -> None:
    try:
        client = get_client()
        data = client.put(f"/admin/users/{id}/status", json={"is_active": active})
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("create-api-key")
def create_api_key(
    user: int = typer.Option(..., "--user", "-u"),
    name: str = typer.Option(..., "--name", "-n"),
    expires_at: Optional[str] = typer.Option(None, "--expires-at"),
) -> None:
    try:
        client = get_client()
        body: dict = {"user_id": user, "name": name}
        if expires_at:
            body["expires_at"] = expires_at
        data = client.post("/admin/api-keys", json=body)
        print_response(data)
        typer.echo("\nWARNING: Save the raw_key now. It will not be shown again.", err=True)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("list-api-keys")
def list_api_keys(
    user: int = typer.Option(..., "--user", "-u"),
) -> None:
    try:
        client = get_client()
        data = client.get(f"/admin/users/{user}/api-keys")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("revoke-api-key")
def revoke_api_key(id: int) -> None:
    try:
        client = get_client()
        data = client.delete(f"/admin/api-keys/{id}")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)
