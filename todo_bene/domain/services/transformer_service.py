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
    """Transforme les adresses en liens cliquables en ignorant les numéros de téléphone.
    Implique de saisir le téléphone avant l'adresse sous la forme xx xx xx xx xx """
    
    
    # On définit ce qu'est un téléphone (10 chiffres séparés par espaces/points/tirets)
    phone_pattern = r'(?:\d{2}[ \.\-]){4}\d{2}'
    
    # On définit l'adresse
    # \b\d{1,5} : Le numéro de rue (jusqu'à 5 chiffres pour le métrique).
    # (?:[ \-]? [a-zA-Z]\b| [Bb]is|[Tt]er|[Qq]uater)? : 
    #    - Soit un espace/tiret suivi d'une SEULE lettre (40B, 40-A).
    #    - Soit les mots Bis, Ter, Quater.
    # [ \w\',-]+ : Le reste de la rue (interdiction du saut de ligne).
    # [A-Z][a-z]+ : La ville.
    address_pattern = r'\b\d{1,5}(?:[ ]?[a-zA-Z]\b|[ ](?:[Bb]is|[Tt]er|[Qq]uater))?[ \w\',-]+[A-Z][a-z]+'
            
    # On cherche soit un téléphone, soit une adresse
    # En mettant le téléphone en premier dans le OR (|), il est "consommé" en priorité
    combined_pattern = f'({phone_pattern})|({address_pattern})'

    def master_replace(match):
        if match.group(1): # C'est un téléphone
            return match.group(1) # On le renvoie tel quel
        
        # Sinon c'est une adresse (groupe 2)
        address = match.group(2).strip()
        encoded_addr = urllib.parse.quote(address)
        return f'{address} <a href="https://waze.com/ul?q={encoded_addr}&navigate=yes">(Waze)</a>'

    return re.sub(combined_pattern, master_replace, text)

# --- Registre des Transformers ---

# Ce dictionnaire permet à la config de lier un nom (string) à une fonction
TRANSFORMERS_REGISTRY: Dict[str, Callable[[str], str]] = {
    "format_phone": format_phone,
    "waze_link": waze_link,
}

# --- Moteur d'exécution ---

def apply_transformers(text: str, transformer_names: List[str]) -> str:
    """Applique une liste de transformations en cascade sur le texte."""
    result = text
    for name in transformer_names:
        transformer_func = TRANSFORMERS_REGISTRY.get(name)
        if transformer_func:
            result = transformer_func(result)
    return result
