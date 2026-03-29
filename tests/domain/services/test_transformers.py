import urllib

import pytest
from todo_bene.domain.services.transformer_service import apply_transformers, format_phone, waze_link


@pytest.fixture(autouse=True)
def mock_geonames(mocker):
    """
    Mock Pytest pour simuler les réponses de DuckDB/GeoNames.
    """
    mock_exec = mocker.patch("todo_bene.domain.services.transformer_service.duckdb.execute")

    def side_effect(query, params=None):
        url = params[0] if params else ""
        mock_result = mocker.MagicMock()

        # Logique de correspondance corrigée
        if "Arras" in url:
            mock_result.fetchone.return_value = ("Arras",)
        elif "Lile" in url or "Lille" in url:
            mock_result.fetchone.return_value = ("Lille",)
        elif "La+bas" in url:
            mock_result.fetchone.return_value = ("La Bassée",)
        elif "saingin" in url:
            mock_result.fetchone.return_value = ("Sainghin-en-Weppes",)
        elif "Lens" in url:
            mock_result.fetchone.return_value = ("Lens",)
        elif "thumerie" in url:
            mock_result.fetchone.return_value = ("Thumeries",)
        elif "Saint+Remy" in url:
            mock_result.fetchone.return_value = ("Saint-Remy-en-Bouzemont-Saint-Genest-et-Isson",)
        elif "sainte+catherine" in url:
            # CORRECTION ICI : .return_value au lieu de .value
            mock_result.fetchone.return_value = ("Sainte-Catherine",)
        elif "Beaujeu" in url:
            # AJOUT ICI : Pour supporter le test des noms longs
            mock_result.fetchone.return_value = ("Beaujeu-Saint-Vallier-Pierrejux-et-Quitteur",)
        elif "Ville" in url and "Imaginaire" not in url:
            mock_result.fetchone.return_value = ("Paris",)
        else:
            mock_result.fetchone.return_value = None

        return mock_result

    mock_exec.side_effect = side_effect


def test_transformer_phone_only():
    """Vérifie le formatage du téléphone sur le Todo A."""
    todo_a = "🔥 Appeler Client Dupont 💼 Relance pour gppro 06 06 06 06 06 Ne pas oublier"

    # Test unitaire de la fonction
    result = format_phone(todo_a)
    assert "06.06.06.06.06" in result
    assert "06 06 06 06 06" not in result

def test_transformer_waze_only():
    """Vérifie la création du lien Waze sur une adresse simple."""
    address = "06 06 06 06 06 20 rue Alexandre Ribot, Arras"
    result = waze_link(address)

    assert "https://waze.com/ul?q=20%20rue%20Alexandre%20Ribot%20Arras&navigate=yes" in result

def test_transformer_pipeline_todo_b():
    """
    Test du Todo B : vérifie que les deux transformations
    s'appliquent correctement à la suite.
    """
    todo_b = """Check-up Dentiste 🏥 rdv annuel
    03 03 03 03 03 20 rue Alexandre Ribot, Arras"""

    # On applique les deux transformers via le moteur d'exécution
    pipeline = ["format_phone", "waze_link"]
    final_result = apply_transformers(todo_b, pipeline)

    # Vérification téléphone
    assert "03.03.03.03.03" in final_result
    # Vérification Waze
    assert "https://waze.com/ul?q=20%20rue%20Alexandre%20Ribot%20Arras&navigate=yes" in final_result

def test_transformer_unknown_ignored():
    """Vérifie qu'un nom de transformer inconnu ne fait pas planter le code."""
    text = "Test"
    assert apply_transformers(text, ["inexistant"]) == text

def test_waze_link_should_not_consume_phone_numbers():
    """
    Vérifie que le transformer Waze ne confond pas un numéro de mobile
    avec un numéro de rue.
    """
    input_text = """Relance projets A/B Appeler
    06 12 34 56 78 40 rue Jules Ferry, Ville"""

    # Exécution
    result = waze_link(input_text)

    # Assertions
    # 1. Le numéro de téléphone doit rester intact (non inclus dans le lien)
    assert "06 12 34 56 78" in result
    # 2. Seule l'adresse doit être cliquable
    assert 'q=40%20rue%20Jules%20Ferry%20Paris' in result
    # 3. Le téléphone ne doit pas être dans l'URL Waze
    assert '06%2012' not in result

def test_waze_link_with_suffixes():
    """
    Vérifie que les suffixes (B, Bis, Ter, etc.) sont bien inclus dans le lien Waze.
    """
    # 1. Cas du suffixe collé (40B)
    input_b = "00 00 00 00 00 40B rue Jules Ferry, Lens"
    result_b = waze_link(input_b)
    assert 'q=40B%20rue%20Jules%20Ferry%20Lens' in result_b
    assert '40B rue Jules Ferry, Lens <a' in result_b

    # 2. Cas du Bis avec espace (40 Bis)
    input_bis = "00 00 00 00 00 40 Bis rue Jules Ferry, Lens"
    result_bis = waze_link(input_bis)
    assert 'q=40%20Bis%20rue%20Jules%20Ferry%20Lens' in result_bis
    assert '40 Bis rue Jules Ferry, Lens <a' in result_bis

    # 3. Cas d'une lettre isolée avec espace (40 C)
    input_c = "00 00 00 00 00 40 C rue Jules Ferry, Lens"
    result_c = waze_link(input_c)
    assert 'q=40%20C%20rue%20Jules%20Ferry%20Lens' in result_c
    assert '40 C rue Jules Ferry, Lens <a' in result_c

def test_cascading_transformers_order():
    """
    Vérifie que l'enchaînement des deux transformers fonctionne proprement.
    """
    input_text = """Relance projets A/B Appeler
    06 12 34 56 78 40B rue Jules Ferry, Lens
    Prendre le rdv"""

    # On simule le passage dans les deux (Téléphone puis Waze)
    step1 = format_phone(input_text)
    step2 = waze_link(step1)

    # Le téléphone est formaté avec des points, l'adresse a son lien
    assert "06.12.34.56.78" in step2
    assert 'href="https://waze.com/ul?q=40B%20rue%20Jules%20Ferry%20Lens' in step2



def test_waze_link_transformer_success():
    """Test des cas où la transformation doit réussir."""
    # Cas classique avec faute de frappe et accent
    input_1 = "06 06 06 06 06 5 rue d'en haut, La basée"
    output_1 = waze_link(input_1)
    assert "La Bassée" in output_1
    assert "href=\"https://waze.com/ul?q=5%20rue%20d%27en%20haut%20La%20Bass%C3%A9e" in output_1
    assert "(Waze)" in output_1

    # Cas avec ville composée et tirets
    input_2 = "06 06 06 06 06 5 rue d'en haut, saingin en weppes"
    output_2 = waze_link(input_2)
    assert "Sainghin-en-Weppes" in output_2
    assert "06 06 06 06 06" in output_2

def test_waze_link_no_comma():
    """Vérifie qu'on ne touche à rien s'il n'y a pas de virgule."""
    input_text = "06 06 06 06 06 5 rue d'en haut Lille"
    assert waze_link(input_text) == input_text

def test_waze_link_multi_line():
    """Vérifie le respect de la règle : l'adresse termine la ligne."""
    input_text = """06 06 06 06 06 11 rue d'en bas, sainte catherine les-arras
    tralala"""
    output = waze_link(input_text)

    lines = output.split('\n')
    assert "Sainte-Catherine" in lines[0]
    assert "(Waze)" in lines[0]
    assert "tralala" in lines[1]
    assert "(Waze)" not in lines[1]

def test_waze_link_phone_isolation():
    """Vérifie que le téléphone est exclu de l'URL Waze."""
    input_text = "06.01.02.03.04 5 rue du port, thumerie"
    output = waze_link(input_text)
    # Le téléphone doit être présent dans le texte mais absent de l'URL encodée
    assert "06.01.02.03.04" in output
    output = urllib.parse.unquote(output).split("href=")[1].split(">")[0]
    assert "06.01.02.03.04" not in output

def test_waze_link_city_not_found():
    """Vérifie le comportement si la ville n'existe pas du tout."""
    input_text = "5 rue du port, VilleImaginaireQuiNexistePas"
    assert waze_link(input_text) == input_text

def test_waze_link_long_city_names():
    """
    Test la robustesse face aux noms de communes exceptionnellement longs
    ou avec de multiples tirets/espaces.
    """
    # 1. Saint-Remy-en-Bouzemont-Saint-Genest-et-Isson (Marne)
    input_long = "00 00 00 00 00 14 rue de la mairie, Saint Remy en Bouzemont Saint Genest et Isson"
    output_long = waze_link(input_long)

    # On vérifie que GeoNames a bien renvoyé le nom officiel avec tous les tirets
    assert "Saint-Remy-en-Bouzemont-Saint-Genest-et-Isson" in output_long
    # On vérifie que l'URL Waze contient bien le bloc complet
    assert "q=14%20rue%20de%20la%20mairie%20Saint-Remy-en-Bouzemont-Saint-Genest-et-Isson" in output_long

    # 2. Beaujeu-Saint-Vallier-Pierrejux-et-Quitteur (Haute-Saône)
    input_long_2 = "06 00 00 00 00 Place de l'église, Beaujeu Saint Vallier Pierrejux et Quitteur"
    output_long_2 = waze_link(input_long_2)

    assert "Beaujeu-Saint-Vallier-Pierrejux-et-Quitteur" in output_long_2
    assert "(Waze)" in output_long_2

def test_waze_link_with_extra_text_after_newline():
    """
    Vérifie que le texte après un saut de ligne n'est pas inclus dans la ville
    même si la virgule est sur la ligne du dessus.
    """
    input_multiline = "06 01 02 03 04 5 rue du port, Lille\nCode porte 1234"
    output = waze_link(input_multiline)

    lines = output.split('\n')
    assert "Lille" in lines[0]
    assert "(Waze)" in lines[0]
    assert "Code porte 1234" == lines[1]
    assert "(Waze)" not in lines[1]