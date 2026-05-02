from __future__ import annotations

from typing import Optional

import typer

from sdd_cli.client import APIError, get_client
from sdd_cli.output import print_response

app = typer.Typer(help="Project management", no_args_is_help=True)


@app.command()
def list(
    team: int = typer.Option(..., "--team"),
    status: Optional[str] = typer.Option(None, "--status"),
) -> None:
    try:
        client = get_client()
        params: dict = {}
        if status is not None:
            params["status"] = status
        data = client.get(f"/teams/{team}/projects", params=params)
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command()
def get(project_id: int) -> None:
    try:
        client = get_client()
        data = client.get(f"/projects/{project_id}")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command()
def create(
    team: int = typer.Option(..., "--team"),
    name: str = typer.Option(..., "--name"),
    description: Optional[str] = typer.Option(None, "--description"),
    start_date: Optional[str] = typer.Option(None, "--start-date"),
) -> None:
    try:
        client = get_client()
        payload: dict = {"name": name}
        if description is not None:
            payload["description"] = description
        if start_date is not None:
            payload["start_date"] = start_date
        data = client.post(f"/teams/{team}/projects", json=payload)
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command()
def update(
    project_id: int,
    name: Optional[str] = typer.Option(None, "--name"),
    description: Optional[str] = typer.Option(None, "--description"),
    start_date: Optional[str] = typer.Option(None, "--start-date"),
) -> None:
    try:
        client = get_client()
        payload: dict = {}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if start_date is not None:
            payload["start_date"] = start_date
        data = client.put(f"/projects/{project_id}", json=payload)
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command()
def archive(project_id: int) -> None:
    try:
        client = get_client()
        data = client.put(f"/projects/{project_id}/archive")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command()
def delete(project_id: int) -> None:
    try:
        client = get_client()
        data = client.delete(f"/projects/{project_id}")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command(name="test-stats")
def test_stats(project_id: int) -> None:
    try:
        client = get_client()
        data = client.get(f"/projects/{project_id}/test-statistics")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)
