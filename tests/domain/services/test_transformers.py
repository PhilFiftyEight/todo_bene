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