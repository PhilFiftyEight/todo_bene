import re
import urllib.parse
from typing import List, Callable, Dict

# --- Utilitaires de Transformation ---

def format_phone(text: str) -> str:
    """Remplace les espaces dans les numéros de téléphone (ex: 06 00...) par des points."""
    # Regex pour détecter 10 chiffres avec espaces ou tirets
    phone_pattern = r'(\d{2})[ \-](\d{2})[ \-](\d{2})[ \-](\d{2})[ \-](\d{2})'
    return re.sub(phone_pattern, r'\1.\2.\3.\4.\5', text)

def waze_link(text: str) -> str:
    """Transforme les adresses (ex: 5 rue...) en liens cliquables vers Waze."""
    # Regex simplifiée pour détecter un début d'adresse (chiffre + nom de rue)
    # Note : À affiner selon tes habitudes de saisie
    address_pattern = r'(\d+[\w\s\',-]+(?:Ville|Paris|Lyon|Marseille|[A-Z][a-z]+))'
    
    def replace_with_waze(match):
        address = match.group(0).strip()
        encoded_addr = urllib.parse.quote(address)
        return f"{address} (https://waze.com/ul?q={encoded_addr}&navigate=yes)"

    return re.sub(address_pattern, replace_with_waze, text)

# --- Registre des Transformers ---

# Ce dictionnaire permet à la config de lier un nom (string) à une fonction
TRANSFORMERS_REGISTRY: Dict[str, Callable[[str], str]] = {
    "format_phone": format_phone,
    "waze_link": waze_link,
}

# def get_available_transformers() -> list[str]:
#     """Renvoie la liste des noms de transformers enregistrés."""
#     return list(TRANSFORMERS_REGISTRY.keys())

# --- Moteur d'exécution ---

def apply_transformers(text: str, transformer_names: List[str]) -> str:
    """Applique une liste de transformations en cascade sur le texte."""
    result = text
    for name in transformer_names:
        transformer_func = TRANSFORMERS_REGISTRY.get(name)
        if transformer_func:
            result = transformer_func(result)
    return result
