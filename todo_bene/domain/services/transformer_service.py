from os import getenv
import re
import urllib.parse
from typing import List, Callable, Dict, Optional

from dotenv import load_dotenv
import duckdb

load_dotenv()

# --- Utilitaires de Transformation ---

def format_phone(text: str) -> str:
    """Remplace les espaces dans les numéros de téléphone (ex: 06 00...) par des points."""
    # Regex pour détecter 10 chiffres avec espaces ou tirets
    phone_pattern = r'(\d{2})[ \-](\d{2})[ \-](\d{2})[ \-](\d{2})[ \-](\d{2})'
    return re.sub(phone_pattern, r'\1.\2.\3.\4.\5', text)


def check_city_duckdb(candidate: str) -> Optional[str]:
    """Valide et corrige le nom de la ville via GeoNames.
    Nécessite d'avoir un compte gratuit sur géoname pour obtenir un username
    https://www.geonames.org/login
    """
    if not candidate: # or len(candidate.strip()) < 2:
        return None

    from todo_bene.infrastructure.config import decrypt_value
    geoname_username = decrypt_value(getenv("GEONAME_USERNAME"))

    country = getenv("LANG")[3:5]

    encoded = urllib.parse.quote_plus(candidate.strip())
    for fuzzy_val in [1.0, 0.9, 0.8, 0.7, 0.6]:
        url = f"https://secure.geonames.org/searchJSON?q={encoded}&maxRows=1&country={country}&fuzzy={fuzzy_val}&username={geoname_username}"
        query = "SELECT geonames[1].name FROM read_json(?) WHERE geonames[1].fcl = 'P'"
        try:
            res = duckdb.execute(query, [url]).fetchone()
            if res and res[0]:
                return res[0]
        except Exception:
            continue
    return None

def waze_link(description: str) -> str:
    """
    Analyse et enrichit une description de tâche avec des liens de navigation Waze.

    Cette fonction parcourt chaque ligne de la description et applique une
    transformation si un format d'adresse valide est détecté.

    Formats attendus pour le déclenchement :
    1. Nouveau format (avec Nom/Prénom) : '[Téléphone] [Nom/Prénom], [Adresse], [Ville]'
    2. Ancien format (compatible) : '[Téléphone] [Adresse], [Ville]'

    Règles de transformation :
    1. Séparateurs : 
       - Si 2 virgules sont détectées : [Préfixe], [Adresse], [Ville]
       - Si 1 virgule est détectée : [Préfixe/Téléphone + Rue], [Ville]
    2. Isolation du téléphone : Si un numéro de mobile FR est détecté dans le
       préfixe, il est extrait pour ne pas polluer la recherche Waze.
    3. Correction géographique (GeoNames) : La ville candidate est validée via
       DuckDB. Si une correspondance est trouvée (même avec des fautes d'orthographe
       ou des accents manquants), elle est remplacée par le nom officiel.
    4. Génération HTML : Ajoute un lien cliquable formaté pour l'affichage email.

    Args:
        description (str): Le texte multi-ligne du Todo.

    Returns:
        str: La description transformée avec les liens HTML (Waze).
    """


    def transform_waze_line(line: str) -> str:
        """Transforme la ligne avec détection téléphone, adresse et ville."""
        # 1. Tentative avec le nouveau format strict (2 virgules)
        if line.count(',') == 2:
            parts = line.split(',')
            prefix = parts[0].strip()   # Téléphone + Nom
            address = parts[1].strip()  # Adresse
            city_candidate = parts[2].strip() # Ville
        # 2. Compatibilité avec l'ancien format (1 virgule)
        elif line.count(',') == 1:
            parts = line.rsplit(',', 1)
            prefix = parts[0].strip()   # Téléphone + Rue
            city_candidate = parts[1].strip()
            
            # Isolation du téléphone dans le préfixe
            phone_pattern = r'(?:\d{2}[ \.\-]){4}\d{2}'
            phone_match = re.search(phone_pattern, prefix)
            if not phone_match:
                return line
            phone = phone_match.group(0)
            address = prefix.replace(phone, "").strip() # Adresse = Rue
        else:
            return line
            
        # Validation de la ville
        validated_city = check_city_duckdb(city_candidate)
        if not validated_city:
            return line

        # 4. Construction de l'URL Waze (Adresse + Ville validée)
        full_address_for_waze = f"{address} {validated_city}".strip()
        encoded_addr = urllib.parse.quote(full_address_for_waze)
        waze_url = f'https://waze.com/ul?q={encoded_addr}&navigate=yes'

        # 5. Reconstruction de la ligne d'affichage
        if line.count(',') == 2:
             return f'{prefix}, {address}, {validated_city} <a href="{waze_url}">(Waze)</a>'
        return f'{prefix}, {validated_city} <a href="{waze_url}">(Waze)</a>'

    if not description:
        return description
    lines = description.split('\n')
    return '\n'.join([transform_waze_line(l) for l in lines])


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
