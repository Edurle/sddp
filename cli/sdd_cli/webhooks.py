from __future__ import annotations

from typing import Optional

import typer

from sdd_cli.client import APIError, get_client
from sdd_cli.output import print_response

app = typer.Typer(help="Webhook management")


@app.command(name="list")
def list_webhooks(
    team_id: int = typer.Option(..., "--team-id", "-t"),
) -> None:
    try:
        client = get_client()
        data = client.get(f"/teams/{team_id}/webhooks")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command(name="create")
def create_webhook(
    team_id: int = typer.Option(..., "--team-id", "-t"),
    url: str = typer.Option(..., "--url", "-u"),
    events: Optional[str] = typer.Option(None, "--events", "-e"),
    secret: Optional[str] = typer.Option(None, "--secret", "-s"),
) -> None:
    try:
        client = get_client()
        body: dict = {"url": url}
        if events is not None:
            body["events"] = [e.strip() for e in events.split(",")]
        if secret is not None:
            body["secret"] = secret
        data = client.post(f"/teams/{team_id}/webhooks", json=body)
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command(name="update")
def update_webhook(
    team_id: int = typer.Option(..., "--team-id", "-t"),
    webhook_id: int = typer.Option(..., "--webhook-id", "-w"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    events: Optional[str] = typer.Option(None, "--events", "-e"),
    secret: Optional[str] = typer.Option(None, "--secret", "-s"),
    is_active: Optional[bool] = typer.Option(None, "--is-active"),
) -> None:
    try:
        client = get_client()
        body: dict = {}
        if url is not None:
            body["url"] = url
        if events is not None:
            body["events"] = [e.strip() for e in events.split(",")]
        if secret is not None:
            body["secret"] = secret
        if is_active is not None:
            body["is_active"] = is_active
        data = client.put(f"/teams/{team_id}/webhooks/{webhook_id}", json=body)
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command(name="delete")
def delete_webhook(
    team_id: int = typer.Option(..., "--team-id", "-t"),
    webhook_id: int = typer.Option(..., "--webhook-id", "-w"),
) -> None:
    try:
        client = get_client()
        data = client.delete(f"/teams/{team_id}/webhooks/{webhook_id}")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command(name="deliveries")
def list_deliveries(
    team_id: int = typer.Option(..., "--team-id", "-t"),
    webhook_id: int = typer.Option(..., "--webhook-id", "-w"),
) -> None:
    try:
        client = get_client()
        data = client.get(f"/teams/{team_id}/webhooks/{webhook_id}/deliveries")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)
