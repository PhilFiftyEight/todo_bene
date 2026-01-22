# Copyright (c) 2026 PhilFiftyEight
# Licensed under the MIT License.
import os
import sys
import getpass
from typing import Optional
from contextlib import contextmanager
import locale
from uuid import UUID
from pathlib import Path
import typer
from rich.table import Table
from rich.console import Console
from rich import box
from rich.prompt import Prompt
from rich.panel import Panel
from rich.align import Align
import pendulum

# Imports Internes
from todo_bene.application.use_cases.user_create import UserCreateUseCase
from todo_bene.application.use_cases.todo_get import TodoGetUseCase
from todo_bene.domain.entities.todo import Todo
from todo_bene.infrastructure.config import load_user_config, save_user_config
from todo_bene.infrastructure.persistence.duckdb_todo_repository import (
    DuckDBTodoRepository,
)
from todo_bene.application.use_cases.todo_create import TodoCreateUseCase
from todo_bene.application.use_cases.todo_delete import TodoDeleteUseCase
from todo_bene.application.use_cases.todo_complete import TodoCompleteUseCase

app = typer.Typer()
console = Console()

# --- UTILITAIRES ---
def ensure_user_setup() -> UUID:
    """
    Vérifie si un utilisateur est configuré. 
    Sinon, lance un wizard avec un en-tête stylisé 'TODO BENE'.
    """
    console.clear()
    user_id = load_user_config()
    if user_id:
        return user_id

    # --- EN-TÊTE STYLISÉ (Style image) ---
    # On crée un titre imposant
    banner = (
        r"[bold cyan]  _____ ___  ___   ___  [/bold cyan]\n"
        r"[bold cyan] |_   _/ _ \|   \ / _ \ [/bold cyan]\n"
        r"[bold cyan]   | || (_) | |) | (_) |[/bold cyan]\n"
        r"[bold white]   |_| \___/|___/ \___/ [/bold white]\n"
        r"[bold green]  ___  ___ _  _ ___ [/bold green]\n"
        r"[bold green] | _ )| __| \| | __|[/bold green]\n"
        r"[bold green] | _ \| _|| .` | _| [/bold green]\n"
        r"[bold white] |___/|___|_|\_|___|[/bold white]\n"
        r"\n[dim]// Configurons votre profil pour commencer.[/dim]"
    )

    console.print("\n")
    console.print(Align.center(
        Panel(
            Align.center(banner),
            border_style="green",
            box=box.DOUBLE_EDGE,
            padding=(1, 5)
        )
    ))
    console.print("\n")

    email = Prompt.ask("[bold]Quel est votre email ?[/bold]")

    with get_repository() as repo:
        # 1. On vérifie si cet email est déjà connu en BDD
        existing_user = repo.get_user_by_email(email)
        
        if existing_user:
            console.print(f"[yellow]Restauration du profil existant pour : {existing_user.name}[/yellow]")
            save_user_config(existing_user.uuid)
            return existing_user.uuid
        
        # 2. Sinon, on continue la création classique
        name = Prompt.ask("Email inconnu. Quel est votre nom ?", default=getpass.getuser())
        new_user = UserCreateUseCase(repo).execute(name, email)
        
        save_user_config(new_user.uuid)
        console.print(f"\n[bold green]Bienvenue {name} ! Profil créé.[/bold green]")
        return new_user.uuid   

@contextmanager
def get_repository():
    db_path = os.getenv("TODO_BENE_DB_PATH", str(Path.home() / ".todo_bene.db"))
    repo = DuckDBTodoRepository(db_path)
    try:
        yield repo
    finally:
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
    console.print(f"[red]{message}[/red]")
    if sys.stdin.isatty():
        Prompt.ask(
            "[dim]Appuyez sur Entrée pour continuer[/dim]",
            show_default=False,
            default="",
        )


def _resolve_parent_uuid(repo, user_id: UUID, parent_input: str) -> Optional[UUID]:
    """
    Tente de résoudre un UUID de parent à partir d'une saisie (UUID ou titre).
    Gère l'interaction avec l'utilisateur en cas d'ambiguïté.
    """
    if not parent_input:
        return None

    # Tentative de résolution directe par UUID
    try:
        return UUID(parent_input)
    except ValueError:
        pass

    # Recherche par titre
    candidates = repo.search_by_title(user_id, parent_input)

    if not candidates:
        console.print(f"[yellow]⚠ Aucun parent trouvé pour '{parent_input}'.[/yellow]")
        if not typer.confirm("Voulez-vous créer la tâche sans parent ?"):
            raise typer.Abort()
        return None

    if len(candidates) == 1:
        console.print(f"[green]Parent sélectionné : {candidates[0].title}[/green]")
        return candidates[0].uuid

    # Cas multiple : sélection interactive
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
    """Gère les conséquences d'une complétude réussie (répétition et remontée).
    Return True si on doit quitter la vue détail"""
    should_exit = False
    # 1. Si c'est une racine, on propose la répétition
    if result.get("is_root"):
        # On récupère le titre pour la clarté (optionnel mais mieux)
        todo = repo.get_by_id(result["completed_id"])
        title = todo.title if todo else "la racine"
        Prompt.ask(
            f"\n[bold cyan]' {title} ' est une tâche racine. Voulez-vous la répéter ?[/bold cyan] (o/N)",
            default="n",
        )
        should_exit = True  # On vient de finir une racine, on veut sortir

    # 2. Si des parents sont libérés, on propose la validation récursive
    if result.get("newly_pending_ids"):
        ask_validate_parents_recursive(repo, result["newly_pending_ids"], user_id)
        # Si l'utilisateur valide un parent, on considère qu'on veut remonter
        should_exit = True

    return should_exit


def ask_validate_parents_recursive(repo, newly_pending_ids: list, user_id: UUID):
    """Demande récursivement à l'utilisateur s'il veut valider les parents libérés."""
    for p_id in newly_pending_ids:
        p_todo = repo.get_by_id(p_id)
        if not p_todo:
            continue

        if typer.confirm(f"\n💡 Valider aussi le parent '{p_todo.title}' ?"):
            use_case = TodoCompleteUseCase(repo)
            result = use_case.execute(todo_id=p_id, user_id=user_id)

            if result and result.get("success"):
                console.print(
                    f"[bold green]✓ Parent '{p_todo.title}' terminé ![/bold green]"
                )
                # On utilise la fonction de succès ici AUSSI !
                handle_completion_success(repo, result, user_id)


def _display_detail_view(todo: Todo, children: list[Todo], repo):
    """S'occupe uniquement du rendu visuel des détails."""
    if sys.stdin.isatty():
                console.clear()
    # 1. État et Couleur
    state_label = "[bold green]✅ COMPLÉTÉE[/bold green]" if todo.state else "[bold red]⏳ À FAIRE[/bold red]"
    
    # 2. Titre et Priorité
    prio_mark = "[yellow]🔥 [/yellow]" if todo.priority else ""
    header = f"{prio_mark}[bold white]{todo.title}[/bold white]"

    # 3. Information Parent
    parent_line = ""
    if todo.parent:
        p_obj = repo.get_by_id(todo.parent)
        p_name = p_obj.title if p_obj else str(todo.parent)[:8]
        parent_line = f"[dim] → {p_name}[/dim]"

    # 4. Construction du contenu du Panel
    content = f"{header}{parent_line}\n"
    content += f"\n[italic]{todo.description or 'Pas de description'}[/italic]"
    tz = pendulum.local_timezone()
    date_fmt = get_date_format()
    d_start = pendulum.from_timestamp(todo.date_start, tz=tz).format(date_fmt)
    d_due = pendulum.from_timestamp(todo.date_due, tz=tz).format(date_fmt)
    content += f"\n\n[blue]Démarrage: {d_start} - Échéance: {d_due}[/blue]"

    panel = Panel(
        Align.center(content, vertical="middle"),
        title=state_label,
        border_style="grey37", # Couleur grise
        box=box.ROUNDED,
        width=60,
        #expand=False
    )
    console.print("\n")
    console.print(Align.center(panel))

    # Affichage des enfants
    if children:
        console.print("\n[bold]Sous-tâches :[/bold]")
        for idx, child in enumerate(children, 1):
            c_status = "✅" if child.state else "⏳"
            console.print(f"  {idx}. {c_status} {child.title}")
    else:
        console.print("\n[dim]Aucune sous-tâche.[/dim]")

    # Menu d'actions
    console.print("\n[bold]Actions :[/bold]")
    console.print(
        "  [b]t[/b]: Terminer | [b]s[/b]: Supprimer | [b]n[/b]: Nouvelle sous-tâche"
    )
    console.print("  [b]r[/b]: Retour | [b][N°][/b]: Voir sous-tâche")


def _handle_action(
    choice: str, todo: Todo, children: list[Todo], repo, user_id
) -> tuple[bool, bool]:
    """
    Traite l'action textuelle choisie par l'utilisateur.

    Cette fonction découple la prise de décision de la boucle d'affichage.
    Elle utilise un système de signaux via un tuple de booléens.

    Args:
        choice (str): La commande saisie ('t', 'd', 'n', 'r', etc.).
        todo (Todo): L'objet Todo actuellement consulté.
        children (list[Todo]): La liste des sous-tâches chargées.
        repo: Le repository pour les opérations de persistance.

    Returns:
        tuple[bool, bool]: (should_break, exit_cascade)
            - should_break (bool): Si True, la boucle 'while' de la vue actuelle
              doit s'arrêter (on quitte l'écran de cette tâche).
            - exit_cascade (bool): Si True, demande aux parents dans la pile
              récursive de se fermer aussi (utilisé après une complétude réussie).
    """
    # 1. Retour simple
    if choice == "r":
        return True, False

    # 2. Complétude (Le point complexe)
    if choice == "t":
        # On délègue à une mini-fonction dédiée (Étape 2.1)
        finished = _execute_completion_logic(todo, repo, user_id)
        if finished:
            # On casse la boucle ET on demande aux parents de se fermer
            return True, True

    # 3. Suppression
    if choice == "s":
        if typer.confirm(f"Supprimer {todo.title} ?"):
            TodoDeleteUseCase(repo).execute(todo.uuid, user_id)
            console.print("[green]Supprimé avec succès.[/green]")
            return True, False  # On quitte car l'objet n'existe plus

    # 4. Ajout de sous-tâche
    if choice == "n":
        Prompt.ask("Action à venir, merci d'utiliser la ligne de commande!")
        #title = Prompt.ask("Titre de la sous-tâche")
        #TodoCreateUseCase(repo).execute(title, todo.user, parent=todo.uuid)
        # On retourne False, False pour rafraîchir l'affichage et voir le nouvel enfant
        return False, False

    return False, False


def _execute_completion_logic(todo: Todo, repo, user_id: UUID) -> bool:
    """
    Gère la logique de complétude et retourne True si on doit fermer la vue.
    """
    use_case = TodoCompleteUseCase(repo)

    # Exécution du Use Case
    result = use_case.execute(todo.uuid, user_id)

    if result is None:
        console.print("[red]Erreur : Tâche introuvable ou accès refusé.[/red]")
        return False

    # CAS 1 : Succès immédiat
    if result.get("success"):
        console.print(f"[green]✔[/green] Tâche '{todo.title}' terminée !")
        # Gère la répétition ou la remontée aux parents (cascade)
        handle_completion_success(repo, result, user_id)
        return True

    # CAS 2 : Blocage car enfants actifs (success: False)
    if result.get("reason") == "active_children":
        active_count = result.get("active_count", 0)
        console.print(
            f"\n[yellow]⚠ Blocage :[/yellow] {active_count} sous-tâche(s) en cours."
        )

        if typer.confirm("Voulez-vous TOUT terminer (enfants inclus) ?"):
            # Deuxième appel avec force=True
            final_result = use_case.execute(todo.uuid, user_id, force=True)
            if final_result and final_result.get("success"):
                console.print(f"[green]✔[/green] {todo.title} a été terminée !")
                handle_completion_success(repo, final_result, user_id)
                return True

    return False


def _display_root_list(roots: list[Todo], repo):
    """S'occupe uniquement du rendu visuel de la liste principale."""
    tz = pendulum.local_timezone()
    date_fmt = get_date_format()

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
        child_signal = (
            f" [bold cyan][{repo.count_all_descendants(todo.uuid)}+][/bold cyan]"
            if len(children) > 0
            else ""
        )
        raw_desc = str(todo.description) if todo.description else ""
        desc = (raw_desc[:20] + "...") if len(raw_desc) > 20 else raw_desc
        d_start = pendulum.from_timestamp(todo.date_start, tz=tz).format(date_fmt)
        d_due = pendulum.from_timestamp(todo.date_due, tz=tz).format(date_fmt)

        table.add_row(
            f"{idx:3}",
            prio_mark,
            f"{todo.title}{child_signal}",
            desc or "[dim italic]Pas de description[/dim italic]",
            d_start,
            d_due,
        )
    console.print(table)


def _handle_list_navigation(choice: str, roots: list[Todo], user_id: UUID) -> bool:
    """
    Gère la logique de navigation depuis la liste principale.
    Retourne True si une action de navigation a été effectuée.
    """
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


# --- NAVIGATION ET DÉTAILS ---
def _handle_navigation(choice: str, children: list[Todo], user_id: UUID) -> bool:
    """
    Gère l'entrée dans une sous-tâche par son index.

    Args:
        choice (str): La saisie utilisateur (censée être un chiffre).
        children (list[Todo]): La liste des enfants affichés.

    Returns:
        bool: True si on doit propager la fermeture (cascade), False sinon.
    """
    if not choice.isdigit():
        return False

    idx = int(choice) - 1
    if 0 <= idx < len(children):
        # Appel récursif : on descend dans l'enfant
        # Rappel : show_details renvoie True si le parent doit aussi se fermer
        exit_cascade = show_details(children[idx].uuid, user_id)
        return exit_cascade

    console.print("[yellow]Index invalide.[/yellow]")
    return False


def show_details(todo_uuid: UUID, user_id: UUID) -> bool:
    with get_repository() as repo:
        while True:
            # 1. Rafraîchissement des données
            todo, children = TodoGetUseCase(repo).execute(todo_uuid, user_id)
            # children = repo.find_by_parent(todo_uuid)

            # 2. Affichage (Extrait à l'étape 1)
            _display_detail_view(todo, children, repo)

            choice = Prompt.ask("\nVotre choix").lower().strip()

            # 3. Navigation numérique (Extrait à l'étape 4)
            if choice.isdigit():
                if _handle_navigation(choice, children, user_id):
                    return True  # Cascade !
                continue

            # 4. Actions textuelles (Extrait à l'étape 2)
            should_break, exit_cascade = _handle_action(
                choice, todo, children, repo, user_id
            )
            if should_break:
                return exit_cascade


# @app.callback()
# def main(ctx: typer.Context):
#     if ctx.invoked_subcommand == "register":
#         return
#     if load_user_config() is None:
#         console.print("[red]Erreur : Aucun utilisateur enregistré.[/red]")
#         raise typer.Exit(code=1)
@app.callback()
def main(ctx: typer.Context):
    """
    Callback principal : s'assure que l'environnement est prêt,
    sauf pour la commande 'register' qui est manuelle.
    """
    if ctx.invoked_subcommand == "register":
        return
    
    # On lance le wizard automatiquement si besoin
    ensure_user_setup()


@app.command()
def register(
    name: str = typer.Option(default_factory=getpass.getuser),
    email: str = typer.Option(..., prompt="Votre email"),
):
    from todo_bene.domain.entities.user import User

    new_user = User(name=name, email=email)
    save_user_config(new_user.uuid)
    console.print(f"[bold green]Bienvenue {name} ![/bold green]")


@app.command(name="add")
def create(
    title: str,
    user_id: Optional[UUID] = typer.Option(None),
    category: str = typer.Option("Quotidien"),
    description: str = typer.Option(""),
    priority: bool = typer.Option(False, "--priority", "-p"),
    start: str = typer.Option("", "--start"),
    due: str = typer.Option("", "--due"),
    parent: Optional[str] = typer.Option(
        None, "--parent", help="UUID ou partie du titre du parent"
    ),
):
    effective_user_id = user_id or load_user_config()

    with get_repository() as repo:
        # Résolution simplifiée du parent
        selected_parent_uuid = _resolve_parent_uuid(repo, effective_user_id, parent)

        use_case = TodoCreateUseCase(repo)

        try:
            todo = use_case.execute(
                title=title,
                user=effective_user_id,
                category=category,
                description=description,
                priority=priority,
                date_start=start,
                date_due=due,
                parent=selected_parent_uuid,
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
    with get_repository() as repo:
        while True:
            roots = repo.find_top_level_by_user(user_id)
            if not roots:
                console.print("[yellow]Aucun Todo trouvé.[/yellow]")
                return

            if sys.stdin.isatty():
                console.clear()

            # APPEL DE LA NOUVELLE FONCTION DE RENDU
            _display_root_list(roots, repo)

            count = len(roots)
            message = (
                f"{count} tâche racine trouvée"
                if count <= 1
                else f"{count} tâches racines trouvées"
            )
            console.print(f"\n[dim] {message}.[/dim]")

            try:
                choice = Prompt.ask(
                    "\nSaisissez l'index (ou 'q' pour quitter)", default="q"
                ).lower()
            except EOFError:
                break

            if choice == "q":
                break

            # Utilisation de la nouvelle fonction de navigation
            _handle_list_navigation(choice, roots, user_id)

            if not sys.stdin.isatty():
                break


@app.command(name="list-dev")
def list_dev():
    """Vue technique détaillée avec encadrement minimaliste (style list)."""
    user_id = load_user_config()
    # repo = get_repository()
    with get_repository() as repo:
        todos = repo.find_all_by_user(user_id)

        if not todos:
            console.print("[yellow]La base est vide pour cet utilisateur.[/yellow]")
            return

        # On reprend le style box.SIMPLE de la commande 'list'
        # table = Table(box=box.SIMPLE, header_style="bold")
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

            # Identification visuelle du parent
            if t.parent:
                parent_info = f"[cyan]↳ {str(t.parent)[:8]}[/cyan]"
            else:
                parent_info = "[dim]• Racine[/dim]"

            # Timestamps bruts pour le debug
            raw_dates = f"S:{t.date_start} | D:{t.date_due}"

            table.add_row(short_id, parent_info, t.title, state, raw_dates)

        console.print(table)
        console.print(f"\n[dim] Total : {len(todos)} items en base.[/dim]")


if __name__ == "__main__":
    app()
