import pytest
from todo_bene.domain.services.transformer_service import apply_transformers, format_phone, waze_link

def test_transformer_phone_only():
    """Vérifie le formatage du téléphone sur le Todo A."""
    todo_a = "🔥 Appeler Client Dupont 💼 Relance pour gppro 06 06 06 06 06 Ne pas oublier"
    
    # Test unitaire de la fonction
    result = format_phone(todo_a)
    assert "06.06.06.06.06" in result
    assert "06 06 06 06 06" not in result

def test_transformer_waze_only():
    """Vérifie la création du lien Waze sur une adresse simple."""
    address = "20 rue Alexandre Ribot Arras"
    result = waze_link(address)
    
    assert "https://waze.com/ul?q=20%20rue%20Alexandre%20Ribot%20Arras&navigate=yes" in result

def test_transformer_pipeline_todo_b():
    """
    Test du Todo B : vérifie que les deux transformations 
    s'appliquent correctement à la suite.
    """
    todo_b = "Check-up Dentiste 🏥 rdv annuel 20 rue Alexandre Ribot Arras 03 03 03 03 03"
    
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
    input_text = """Relance projets A/B Appeler 06 12 34 56 78
    40 rue Jules Ferry Ville"""
    
    # Exécution
    result = waze_link(input_text)
    
    # Assertions
    # 1. Le numéro de téléphone doit rester intact (non inclus dans le lien)
    assert "06 12 34 56 78" in result
    # 2. Seule l'adresse doit être cliquable
    assert 'q=40%20rue%20Jules%20Ferry%20Ville' in result
    # 3. Le téléphone ne doit pas être dans l'URL Waze
    assert '06%2012' not in result

def test_waze_link_with_suffixes():
    """
    Vérifie que les suffixes (B, Bis, Ter, etc.) sont bien inclus dans le lien Waze.
    """
    # 1. Cas du suffixe collé (40B)
    input_b = "RDV au 40B rue Jules Ferry Lens"
    result_b = waze_link(input_b)
    assert 'q=40B%20rue%20Jules%20Ferry%20Lens' in result_b
    assert '40B rue Jules Ferry Lens <a' in result_b

    # 2. Cas du Bis avec espace (40 Bis)
    input_bis = "RDV au 40 Bis rue Jules Ferry Lens"
    result_bis = waze_link(input_bis)
    assert 'q=40%20Bis%20rue%20Jules%20Ferry%20Lens' in result_bis
    assert '40 Bis rue Jules Ferry Lens <a' in result_bis

    # 3. Cas d'une lettre isolée avec espace (40 C)
    input_c = "RDV au 40 C rue Jules Ferry Lens"
    result_c = waze_link(input_c)
    assert 'q=40%20C%20rue%20Jules%20Ferry%20Lens' in result_c
    assert '40 C rue Jules Ferry Lens <a' in result_c

def test_cascading_transformers_order():
    """
    Vérifie que l'enchaînement des deux transformers fonctionne proprement.
    """
    input_text = """
Relance projets A/B Appeler 06 12 34 56 78
40B rue Jules Ferry Lens
Prendre le rdv"""
    
    # On simule le passage dans les deux (Téléphone puis Waze)
    step1 = format_phone(input_text)
    step2 = waze_link(step1)
    print()
    print(step2)
    # Le téléphone est formaté avec des points, l'adresse a son lien
    assert "06.12.34.56.78" in step2
    assert 'href="https://waze.com/ul?q=40B%20rue%20Jules%20Ferry%20Lens' in step2