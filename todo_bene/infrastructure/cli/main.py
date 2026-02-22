# Copyright (c) 2026 PhilFiftyEight
# Licensed under the MIT License.
import sys
from os import getenv
from typing import Optional, Tuple
from typing import Annotated
from contextlib import contextmanager
import locale
from uuid import UUID
from pathlib import Path
import typer
from rich.text import Text
from rich.table import Table
from rich.style import Style
from rich.console import Console
from rich import box
from rich.prompt import Confirm, Prompt
from rich.panel import Panel
from rich.align import Align
import pendulum

# Imports Internes
from todo_bene.infrastructure.config import (
    get_base_paths,
    load_user_info,
    save_user_config,
)

from todo_bene.domain.entities.todo import Todo
from todo_bene.domain.entities.category import Category

from todo_bene.application.use_cases.user_create import UserCreateUseCase

from todo_bene.application.use_cases.category_create import CategoryCreateUseCase
from todo_bene.application.use_cases.category_list import CategoryListUseCase

from todo_bene.application.use_cases.todo_create import TodoCreateUseCase
from todo_bene.application.use_cases.todo_delete import TodoDeleteUseCase
from todo_bene.application.use_cases.todo_complete import TodoCompleteUseCase
from todo_bene.application.use_cases.todo_find_top_level_by_user import (
    TodoGetAllRootsByUserUseCase,
)
from todo_bene.application.use_cases.todo_repetition import RepetitionTodo
from todo_bene.application.use_cases.todo_update import TodoUpdateUseCase
from todo_bene.application.use_cases.todo_get import TodoGetUseCase

from todo_bene.infrastructure.persistence.duckdb.duckdb_connection_manager import (
    DuckDBConnectionManager,
)
from todo_bene.infrastructure.persistence.duckdb.duckdb_todo_repository import (
    DuckDBTodoRepository,
)
from todo_bene.infrastructure.persistence.duckdb.duckdb_category_repository import (
    DuckDBCategoryRepository,
)

app = typer.Typer()
console = Console()

# get locale
def _get_locale():
    return getenv("LANG")[3:5]

# --- UI TOOLKIT ---
def _pause():
    info="Appuyez sur une touche pour continuer..." # if FR else default > "Press any key to continue..."
    typer.pause(info) if _get_locale() == "FR" else typer.pause()


def show_success(message: str, title: str = "Succès", pause: bool = False):
    """Affiche un message de succès dans un Panel vert."""
    console.print(
        Panel(
            f"[bold green]✔[/bold green] {message}",
            title=f"[bold green]{title}",
            border_style="green",
            expand=False,
        )
    )
    if pause:
        _pause()


def show_error(message: str, title: str = "Erreur", pause: bool = False):
    """Affiche un message d'erreur dans un Panel rouge."""
    console.print(
        Panel(
            f"[bold red]✘[/bold red] {message}",
            title=f"[bold red]{title}",
            border_style="red",
            expand=False,
        )
    )
    if pause:
        _pause()


def ensure_user_setup() -> Tuple[UUID, str]:
    """
    Gère le cycle de vie initial du profil utilisateur.
    """
    user_id, db_path, profile_name = load_user_info()

    if user_id is None:
        console.clear()
        banner = r"""
            [bold cyan]  _____ ___  ___   ___  [/bold cyan]
            [bold cyan] |_   _/ _ \|   \ / _ \ [/bold cyan]
            [bold cyan]   | || (_) | |) | (_) |[/bold cyan]
            [bold white]   |_| \___/|___/ \___/ [/bold white]
            [bold green]  ___  ___ _  _ ___ [/bold green]
            [bold green] | _ )| __| \| | __|[/bold green]
            [bold green] | _ \| _|| .` | _| [/bold green]
            [bold white] |___/|___|_|\_|___|[/bold white]
            [dim]// Configurons votre profil pour commencer.[/dim]
        """

        console.print("\n")
        console.print(
            Align.center(
                Panel(
                    Align.center(banner),
                    border_style="green",
                    box=box.DOUBLE_EDGE,
                    padding=(1, 5),
                )
            )
        )
        console.print("\n")

        email = typer.prompt("Veuillez saisir votre email")
        import getpass

        default_name = getpass.getuser()
        name = typer.prompt("Veuillez saisir votre nom", default=default_name)

        is_dev = typer.confirm(
            "Est-ce un environnement de développement ?", default=False
        )

        if is_dev:
            import os

            final_profile_name = f"{name}_dev"
            os.environ["TODO_BENE_DEV_MODE"] = "1"
            with open(Path(".env"), "w") as f:
                f.write(f"TODO_BENE_PROFILE={final_profile_name}\n")
            db_path_final = str(Path.cwd() / "dev.db")
        else:
            final_profile_name = f"{name}_prod"
            _, data_dir = get_base_paths()
            db_path_final = str(data_dir / ".todo_bene.db")

        with DuckDBTodoRepository(
            DuckDBConnectionManager(db_path_final).get_connection()
        ) as repo:
            new_user = UserCreateUseCase(repo).execute(name, email)

        save_user_config(new_user.uuid, db_path_final, final_profile_name)
        user_id = new_user.uuid
        db_path = db_path_final

    return user_id, db_path


@contextmanager
def get_repository():
    _, db_path, _ = load_user_info()
    if not db_path:
        raise RuntimeError(
            "Configuration introuvable. Veuillez lancer 'tb' pour configurer votre profil."
        )
    manager = DuckDBConnectionManager(db_path)
    repo = DuckDBTodoRepository(manager.get_connection())
    try:
        yield repo
    finally:
        manager.close()
        if hasattr(repo, "close"):
            repo.close()


def get_date_format():
    try:
        lang, _ = locale.getlocale()
        if lang and lang.startswith("fr"):
            return "DD/MM/YYYY HH:mm"
    except TypeError:
        pass
    return "YYYY-MM-DD HH:mm"


def continue_after_invalid(message: str):
    # console.print(f"[red]{message}[/red]")
    show_error(message, title="Invalide", pause=True)
    # if sys.stdin.isatty():
    #     Prompt.ask(
    #         "[dim]Appuyez sur Entrée pour continuer[/dim]",
    #         show_default=False,
    #         default="",
    #     )


def _resolve_parent_uuid(repo, user_id: UUID, parent_input: str) -> Optional[UUID]:
    if not parent_input:
        return None
    try:
        return UUID(parent_input)
    except ValueError:
        pass

    candidates = repo.search_by_title(user_id, parent_input)
    if not candidates:
        console.print(f"[yellow]⚠ Aucun parent trouvé pour '{parent_input}'.[/yellow]")
        if not typer.confirm("Voulez-vous créer la tâche sans parent ?"):
            raise typer.Abort()
        return None

    if len(candidates) == 1:
        console.print(f"[green]Parent sélectionné : {candidates[0].title}[/green]")
        return candidates[0].uuid

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
            return candidates[idx - 1].uuid
    except ValueError:
        console.print("[yellow]Choix invalide, création sans parent.[/yellow]")
    return None


def handle_completion_success(repo, result, user_id: UUID):
    should_exit = False
    if result.get("is_root"):
        todo = repo.get_by_id(result["completed_id"])
        title = todo.title if todo else "la racine"
        answer = Prompt.ask(
            f"\n[bold cyan]' {title} ' est une tâche racine. Voulez-vous la répéter ?[/bold cyan] (o/N)",
            default="n",
        )
        if answer == "o":
            # Si la tâche n'a pas de fréquence, on la demande (déclenche le 2ème prompt du test)
            if not todo.frequency:
                new_freq = Prompt.ask("Fréquence de répétition ?", default="tomorrow")
                if new_freq:
                    todo.frequency = new_freq
                    repo.save(todo)
            
            # Exécution de la répétition
            if todo.frequency:
                try:
                    repetition_use_case = RepetitionTodo(repo)
                    new_todos = repetition_use_case.execute(todo.uuid)
                    
                    if new_todos:
                        # Identification de la nouvelle racine créée
                        new_root = next(t for t in new_todos if t.parent is None)
                        dt_str = pendulum.from_timestamp(new_root.date_start, tz=pendulum.local_timezone()).format("DD/MM/YYYY HH:mm")
                        show_success(f"[green]Nouvelle occurrence planifiée pour le : {dt_str}[/green]", "Todo répété", True)
                except Exception as e:
                    show_error(f"Erreur lors de la répétition : {e}", pause=True)
        should_exit = True
    if result.get("newly_pending_ids"):
        ask_validate_parents_recursive(repo, result["newly_pending_ids"], user_id)
        should_exit = True
    return should_exit


def ask_validate_parents_recursive(repo, newly_pending_ids: list, user_id: UUID):
    for p_id in newly_pending_ids:
        p_todo = repo.get_by_id(p_id)
        if not p_todo:
            continue
        if typer.confirm(f"\n💡 Valider aussi le parent '{p_todo.title}' ?"):
            use_case = TodoCompleteUseCase(repo)
            result = use_case.execute(todo_id=p_id, user_id=user_id)
            if result and result.get("success"):
                # console.print(f"[bold green]✓ Parent '{p_todo.title}' terminé ![/bold green]")
                show_success(
                    f"Parent '{p_todo.title}' terminé !", title="Cascade", pause=True
                )
                handle_completion_success(repo, result, user_id)


def _display_detail_view(todo: Todo, children: list[Todo], repo):
    if sys.stdin.isatty():
        console.clear()
    # RÉCUPÉRATION EMOJI
    cat_emoji = Category(name=todo.category, user_id=todo.user).emoji
    # -------------------------------
    state_label = (
        "[bold green]✅ COMPLÉTÉE[/bold green]"
        if todo.state
        else "[bold red]⏳ À FAIRE[/bold red]"
    )
    prio_mark = "[yellow]🔥 [/yellow]" if todo.priority else ""
    header = f"{prio_mark}[bold white]{todo.title}[/bold white]"
    parent_line = ""
    if todo.parent:
        p_obj = repo.get_by_id(todo.parent)
        p_name = p_obj.title if p_obj else str(todo.parent)[:8]
        parent_line = f"[dim] → {p_name}[/dim]"
    # On construit une ligne composite : [Titre + Parent] ... [Emoji]
    base_text = f"{prio_mark}{todo.title}{parent_line}"
    t_obj = Text(base_text)    
    # Calcul de l'espace (Largeur 70 - 2 bords - longueur texte - 1 emoji - padding)
    # Note : On retire 2 ou 3 selon le padding interne du Panel
    # Il faut ajouter 11 si todo.parent car cell_len : Get the number of cells required to render this text. < les caractères de control (eg [dim]) ne sont pas comptés
    lg_space = 70 - 2 - t_obj.cell_len - 1 - 3 # cas général
    if todo.parent: # on élimine [dim]...[/dim]
        lg_space +=  + 11
    if prio_mark:
        lg_space += 17 # on élimine [yellow]...[/yellow]
    space = " " * max(1, lg_space)
    
    header_with_emoji = f"[bold white]{base_text}[/bold white]{space}{cat_emoji}"

    content = f"{header_with_emoji}\n\n[italic]{todo.description or 'Pas de description'}[/italic]"
    tz = pendulum.local_timezone()
    date_fmt = get_date_format()
    d_start = pendulum.from_timestamp(todo.date_start, tz=tz).format(date_fmt)
    d_due = pendulum.from_timestamp(todo.date_due, tz=tz).format(date_fmt)
    content += f"\n\n[blue]Démarrage: {d_start} - Échéance: {d_due}[/blue]"
    panel = Panel(
        #Align.center(content, vertical="middle"),
        content,
        title=state_label,
        border_style="grey37",
        box=box.ROUNDED,
        width=70,
    )
    console.print("\n")
    console.print(Align.center(panel))
    if children:
        console.print("\n[bold]Sous-tâches :[/bold]")
        for idx, child in enumerate(children, 1):
            c_status = "✅" if child.state else "⏳"
            prio_child = f" 🔥"if child.priority else ""
            console.print(f"  {idx}. {c_status} {child.title}{prio_child}")
    else:
        console.print("\n[dim]Aucune sous-tâche.[/dim]")
    console.print("\n[bold]Actions :[/bold]")
    console.print(
        " [b]m[/b]: Modifier | [b][N°][/b]: Voir sous-tâche | [b]n[/b]: Nouvelle sous-tâche "
    )
    console.print(" [b]t[/b]: Terminer | [b]s[/b]: Supprimer |  [b]r[/b]: Retour ")


def _handle_action(
    choice: str, todo: Todo, children: list[Todo], repo, user_id
) -> tuple[bool, bool]:
    if choice == "r":
        return True, False
    if choice == "t":
        finished = _execute_completion_logic(todo, repo, user_id)
        if finished:
            return True, True
    if choice == "s":
        if typer.confirm(f"Supprimer {todo.title} ?"):
            TodoDeleteUseCase(repo).execute(todo.uuid, user_id)
            # console.print("[green]Supprimé avec succès.[/green]")
            show_success("Supprimé avec succès.", title="Suppression", pause=True)
            return True, False
    if choice == "m":
        console.print("\n[bold blue]📝 Modification du Todo[/bold blue]")
        console.print("[dim]Laissez vide pour conserver la valeur actuelle[/dim]\n")
        new_title = Prompt.ask(
            f"Titre [dim]({todo.title})[/dim]", default=todo.title, show_default=False
        )
        current_desc = todo.description if todo.description else ""
        new_desc = Prompt.ask(
            f"Description [dim]({current_desc or 'aucune'})[/dim]",
            default=current_desc,
            show_default=False,
        )
        current_priority = todo.priority
        new_priority = typer.confirm(
            f"Prioritaire ? ({'Oui' if current_priority else 'Non'})",
            default=current_priority,
        )
        new_cat = Prompt.ask(
            f"Catégorie [dim]({todo.category})[/dim]",
            default=todo.category,
            show_default=False,
        )

        def ask_date(label: str, default_ts: Optional[int] = None) -> int:
            default_str = ""
            if default_ts:
                default_str = pendulum.from_timestamp(
                    default_ts, tz=pendulum.local_timezone()
                ).format("DD/MM/YYYY HH:mm")
            val = Prompt.ask(f"{label}", default=default_str)
            if val == default_str and default_ts is not None:
                return int(default_ts)
            try:
                dt = pendulum.from_format(
                    val, "DD/MM/YYYY HH:mm", tz=pendulum.local_timezone()
                )
                return int(dt.timestamp())
            except ValueError:
                # console.print("[bold red]❌ Format de date invalide.[/bold red] Utilisez : DD/MM/YYYY HH:mm")
                show_error(
                    "Format de date invalide. Utilisez : DD/MM/YYYY HH:mm",
                    title="Date",
                    pause=True,
                )
                raise ValueError()

        try:
            new_start = ask_date("Début", todo.date_start)
            new_due = ask_date("Échéance", todo.date_due)
            updates = {
                "title": new_title,
                "description": new_desc,
                "priority": new_priority,
                "category": new_cat,
                "date_start": new_start,
                "date_due": new_due,
            }
            use_case = TodoUpdateUseCase(repo)
            forbiden = use_case.execute(todo.uuid, **updates)
            if forbiden:
                visible = [
                    f
                    for f in forbiden
                    if f
                    in ["title", "description", "category", "date_start", "date_due"]
                ]
                if visible:
                    console.print(
                        f"[yellow]⚠ Champs non modifiables : {', '.join(visible)}[/yellow]"
                    )
                tech_forbiden = [f for f in forbiden if f in ["user", "uuid"]]
                if tech_forbiden:
                    console.print(
                        f"[dim yellow]Champs non modifiables : {', '.join(tech_forbiden)}[/dim yellow]"
                    )
            # console.print("[bold green]✔ Todo mis à jour avec succès ![/bold green]")
            show_success("Todo mis à jour avec succès !", title="Mise à jour", pause=True)
            return False, False
        except ValueError as e:
            # console.print(f"[bold red]❌ Erreur : {e}[/bold red]")
            show_error(f"Erreur : {e}", title="Modification", pause=True)
            return False, False

    def menu_nouvelle_sous_tache(parent: Todo, repo):
        console.print(
            Panel(
                f"[bold blue]🆕 Nouvelle sous-tâche pour : {parent.title}[/bold blue]"
            )
        )
        console.print(f"[dim]Catégorie héritée : {parent.category}[/dim]")
        title = Prompt.ask("Titre de la sous-tâche")
        description = Prompt.ask("Description (optionnelle)", default="")
        priority = Confirm.ask("Prioritaire ?", default=False)
        fmt = "DD/MM/YYYY HH:mm:ss"
        tz = pendulum.local_timezone()
        def_start = pendulum.from_timestamp(parent.date_start, tz=tz).format(fmt)
        def_due = pendulum.from_timestamp(parent.date_due, tz=tz).format(fmt)
        new_start = Prompt.ask("Date de début", default=def_start)
        new_due = Prompt.ask("Échéance", default=def_due)
        try:
            new_start_ts = pendulum.from_format(new_start, fmt, tz=tz).timestamp()
            new_due_ts = pendulum.from_format(new_due, fmt, tz=tz).timestamp()
        except ValueError:
            # console.print("[bold red]Format de date invalide ![/bold red]")
            show_error("Format de date invalide !", title="Date", pause=True)
            return False
        subtask = Todo(
            title=title,
            description=description,
            user=parent.user,
            category=parent.category,
            priority=priority,
            date_start=new_start_ts,
            date_due=new_due_ts,
            parent=parent.uuid,
        )
        repo.save(subtask)
        # console.print(f"[bold green]✔ Sous-tâche '{title}' créée avec succès ![/bold green]")
        show_success(
            f"Sous-tâche '{title}' créée avec succès !", title="Sous-tâche", pause=True
        )
        return True

    if choice == "n":
        menu_nouvelle_sous_tache(todo, repo)
        return False, False
    return False, False


def _execute_completion_logic(todo: Todo, repo, user_id: UUID) -> bool:
    use_case = TodoCompleteUseCase(repo)
    result = use_case.execute(todo.uuid, user_id)
    if result is None:
        # console.print("[red]Erreur : Tâche introuvable ou accès refusé.[/red]")
        show_error(
            "Erreur : Tâche introuvable ou accès refusé.", title="Accès", pause=True
        )
        return False
    if result.get("success"):
        # console.print(f"[green]✔[/green] Tâche '{todo.title}' terminée !")
        show_success(
            f"Tâche '{todo.title}' terminée !",
            title="Terminé",
            pause=False if result.get("is_root") else True
        )
        handle_completion_success(repo, result, user_id)
        return True
    if result.get("reason") == "active_children":
        active_count = result.get("active_count", 0)
        console.print(
            f"\n[yellow]⚠ Blocage :[/yellow] {active_count} sous-tâche(s) en cours."
        )
        if typer.confirm("Voulez-vous TOUT terminer (enfants inclus) ?"):
            final_result = use_case.execute(todo.uuid, user_id, force=True)
            if final_result and final_result.get("success"):
                # console.print(f"[green]✔[/green] {todo.title} a été terminée !")
                show_success(
                    f"{todo.title} a été terminée !", title="Forçage"
                )
                handle_completion_success(repo, final_result, user_id)
                return True
    return False


def _display_root_list(roots: list[Todo], repo, period: str = "all"):
    # --- CACHE EMOJI
    emoji_cache = {}
    if roots:
        user_id = roots[0].user
        from todo_bene.infrastructure.persistence.duckdb.duckdb_category_repository import DuckDBCategoryRepository
        cat_repo = DuckDBCategoryRepository(repo._conn)
        all_cats = CategoryListUseCase(cat_repo).execute(user_id)
        for name in all_cats:
            emoji_cache[name] = Category(name=name, user_id=user_id).emoji

    tz = pendulum.local_timezone()
    date_fmt = get_date_format()
    table = Table(box=box.SIMPLE, header_style="bold", row_styles=["none", "dim"])
    table.add_column("Idx", justify="right", style="cyan", width=4)
    table.add_column(" ", justify="center", width=2)
    table.add_column("Titre", style="blue")
    table.add_column("Description", style="white")
    table.add_column("Début", style="green")
    table.add_column("Échéance", style="magenta")

    last_group = None

    for idx, todo in enumerate(roots, 1):
        # --- LOGIQUE DE REGROUPEMENT ---
        current_group = None
        dt_due = pendulum.from_timestamp(todo.date_due, tz=tz)
        
        if period == "week":
            current_group = dt_due.format("dddd DD MMMM", locale=_get_locale()).upper()
        elif period == "month":
            current_group = f"SEMAINE {dt_due.week_of_year} ({dt_due.start_of('week').format('DD/MM', locale=_get_locale())})"

        if current_group and current_group != last_group:
            if last_group is not None:
                table.add_row("", "", "", "", "", "")
            
            table.add_row(
                "", "", current_group, "", "", "",
                style=Style(color="yellow", dim=False, bold=True)
            )
            table.add_section()
            last_group = current_group
        # ----------------------------------------------

        prio_mark = "🔥" if todo.priority else ""
        children = repo.find_by_parent(todo.uuid)
        child_signal = (
            f" [bold cyan][{repo.count_all_descendants(todo.uuid)}+][/bold cyan]"
            if len(children) > 0
            else ""
        )
        
        # Titre avec Emoji
        emoji = emoji_cache.get(todo.category, "🔖")
        display_title = f"{emoji}  {todo.title}{child_signal}"

        raw_desc = str(todo.description) if todo.description else ""
        desc = (raw_desc[:20] + "...") if len(raw_desc) > 20 else raw_desc
        d_start = pendulum.from_timestamp(todo.date_start, tz=tz).format(date_fmt)
        d_due = pendulum.from_timestamp(todo.date_due, tz=tz).format(date_fmt)
        
        table.add_row(
            f"{idx:3}",
            prio_mark,
            display_title,
            desc or "[dim italic]Pas de description[/dim italic]",
            d_start,
            d_due,
        )
    console.print(table)

def _handle_list_navigation(choice: str, roots: list[Todo], user_id: UUID) -> bool:
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(roots):
            show_details(roots[idx].uuid, user_id)
            return True
        else:
            continue_after_invalid("Index inconnu.")
    except ValueError:
        continue_after_invalid("Saisie invalide.")
    return False


def _handle_navigation(choice: str, children: list[Todo], user_id: UUID) -> bool:
    if not choice.isdigit():
        return False
    idx = int(choice) - 1
    if 0 <= idx < len(children):
        exit_cascade = show_details(children[idx].uuid, user_id)
        return exit_cascade
    # console.print("[yellow]Index invalide.[/yellow]")
    show_error("Index invalide.", title="Navigation")
    return False


def show_details(todo_uuid: UUID, user_id: UUID) -> bool:
    with get_repository() as repo:
        while True:
            todo, children = TodoGetUseCase(repo).execute(todo_uuid, user_id)
            _display_detail_view(todo, children, repo)
            choice = Prompt.ask("\nVotre choix", default="r").lower().strip()
            if choice.isdigit():
                if _handle_navigation(choice, children, user_id):
                    return True
                continue
            should_break, exit_cascade = _handle_action(
                choice, todo, children, repo, user_id
            )
            if should_break:
                return exit_cascade


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Pour une organisation simplifiée et lutter contre la procrastination"""
    if ctx.invoked_subcommand == "register":
        return
    user_id, db_path = ensure_user_setup()
    ctx.obj = {"user_id": user_id, "db_path": db_path}
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


def complete_category(incomplete: str):
    user_id, _, _ = load_user_info()
    if not user_id:
        return [
            name for name in Category.ALL if name.lower().startswith(incomplete.lower())
        ]
    with get_repository() as repo:
        cat_repo = DuckDBCategoryRepository(repo._conn)
        list_use_case = CategoryListUseCase(cat_repo)
        all_categories = list_use_case.execute(user_id)
    return [
        name for name in all_categories if name.lower().startswith(incomplete.lower())
    ]

def complete_period(incomplete: str):
    periods = ["today", "week", "month", "all"]
    return [p for p in periods if p.startswith(incomplete.lower())]

@app.command(name="add")
def create(
    title: Annotated[str, typer.Argument(help="Titre du todo")],
    category: Annotated[
        Optional[str],
        typer.Option("--category", "-c", autocompletion=complete_category),
    ] = "Quotidien",
    description: Annotated[Optional[str], typer.Option("--description", "-d")] = None,
    priority: Annotated[bool, typer.Option("--priority", "-p")] = False,
    start: Annotated[Optional[str], typer.Option("--start", "-s")] = None,
    due: Annotated[Optional[str], typer.Option("--due", "-e")] = None,
    parent: Annotated[Optional[str], typer.Option("--parent")] = None,
):
    user_id, _ = ensure_user_setup()
    effective_user_id = user_id if user_id else load_user_info()[0]

    with get_repository() as repo:
        cat_repo = DuckDBCategoryRepository(repo._conn)
        list_use_case = CategoryListUseCase(cat_repo)
        all_allowed = list_use_case.execute(effective_user_id)
        temp_cat = Category(name=category or "Quotidien", user_id=effective_user_id)
        formatted_name = temp_cat.name

        if formatted_name not in all_allowed:
            console.print(
                f"[yellow]La catégorie {formatted_name} n'existe pas.[/yellow]"
            )
            if typer.confirm(f"Voulez-vous créer la catégorie {formatted_name} ?"):
                CategoryCreateUseCase(cat_repo).execute(
                    formatted_name, effective_user_id
                )
                # console.print(f"[green]Catégorie {formatted_name} créée.[/green]")
                show_success(f"Catégorie {formatted_name} créée.", title="Catégorie")
                category = formatted_name
            else:
                category = "Quotidien"
        else:
            category = formatted_name

        selected_parent_uuid = _resolve_parent_uuid(repo, effective_user_id, parent)
        use_case = TodoCreateUseCase(repo)
        current_start, current_due = start, due

        while True:
            try:
                todo = use_case.execute(
                    title=title,
                    user=effective_user_id,
                    category=category,
                    description=description or "",
                    priority=priority,
                    date_start=current_start or "",
                    date_due=current_due or "",
                    parent=selected_parent_uuid,
                )
                # Message de succès
                # console.print(f"[bold green]Succès ![/bold green] {msg}")
                msg = f"Succès ! [cyan]{todo.title}[/cyan]"
                if todo.priority:
                    msg += " [yellow](prioritaire)[/yellow]"
                show_success(msg, title="Todo créé")
                break
            except ValueError as e:
                # console.print(f"\n[bold red]🙅‍♂️ Erreur de validation : {e}[/bold red]")
                show_error(f"Erreur de validation : {e}", title="Validation")
                if not sys.stdin.isatty():
                    raise typer.Exit(code=1)
                console.print("[dim]Il y a un problème avec les dates fournies.[/dim]")
                action = Prompt.ask(
                    "Que voulez-vous corriger ? r",
                    choices=["d", "e", "a", "début", "échéance", "annuler"],
                    default="d",
                )
                if action in ["d", "début"]:
                    current_start = Prompt.ask("Nouvelle date de début")
                elif action in ["e", "échéance"]:
                    current_due = Prompt.ask("Nouvelle date d'échéance")
                elif action in ["a", "annuler"]:
                    console.print("[yellow]Bye ![/yellow]")
                    raise typer.Exit(code=0)
                else:
                    console.print("[yellow]Erreur saisie, Bye ![/yellow]")
                    raise typer.Exit(code=0)


@app.command(name="list")
def list_todos(
    category: Annotated[
        Optional[str],
        typer.Option("--category", "-c", autocompletion=complete_category),
    ] = None,
    period: Annotated[
        str, 
        typer.Option("--period", "-p", autocompletion=complete_period, help="today, week, month, all")
    ] = "today",
):
    user_id, _, _ = load_user_info()
    with get_repository() as repo:
        while True:
            use_case = TodoGetAllRootsByUserUseCase(repo)
            roots, postponed_count = use_case.execute(user_id, category=category, period=period)
            if postponed_count > 0:
                console.print(
                    Panel(
                        f"[bold blue]ℹ[/bold blue] {postponed_count} tâche{'s' if postponed_count > 1 else ''} en retard {'ont été reportées' if postponed_count > 1 else 'a été reportée'} à ce soir.",
                        border_style="blue",
                        padding=(0, 1),
                    )
                )

            if not roots:
                msg = f"Aucun Todo trouvé pour la période '{period}'"
                if category:
                    msg += f" pour la catégorie {category}"
                show_error(f"{msg}.", title="Vide")
                return

            if sys.stdin.isatty():
                console.clear()
            # On trie la liste par date d'échéance pour éviter les doublons de bandeaux jaunes
            roots = sorted(roots, key=lambda x: x.date_due)
            # -----------------------------
            _display_root_list(roots, repo, period=period)
            count = len(roots)
            message = (
                f"{count} tâche racine trouvée"
                if count <= 1
                else f"{count} tâches racines trouvées"
            )
            console.print(f"\n[dim] {message} pour la période '{period}'.[/dim]")
            try:
                choice = Prompt.ask(
                    "\nSaisissez l'index (ou 'q' pour quitter)", default="q"
                ).lower()
            except EOFError:
                break
            if choice == "q":
                break
            _handle_list_navigation(choice, roots, user_id)
            if not sys.stdin.isatty():
                break


@app.command(name="list-dev")
def list_dev():
    with get_repository() as repo:
        query = "SELECT * FROM todos"
        todos = [
            repo._row_to_todo(todo) for todo in repo._conn.execute(query).fetchall()
        ]
        if not todos:
            # console.print("[yellow]La base est vide pour cet utilisateur.[/yellow]")
            show_error("La base est vide pour cet utilisateur.", title="Debug")
            return
        table = Table(
            title="Vue Développeur - Tous les Todos", box=box.MINIMAL_DOUBLE_HEAD
        )
        table.add_column("UUID (8)", style="dim", no_wrap=True)
        table.add_column("Structure (Parent)", no_wrap=True)
        table.add_column("Titre", style="bold white")
        table.add_column("État", justify="center")
        table.add_column("Dates (Raw TS)", style="dim")
        for t in todos:
            state = "[green]✅[/green]" if t.state else "[red]❌[/red]"
            short_id = f"{str(t.uuid)[:8]}"
            parent_info = (
                f"[cyan]↳ {str(t.parent)[:8]}[/cyan]"
                if t.parent
                else "[dim]• Racine[/dim]"
            )
            raw_dates = f"S:{t.date_start} | D:{t.date_due}"
            table.add_row(short_id, parent_info, t.title, state, raw_dates)
        console.print(table)
        console.print(f"\n[dim] Total : {len(todos)} items en base.[/dim]")


if __name__ == "__main__":
    app()
