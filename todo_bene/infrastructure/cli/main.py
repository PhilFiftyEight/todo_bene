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
from todo_bene.application.use_cases.todo_delete import TodoDeleteUseCase

app = typer.Typer()
console = Console()

# --- UTILITAIRES ---

def get_repository():
    db_path = os.getenv("TODO_BENE_DB_PATH", str(Path.home() / ".todo_bene.db"))
    return DuckDBTodoRepository(db_path)

def get_date_format():
    try:
        lang, _ = locale.getlocale()
        if lang and lang.startswith('fr'):
            return "DD/MM/YYYY HH:mm"
    except Exception:
        pass
    return "YYYY-MM-DD HH:mm"

def continue_after_invalid(message: str):
    console.print(f"[red]{message}[/red]")
    if sys.stdin.isatty():
        Prompt.ask("[dim]Appuyez sur Entrée pour continuer[/dim]", show_default=False, default="")

# --- NAVIGATION ET DÉTAILS ---

def show_details(todo_uuid: UUID):
    repo = get_repository()
    user_id = load_user_config()
    tz = pendulum.local_timezone()
    date_fmt = get_date_format()
    
    while True:
        todo = repo.get_by_id(todo_uuid)
        if not todo:
            break
            
        if sys.stdin.isatty():
            console.clear()
        
        status = "[bold green]COMPLÉTÉ[/bold green]" if todo.state else "[bold yellow]À FAIRE[/bold yellow]"
        prio = " 🔥" if todo.priority else ""
        
        console.print(Panel(
            f"[bold blue]{todo.title}[/bold blue]{prio}\n\n"
            f"[white]{todo.description or 'Aucune description.'}[/white]\n\n"
            f"[dim]Catégorie : {todo.category}[/dim]",
            title=status,
            expand=False
        ))
        
        d_start = pendulum.from_timestamp(todo.date_start, tz=tz).format(date_fmt)
        d_due = pendulum.from_timestamp(todo.date_due, tz=tz).format(date_fmt)
        console.print(f"[green]Début :[/green] {d_start}   [magenta]Échéance :[/magenta] {d_due}")
        
        children = repo.find_by_parent(todo.uuid)
        if children:
            console.print("\n[bold]Sous-tâches :[/bold]")
            child_table = Table(box=box.SIMPLE, header_style="bold", row_styles=["none", "dim"])
            child_table.add_column("Idx", justify="right", style="cyan", width=4)
            child_table.add_column(" ", justify="center", width=2)
            child_table.add_column("Titre", style="blue")
            child_table.add_column("Description", style="white")
            child_table.add_column("Début", style="green")
            child_table.add_column("Echéance", style="magenta")

            for i, child in enumerate(children, 1):
                prio_mark = "🔥" if child.priority else ""
                sub_children = repo.find_by_parent(child.uuid)
                child_signal = f" [bold cyan][{len(sub_children)}+][/bold cyan]" if len(sub_children) > 0 else ""

                raw_desc = str(child.description) if child.description else ""
                desc = (raw_desc[:20] + "...") if len(raw_desc) > 20 else raw_desc

                c_start = pendulum.from_timestamp(child.date_start, tz=tz).format(date_fmt)
                c_due = pendulum.from_timestamp(child.date_due, tz=tz).format(date_fmt)

                child_table.add_row(
                    f"{i:3}", 
                    prio_mark, 
                    f"{child.title}{child_signal}", 
                    desc or "[dim italic]Pas de description[/dim italic]", 
                    c_start, 
                    c_due
                )
            console.print(child_table)
        
        if sys.stdin.isatty():
            console.print("\n[bold]Actions :[/bold]")
            console.print("[white][V]oir sous-tâche (n°) | [T]erminer | [S]upprimer | [R]etour[/white]")
        
        try:
            choice = Prompt.ask("\nQue voulez-vous faire ?", default="r").lower()
        except EOFError:
            break

        if choice == 'r':
            break
        elif choice == 's':
            if typer.confirm(f"Voulez-vous vraiment supprimer '{todo.title}' et tous ses enfants ?"):
                use_case = TodoDeleteUseCase(repo)
                use_case.execute(todo_id=todo.uuid, user_id=user_id)
                console.print("[bold green]Supprimé avec succès.[/bold green]")
                return 
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

        if not sys.stdin.isatty():
            break

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
    parent: Optional[str] = typer.Option(None, "--parent", help="UUID ou partie du titre du parent")
):
    effective_user_id = user_id or load_user_config()
    repo = get_repository()
    use_case = TodoCreateUseCase(repo)
    
    selected_parent_uuid = None

    if parent:
        try:
            selected_parent_uuid = UUID(parent)
        except ValueError:
            candidates = repo.search_by_title(effective_user_id, parent)
            
            if not candidates:
                console.print(f"[yellow]⚠ Aucun parent trouvé pour '{parent}'.[/yellow]")
                if not typer.confirm("Voulez-vous créer la tâche sans parent ?"):
                    raise typer.Abort()
            elif len(candidates) == 1:
                selected_parent_uuid = candidates[0].uuid
                console.print(f"[green]Parent sélectionné : {candidates[0].title}[/green]")
            else:
                console.print("\n[bold cyan]Plusieurs parents possibles trouvés :[/bold cyan]")
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("N°", style="dim")
                table.add_column("Titre")
                table.add_column("Catégorie")

                for i, cand in enumerate(candidates, 1):
                    table.add_row(str(i), cand.title, cand.category)
                
                console.print(table)
                choice = Prompt.ask("Choisissez le numéro du parent", default="0")
                try:
                    idx = int(choice)
                    if 1 <= idx <= len(candidates):
                        selected_parent_uuid = candidates[idx-1].uuid
                except ValueError:
                    console.print("[yellow]Choix invalide, création sans parent.[/yellow]")

    try:
        todo = use_case.execute(
            title=title, user=effective_user_id, category=category, 
            description=description, priority=priority,
            date_start=start, date_due=due, parent=selected_parent_uuid
        )
        msg = f"Todo créé : [cyan]{todo.title}[/cyan]"
        if todo.priority:
            msg += " [yellow](prioritaire)[/yellow]"
        console.print(f"[bold green]Succès ![/bold green] {msg}")
    except ValueError as e:
        console.print(f"[bold red]Erreur : {e}[/bold red]")
        raise typer.Exit(code=1)

@app.command(name="list")
def list_todos():
    user_id = load_user_config()
    repo = get_repository()
    tz = pendulum.local_timezone()
    date_fmt = get_date_format()

    while True:
        roots = repo.find_top_level_by_user(user_id)
        if not roots:
            console.print("[yellow]Aucun Todo trouvé.[/yellow]")
            return

        if sys.stdin.isatty():
            console.clear()
        
        table = Table(box=box.SIMPLE, header_style="bold", row_styles=["none", "dim"])
        table.add_column("Idx", justify="right", style="cyan", width=4)
        table.add_column(" ", justify="center", width=2)
        table.add_column("Titre", style="blue")
        table.add_column("Description", style="white")
        table.add_column("Début", style="green")
        table.add_column("Echéance", style="magenta")

        for idx, todo in enumerate(roots, 1):
            prio_mark = "🔥" if todo.priority else ""
            children = repo.find_by_parent(todo.uuid)
            child_signal = f" [bold cyan][{len(children)}+][/bold cyan]" if len(children) > 0 else ""

            raw_desc = str(todo.description) if todo.description else ""
            desc = (raw_desc[:20] + "...") if len(raw_desc) > 20 else raw_desc

            d_start = pendulum.from_timestamp(todo.date_start, tz=tz).format(date_fmt)
            d_due = pendulum.from_timestamp(todo.date_due, tz=tz).format(date_fmt)

            table.add_row(f"{idx:3}", prio_mark, f"{todo.title}{child_signal}", desc or "[dim italic]Pas de description[/dim italic]", d_start, d_due)

        console.print(table)
        count = len(roots)
        message = f"{count} tâche racine trouvée" if count <= 1 else f"{count} tâches racines trouvées"
        console.print(f"\n[dim] {message}.[/dim]")
        
        # --- FIX POUR LES TESTS ---
        # On lit le choix avant de vérifier isatty()
        try:
            choice = Prompt.ask("\nSaisissez l'index pour voir les détails (ou 'q' pour quitter)", default="q").lower()
        except EOFError:
            break

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
            
        # Si on n'est pas dans un terminal (test), on ne veut pas boucler après une commande
        if not sys.stdin.isatty():
            break

@app.command(name="list-dev")
def list_dev():
    """Affiche une vue technique brute de tous les Todos en base."""
    user_id = load_user_config()
    repo = get_repository()
    
    # On récupère tout sans distinction de hiérarchie
    todos = repo.find_all_by_user(user_id) 
    
    if not todos:
        console.print("[yellow]La base est vide pour cet utilisateur.[/yellow]")
        return

    table = Table(title="Vue Développeur - Tous les Todos", box=box.MINIMAL_DOUBLE_HEAD)
    table.add_column("UUID (Short)", style="dim")
    table.add_column("Titre", style="bold")
    table.add_column("Parent UUID", style="dim")
    table.add_column("État", justify="center")
    table.add_column("Start (TS)", style="green")
    table.add_column("Due (TS)", style="magenta")

    for t in todos:
        state = "✅" if t.state else "❌"
        # On tronque les UUID pour la lisibilité
        short_id = str(t.uuid)[:8] + "..."
        parent_id = str(t.parent)[:8] + "..." if t.parent else "None"
        
        table.add_row(
            short_id,
            t.title,
            parent_id,
            state,
            str(t.date_start),
            str(t.date_due)
        )
    
    console.print(table)
    console.print(f"\n[bold cyan]Total en base : {len(todos)} items.[/bold cyan]")

if __name__ == "__main__":
    app()