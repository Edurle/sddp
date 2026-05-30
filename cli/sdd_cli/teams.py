from __future__ import annotations

import json
from typing import Optional

import typer

from sdd_cli.client import APIError, get_client
from sdd_cli.output import print_response

app = typer.Typer(help="Team management", no_args_is_help=True)


@app.command()
def get(team_id: str) -> None:
    try:
        client = get_client()
        data = client.get(f"/teams/{team_id}")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command()
def create(
    name: str = typer.Option(..., "--name"),
    description: Optional[str] = typer.Option(None, "--description"),
) -> None:
    try:
        client = get_client()
        payload: dict = {"name": name}
        if description is not None:
            payload["description"] = description
        data = client.post("/teams/", json=payload)
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command()
def update(
    team_id: str,
    name: Optional[str] = typer.Option(None, "--name"),
    description: Optional[str] = typer.Option(None, "--description"),
) -> None:
    try:
        client = get_client()
        payload: dict = {}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        data = client.put(f"/teams/{team_id}", json=payload)
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command()
def delete(
    team_id: str,
    confirm: bool = typer.Option(False, "--confirm"),
    confirm_name: Optional[str] = typer.Option(None, "--confirm-name"),
) -> None:
    try:
        if not confirm:
            typer.echo("Error: --confirm is required", err=True)
            raise typer.Exit(code=1)
        client = get_client()
        headers = {}
        if confirm_name:
            headers["X-Confirm-Delete"] = confirm_name
        data = client.delete(f"/teams/{team_id}", headers=headers or None)
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command()
def transfer(
    team_id: str,
    new_owner_id: int = typer.Option(..., "--new-owner-id"),
) -> None:
    try:
        client = get_client()
        data = client.post(f"/teams/{team_id}/transfer", json={"new_owner_id": new_owner_id})
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command()
def members(
    team_id: str,
    role_id: Optional[str] = typer.Option(None, "--role-id"),
) -> None:
    try:
        client = get_client()
        params: dict = {}
        if role_id is not None:
            params["role_id"] = role_id
        data = client.get(f"/teams/{team_id}/members", params=params)
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command()
def invite(
    team_id: str,
    identifier: str = typer.Option(..., "--identifier"),
) -> None:
    try:
        client = get_client()
        data = client.post(f"/teams/{team_id}/invitations", json={"identifier": identifier})
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command()
def remove_member(
    team_id: str,
    user_id: str,
) -> None:
    try:
        client = get_client()
        data = client.delete(f"/teams/{team_id}/members/{user_id}")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command()
def assign_roles(
    team_id: str,
    user_id: str,
    role_ids: str = typer.Option(..., "--role-ids"),
) -> None:
    try:
        client = get_client()
        parsed = [int(x.strip()) for x in role_ids.split(",")]
        data = client.put(
            f"/teams/{team_id}/members/{user_id}/roles",
            json={"role_ids": parsed},
        )
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command()
def roles(team_id: str) -> None:
    try:
        client = get_client()
        data = client.get(f"/teams/{team_id}/roles")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command()
def create_role(
    team_id: str,
    name: Optional[str] = typer.Option(None, "--name"),
    description: Optional[str] = typer.Option(None, "--description"),
    permissions: Optional[str] = typer.Option(None, "--permissions"),
) -> None:
    try:
        client = get_client()
        payload: dict = {}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if permissions is not None:
            payload["permissions"] = [x.strip() for x in permissions.split(",")]
        data = client.post(f"/teams/{team_id}/roles", json=payload)
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command()
def update_role(
    team_id: str,
    role_id: str,
    name: Optional[str] = typer.Option(None, "--name"),
    description: Optional[str] = typer.Option(None, "--description"),
    permissions: Optional[str] = typer.Option(None, "--permissions"),
) -> None:
    try:
        client = get_client()
        payload: dict = {}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if permissions is not None:
            payload["permissions"] = [x.strip() for x in permissions.split(",")]
        data = client.put(f"/teams/{team_id}/roles/{role_id}", json=payload)
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command()
def delete_role(
    team_id: str,
    role_id: str,
) -> None:
    try:
        client = get_client()
        data = client.delete(f"/teams/{team_id}/roles/{role_id}")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command(name="spec-template")
def spec_template(team_id: str) -> None:
    try:
        client = get_client()
        data = client.get(f"/teams/{team_id}/spec-template")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command(name="agent-guide")
def agent_guide(team_id: str) -> None:
    try:
        client = get_client()
        data = client.get(f"/teams/{team_id}/spec-template/agent-guide")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command(name="update-spec-template")
def update_spec_template(
    team_id: str,
    sections: str = typer.Option(..., "--sections"),
) -> None:
    try:
        client = get_client()
        parsed = json.loads(sections)
        data = client.put(f"/teams/{team_id}/spec-template", json={"sections": parsed})
        print_response(data)
    except json.JSONDecodeError:
        typer.echo("Error: Invalid JSON in --sections", err=True)
        raise typer.Exit(code=1)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)
