from __future__ import annotations

from typing import Optional

import typer

from sdd_cli.client import APIError, get_client
from sdd_cli.output import print_response

app = typer.Typer(help="Iteration management", no_args_is_help=True)


@app.command()
def list(
    project: int = typer.Option(..., "--project"),
    status: Optional[str] = typer.Option(None, "--status"),
) -> None:
    try:
        client = get_client()
        params: dict = {}
        if status is not None:
            params["status"] = status
        data = client.get(f"/projects/{project}/iterations", params=params)
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command()
def get(iteration_id: int) -> None:
    try:
        client = get_client()
        data = client.get(f"/iterations/{iteration_id}")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command()
def create(
    name: str = typer.Option(..., "--name"),
    project: Optional[int] = typer.Option(None, "--project"),
    goal: Optional[str] = typer.Option(None, "--goal"),
    start_date: Optional[str] = typer.Option(None, "--start-date"),
    end_date: Optional[str] = typer.Option(None, "--end-date"),
) -> None:
    try:
        client = get_client()
        payload: dict = {"name": name}
        if goal is not None:
            payload["goal"] = goal
        if start_date is not None:
            payload["start_date"] = start_date
        if end_date is not None:
            payload["end_date"] = end_date
        if project is not None:
            data = client.post(f"/projects/{project}/iterations", json=payload)
        else:
            data = client.post("/iterations", json=payload)
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command()
def update(
    iteration_id: int,
    name: Optional[str] = typer.Option(None, "--name"),
    goal: Optional[str] = typer.Option(None, "--goal"),
    start_date: Optional[str] = typer.Option(None, "--start-date"),
    end_date: Optional[str] = typer.Option(None, "--end-date"),
) -> None:
    try:
        client = get_client()
        payload: dict = {}
        if name is not None:
            payload["name"] = name
        if goal is not None:
            payload["goal"] = goal
        if start_date is not None:
            payload["start_date"] = start_date
        if end_date is not None:
            payload["end_date"] = end_date
        data = client.put(f"/iterations/{iteration_id}", json=payload)
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command()
def start(iteration_id: int) -> None:
    try:
        client = get_client()
        data = client.post(f"/iterations/{iteration_id}/start")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command()
def complete(iteration_id: int) -> None:
    try:
        client = get_client()
        data = client.post(f"/iterations/{iteration_id}/complete")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command()
def kanban(iteration_id: int) -> None:
    try:
        client = get_client()
        data = client.get(f"/iterations/{iteration_id}/kanban")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command()
def statistics(iteration_id: int) -> None:
    try:
        client = get_client()
        data = client.get(f"/iterations/{iteration_id}/statistics")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command(name="test-stats")
def test_stats(iteration_id: int) -> None:
    try:
        client = get_client()
        data = client.get(f"/iterations/{iteration_id}/test-statistics")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)
