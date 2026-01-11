import getpass
import os
from typing import Optional
from uuid import UUID
from pathlib import Path
import typer
import pendulum
from rich.console import Console
from rich.table import Table

from todo_bene.application.use_cases.todo_create import TodoCreateUseCase
from todo_bene.infrastructure.cli.config import load_user_config, save_user_config
from todo_bene.infrastructure.persistence.duckdb_todo_repository import DuckDBTodoRepository

app = typer.Typer(rich_markup_mode="rich")
console = Console()

def get_repository():
    db_path = os.getenv("TODO_BENE_DB_PATH", str(Path.home() / ".todo_bene.db"))
    return DuckDBTodoRepository(db_path)

@app.callback()
def main(ctx: typer.Context):
    if ctx.invoked_subcommand == "register":
        return
    if load_user_config() is None:
        console.print("[red]Erreur : Aucun utilisateur enregistré.[/red]")
        raise typer.Exit(code=1)

@app.command()
def register(
    name: str = typer.Option(default_factory=getpass.getuser),
    email: str = typer.Option(..., prompt="Votre email")
):
    from todo_bene.domain.entities.user import User
    new_user = User(name=name, email=email)
    save_user_config(new_user.uuid)
    console.print(f"[bold green]Bienvenue {name} ![/bold green]")

@app.command()
def create(
    title: str,
    user_id: Optional[UUID] = typer.Option(None),
    category: str = typer.Option("Quotidien"),
    description: str = typer.Option(""),
    priority: bool = typer.Option(False, "--priority", "-p"),
    start: str = typer.Option("", "--start"),
    due: str = typer.Option("", "--due"),
    parent: Optional[UUID] = typer.Option(None, "--parent")
):
    """Créer un nouveau Todo."""
    effective_user_id = user_id or load_user_config()
    use_case = TodoCreateUseCase(get_repository())
    
    todo = use_case.execute(
        title=title, user=effective_user_id, category=category, 
        description=description, priority=priority,
        date_start=start, date_due=due, parent=parent
    )

    msg = f"Todo créé : [cyan]{todo.title}[/cyan]"
    if todo.priority:
        msg += " [yellow](prioritaire)[/yellow]"
    
    console.print(f"[bold green]Succès ![/bold green] {msg}")

# ... (imports identiques)

@app.command()
def list():
    """Lister les Todos avec un formatage de date français."""
    user_id = load_user_config()
    todos = get_repository().get_all_roots_by_user(user_id)

    if not todos:
        console.print("[yellow]Aucun Todo trouvé.[/yellow]")
        return

    table = Table(title="Mes Todos")
    table.add_column("Index", style="dim")
    table.add_column("Titre", style="magenta")
    table.add_column("Début", style="cyan")
    table.add_column("Echéance", style="yellow")
    table.add_column("Priorité", justify="center")

    tz = pendulum.local_timezone()
    for i, t in enumerate(todos, 1):
        # Formatage français : Jour/Mois/Année Heure:Minute
        d_start = pendulum.from_timestamp(t.date_start, tz=tz).format("DD/MM/YYYY HH:mm")
        d_due = pendulum.from_timestamp(t.date_due, tz=tz).format("DD/MM/YYYY HH:mm")
        
        prio = "⭐" if t.priority else ""
        
        table.add_row(
            str(i), 
            t.title, 
            d_start, 
            d_due, 
            prio
        )

    console.print(table)

if __name__ == "__main__":
    app()