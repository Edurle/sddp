import typer

from sdd_cli import admin, invitations, iterations, me, projects, requirements, tasks, teams, test_cases, test_executions, users, webhooks

app = typer.Typer(
    name="sdd",
    help="SDD CLI - Agent-driven development tool",
    no_args_is_help=True,
)

app.add_typer(me.app, name="me")
app.add_typer(teams.app, name="teams")
app.add_typer(projects.app, name="projects")
app.add_typer(iterations.app, name="iterations")
app.add_typer(requirements.app, name="requirements")
app.add_typer(tasks.app, name="tasks")
app.add_typer(test_cases.app, name="test-cases")
app.add_typer(test_executions.app, name="test-executions")
app.add_typer(admin.app, name="admin")
app.add_typer(webhooks.app, name="webhooks")
app.add_typer(invitations.app, name="invitations")
app.add_typer(users.app, name="users")


@app.callback()
def main() -> None:
    pass
