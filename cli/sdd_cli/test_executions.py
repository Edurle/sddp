from __future__ import annotations

import json
from typing import Optional

import typer

from sdd_cli.client import APIError, get_client
from sdd_cli.output import print_response

app = typer.Typer(help="Test execution commands", no_args_is_help=True)


@app.command("records")
def get_records(
    round: int = typer.Option(..., "--round", "-r"),
) -> None:
    try:
        client = get_client()
        data = client.get(f"/test-executions/{round}/records")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("batch")
def batch_update(
    round: int = typer.Option(..., "--round", "-r"),
    records: Optional[str] = typer.Option(None, "--records"),
    file: Optional[str] = typer.Option(None, "--file", "-f"),
) -> None:
    try:
        if records:
            parsed = json.loads(records)
        elif file:
            with open(file) as f:
                parsed = json.load(f)
        else:
            typer.echo("Error: Provide --records or --file", err=True)
            raise typer.Exit(code=1)
        client = get_client()
        data = client.put(f"/test-executions/{round}/batch", json={"records": parsed})
        print_response(data)
    except json.JSONDecodeError:
        typer.echo("Error: Invalid JSON", err=True)
        raise typer.Exit(code=1)
    except FileNotFoundError:
        typer.echo(f"Error: File not found: {file}", err=True)
        raise typer.Exit(code=1)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("update-record")
def update_record(
    id: int,
    status: str = typer.Option(..., "--status", "-s"),
    actual_result: Optional[str] = typer.Option(None, "--actual-result"),
    failure_reason: Optional[str] = typer.Option(None, "--failure-reason"),
    log_output: Optional[str] = typer.Option(None, "--log-output"),
    duration_ms: Optional[int] = typer.Option(None, "--duration-ms"),
) -> None:
    try:
        client = get_client()
        body: dict = {"status": status}
        if actual_result:
            body["actual_result"] = actual_result
        if failure_reason:
            body["failure_reason"] = failure_reason
        if log_output:
            body["log_output"] = log_output
        if duration_ms is not None:
            body["duration_ms"] = duration_ms
        data = client.put(f"/test-execution-records/{id}", json=body)
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)
