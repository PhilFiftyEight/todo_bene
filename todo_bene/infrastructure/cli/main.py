import typer
import os
import sys
import getpass
from typing import Optional
from rich.table import Table
from rich.console import Console
from rich import box
from rich.prompt import Prompt
from rich.panel import Panel
import pendulum
import locale
from uuid import UUID
from pathlib import Path

# Imports Internes
from todo_bene.infrastructure.cli.config import load_user_config, save_user_config
from todo_bene.infrastructure.persistence.duckdb_todo_repository import DuckDBTodoRepository
from todo_bene.application.use_cases.todo_create import TodoCreateUseCase

app = typer.Typer()
console = Console()

# --- UTILITAIRES ---

def get_repository():
    """Initialise le repository avec le chemin de la base de données."""
    db_path = os.getenv("TODO_BENE_DB_PATH", str(Path.home() / ".todo_bene.db"))
    return DuckDBTodoRepository(db_path)

def get_date_format():
    """Détermine le format de date selon la locale du système."""
    try:
        lang, _ = locale.getlocale()
        if lang and lang.startswith('fr'):
            return "DD/MM/YYYY HH:mm"
    except Exception:
        pass
    return "YYYY-MM-DD HH:mm"

def continue_after_invalid(message: str):
    """Affiche une erreur et attend une action utilisateur avant de continuer (interactif uniquement)."""
    console.print(f"[red]{message}[/red]")
    if sys.stdin.isatty():
        Prompt.ask("[dim]Appuyez sur Entrée pour continuer[/dim]", show_default=False, default="")

# --- NAVIGATION ET DÉTAILS ---

def show_details(todo_uuid: UUID):
    """Affiche les détails d'un Todo et permet de naviguer dans ses enfants."""
    repo = get_repository()
    tz = pendulum.local_timezone()
    date_fmt = get_date_format()
    
    while True:
        todo = repo.get_by_id(todo_uuid)
        if not todo:
            break
            
        if sys.stdin.isatty():
            console.clear()
        
        # Statut et Priorité
        status = "[bold green]COMPLÉTÉ[/bold green]" if todo.state else "[bold yellow]À FAIRE[/bold yellow]"
        prio = " 🔥" if todo.priority else ""
        
        console.print(Panel(
            f"[bold blue]{todo.title}[/bold blue]{prio}\n\n"
            f"[white]{todo.description or 'Aucune description.'}[/white]\n\n"
            f"[dim]Catégorie : {todo.category}[/dim]",
            title=status,
            expand=False
        ))
        
        # Dates
        d_start = pendulum.from_timestamp(todo.date_start, tz=tz).format(date_fmt)
        d_due = pendulum.from_timestamp(todo.date_due, tz=tz).format(date_fmt)
        console.print(f"[green]Début :[/green] {d_start}   [magenta]Échéance :[/magenta] {d_due}")
        
        # Enfants
        children = repo.get_children(todo.uuid)
        if children:
            console.print("\n[bold]Sous-tâches :[/bold]")
            child_table = Table(box=box.SIMPLE, show_header=False)
            child_table.add_column("Idx", justify="right", style="cyan", width=4)
            child_table.add_column("Titre")
            for i, child in enumerate(children, 1):
                child_table.add_row(f"{i:3}", child.title)
            console.print(child_table)
        
        # Si on n'est pas dans un terminal (tests), on n'attend pas de saisie
        if not sys.stdin.isatty():
            break

        console.print("\n[bold]Actions :[/bold]")
        console.print("[white][V]oir sous-tâche (n°) | [T]erminer | [S]upprimer | [R]etour[/white]")
        
        choice = Prompt.ask("\nQue voulez-vous faire ?", default="r").lower()
        if choice == 'r':
            break
        elif choice.startswith('v'):
            try:
                idx_str = choice.replace('v', '').strip()
                idx = int(idx_str) - 1
                if 0 <= idx < len(children):
                    show_details(children[idx].uuid)
                else:
                    continue_after_invalid("Index de sous-tâche inconnu.")
            except ValueError:
                continue_after_invalid("Format invalide.")

# --- COMMANDES CLI ---

@app.callback()
def main(ctx: typer.Context):
    """Garde de sécurité : vérifie l'existence d'un profil sauf pour 'register'."""
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
    """Enregistrer un nouvel utilisateur."""
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

@app.command(name="list")
def list_todos():
    """Lister les Todos racines avec navigation interactive."""
    user_id = load_user_config()
    repo = get_repository()
    tz = pendulum.local_timezone()
    date_fmt = get_date_format()
    
    is_interactive = sys.stdin.isatty()

    while True:
        roots = repo.get_all_roots_by_user(user_id)
        if not roots:
            console.print("[yellow]Aucun Todo trouvé.[/yellow]")
            return

        if is_interactive:
            console.clear()
        
        console.print("") 
        table = Table(box=box.SIMPLE, header_style="bold", row_styles=["none", "dim"])
        table.add_column("Idx", justify="right", style="cyan", width=4)
        table.add_column(" ", justify="center", width=2)
        table.add_column("Titre", style="blue")
        table.add_column("Description", style="white")
        table.add_column("Début", style="green")
        table.add_column("Echéance", style="magenta")

        for idx, todo in enumerate(roots, 1):
            prio_mark = "🔥" if todo.priority else ""
            children_count = len(repo.get_children(todo.uuid))
            child_signal = f" [bold cyan][{children_count}+][/bold cyan]" if children_count > 0 else ""
            
            # Troncature description
            desc = todo.description[:20] + "..." if len(todo.description) > 20 else todo.description
            
            d_start = pendulum.from_timestamp(todo.date_start, tz=tz).format(date_fmt)
            d_due = pendulum.from_timestamp(todo.date_due, tz=tz).format(date_fmt)

            table.add_row(
                f"{idx:3}", 
                prio_mark, 
                f"{todo.title}{child_signal}", 
                desc or "[dim italic]Pas de description[/dim italic]", 
                d_start, 
                d_due
            )

        console.print(table)
        count = len(roots)
        message = f"{count} tâche racine trouvée" if count <= 1 else f"{count} tâches racines trouvées"
        console.print(f"\n[dim] {message}.[/dim]")
        
        if not is_interactive:
            break
            
        choice = Prompt.ask("\nSaisissez l'index pour voir les détails (ou 'q' pour quitter)", default="q").lower()
        if choice == 'q':
            break
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(roots):
                show_details(roots[idx].uuid)
            else:
                continue_after_invalid("Index inconnu.")
        except ValueError:
            continue_after_invalid("Saisie invalide.")

if __name__ == "__main__":
    app()