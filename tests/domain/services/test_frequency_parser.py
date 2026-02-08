# import pytest
# from todo_bene.domain.services.frequency_parser import FrequencyParser

# def test_frequency_parser_unsupported_language_fallback():
#     # Scenario: Si la langue dans la config n'est pas supportée, on fallback sur l'anglais
#     parser_unknown = FrequencyParser(language="de") # Allemand non géré encore
    
#     assert parser_unknown.language == "en"

# def test_frequency_parser_uses_config_language():
#     # Scenario: On simule une configuration utilisateur chargée depuis config.json
#     config_fr = {"language": "fr"}
#     config_en = {"language": "en"}
    
#     # Le parser reçoit la langue issue de la config au moment de l'instanciation
#     parser_fr = FrequencyParser(language=config_fr["language"])
#     parser_en = FrequencyParser(language=config_en["language"])
    
#     # "Toutes les 3 semaines" (FR) == "Every 3 weeks" (EN)
#     assert parser_fr.parse("Toutes les 3 semaines") == "today@weekly#3w@∞"
#     assert parser_en.parse("Every 3 weeks") == "today@weekly#3w@∞"

# def test_frequency_parser_sequence_days():
#     # Scenario: L'utilisateur veut une répétition exponentielle (Anki style)
#     parser_fr = FrequencyParser(language="fr")
#     parser_en = FrequencyParser(language="en")
    
#     # On teste le format français et anglais
#     input_fr = "1, 2, 4, 8, 16 jours"
#     input_en = "1, 2, 4, 8, 16 days"
    
#     expected = "today@sequence#1,2,4,8,16d@∞"
    
#     assert parser_fr.parse(input_fr) == expected
#     assert parser_en.parse(input_en) == expected

# def test_frequency_parser_sequence_variable_spaces():
#     # Test de robustesse sur les espaces et virgules
#     parser = FrequencyParser(language="fr")
#     assert parser.parse("1,2,3 jours") == "today@sequence#1,2,3d@∞"
#     assert parser.parse("10, 20 jours") == "today@sequence#10,20d@∞"

# def test_frequency_parser_specific_day():
#     parser = FrequencyParser(language="fr")
#     # Sortie attendue : type_unité_valeur
#     assert parser.parse("Tous les lundis") == "today@weekly#1mon@∞"
#     assert parser.parse("Chaque vendredi") == "today@weekly#1fri@∞"

# def test_frequency_parser_multi_days():
#     parser = FrequencyParser(language="fr")
#     # "Lundi et Jeudi" -> pivot: "mon , thu" -> résultat: "weekly_1mon,thu"
#     assert parser.parse("Lundi et Jeudi") == "today@weekly#1mon,thu@∞"
#     assert parser.parse("Lundi, Mercredi et Vendredi") == "today@weekly#1mon,wed,fri@∞"

import pendulum
import pytest
from todo_bene.domain.services.frequency_parser import FrequencyParser

def test_frequency_parser_unsupported_language_fallback():
    # Fallback sur l'anglais si la langue est inconnue
    parser_unknown = FrequencyParser(language="de")
    assert parser_unknown.language == "en"

def test_frequency_parser_uses_config_language():
    # Vérifie que le parser utilise bien le lexique FR ou EN
    parser_fr = FrequencyParser(language="fr")
    parser_en = FrequencyParser(language="en")
    
    # "Toutes les" implique l'infini dans SimpleIntervalExtractor
    assert parser_fr.parse("Toutes les 3 semaines") == "today@weekly#3w@∞"
    assert parser_en.parse("Every 3 weeks") == "today@weekly#3w@∞"

def test_frequency_parser_simple_interval():
    # Test de SimpleIntervalExtractor
    parser = FrequencyParser(language="fr")
    assert parser.parse("Chaque jour") == "today@daily#1d@∞"
    assert parser.parse("Toutes les 2 semaines") == "today@weekly#2w@∞"

def test_frequency_parser_multi_days():
    # Test de MultiDayExtractor (Demande implicite -> limite 1)
    parser = FrequencyParser(language="fr")
    assert parser.parse("Lundi et Jeudi") == "today@weekly#1mon,thu@1"
    assert parser.parse("Lundi, Mercredi et Vendredi") == "today@weekly#1mon,wed,fri@1"

def test_frequency_parser_specific_day():
    # Test de SpecificDayExtractor (Tous les... -> limite ∞)
    parser = FrequencyParser(language="fr")
    assert parser.parse("Tous les lundis") == "today@weekly#1mon@∞"
    assert parser.parse("Chaque vendredi") == "today@weekly#1fri@∞"

def test_frequency_parser_sequence_days():
    # Test de SequenceExtractor (Demande implicite -> limite 1)
    parser = FrequencyParser(language="fr")
    assert parser.parse("1, 2, 4, 8, 16 jours") == "today@sequence#1,2,4,8,16d@5"

def test_frequency_parser_sequence_variable_spaces():
    # Test de robustesse sur les espaces dans la séquence
    parser = FrequencyParser(language="fr")
    assert parser.parse("1,2,3 jours") == "today@sequence#1,2,3d@3"
    assert parser.parse("10, 20 jours") == "today@sequence#10,20d@2"

def test_frequency_parser_next_occurrences():
    # Cas n°5 : Limite explicite par décompte
    parser = FrequencyParser(language="fr")
    
    # "Les 5 prochains jours" -> daily#1d avec limite 5
    assert parser.parse("Les 5 prochains jours") == "today@sequence#1,2,3,4,5d@5"
    
    # "3 prochaines semaines" -> weekly#1w avec limite 3
    assert parser.parse("3 prochaines semaines") == "today@sequence#1,2,3w@3"

def test_frequency_parser_post_processing_duration():
    parser = FrequencyParser(language="fr")
    # Test avec "pour"
    assert parser.parse("Tous les lundis pour 1 mois") == "today@weekly#1mon@+1m"
    # Test avec "pendant"
    assert parser.parse("Chaque jour pendant 15 jours") == "today@daily#1d@+15d"
#TODO: ajouter "chaque jour les 2 prochaines semaines" 

def test_frequency_parser_post_processing_duration_extended():
    parser = FrequencyParser(language="fr")

    # 1. Combinaison avec MultiDayExtractor (Limite 1 par défaut -> Écrasée par durée)
    # "Lundi et Mercredi pendant 2 semaines"
    assert parser.parse("Lundi et Mercredi pendant 2 semaines") == "today@weekly#1mon,wed@+2w"

    # 2. Combinaison avec SimpleIntervalExtractor (Limite ∞ par défaut -> Écrasée par durée)
    # "Toutes les 2 semaines pour 6 mois"
    assert parser.parse("Toutes les 2 semaines pour 6 mois") == "today@weekly#2w@+6m"

    # 3. Test des différentes unités de temps pour la durée
    assert parser.parse("Chaque jour pour 10 jours") == "today@daily#1d@+10d"
    assert parser.parse("Chaque jour pendant 1 an") == "today@daily#1d@+1y"

    # 4. Test de robustesse (espaces multiples et majuscules)
    # "Tous les lundis    pendant   3   semaines"
    assert parser.parse("Tous les lundis    pendant   3   semaines") == "today@weekly#1mon@+3w"

    # 5. Cas limite : Si "prochains" (Cas 5) et "pendant" (Cas 6) sont présents
    # Ici, le Cas 5 gagne l'extraction (priorité 5), mais le post-traitement 
    # de durée a le "dernier mot" sur la limite.
    # "Les 5 prochains jours pendant 2 semaines" -> +2w l'emporte sur 5.
    #assert parser.parse("Les 5 prochains jours pendant 2 semaines") == "today@daily#1d@+2w"
    assert parser.parse("Les 5 prochains jours pendant 2 semaines") == "today@sequence#1,2,3,4,5d@+2w"

    #6. # "Chaque jour" -> @daily#1d@∞
    # "les 2 prochaines semaines" -> post-traité en @+2w
    assert parser.parse("chaque jour les 2 prochaines semaines") == "today@daily#1d@+2w"

def test_frequency_parser_next_with_duration_fixed():
    parser = FrequencyParser(language="fr")
    
    # "Les 5 prochains jours pendant 2 semaines"
    # L'extracteur donne la séquence, le post-traitement donne la durée.
    assert parser.parse("Les 5 prochains jours pendant 2 semaines") == "today@sequence#1,2,3,4,5d@+2w"
    
    # "Les 3 prochains mois" (sans durée "pendant")
    # L'extracteur donne la séquence, le parser met la limite à "3" (Cas 5)
    assert parser.parse("Les 3 prochains mois") == "today@sequence#1,2,3m@3"

@pytest.fixture
def frozen_time():
    # On fige le temps au lundi 9 février 2026
    date = pendulum.datetime(2026, 2, 9, tz=pendulum.local_timezone())
    with pendulum.travel_to(date, freeze=True):
        yield
        pendulum.travel_back()

def test_frequency_parser_until_end_of_month(frozen_time):
    parser = FrequencyParser(language="fr")
    # 9 fév -> fin de mois = 28 fév
    assert parser.parse("Chaque jour jusqu'à la fin du mois") == "today@daily#1d@2026-02-28"

def test_frequency_parser_until_end_of_semester(frozen_time):
    parser = FrequencyParser(language="fr")
    # 9 fév (1er semestre) -> fin juin
    assert parser.parse("Tous les lundis jusqu'à la fin du semestre") == "today@weekly#1mon@2026-06-30"

def test_frequency_parser_until_fixed_date_human(frozen_time):
    parser = FrequencyParser(language="fr")
    # "15 juin" -> 2026-06-15
    assert parser.parse("Chaque vendredi jusqu'au 15 juin") == "today@weekly#1fri@2026-06-15"

def test_frequency_parser_until_fixed_date_past(frozen_time):
    parser = FrequencyParser(language="fr")
    # On est en février, "jusqu'au 1er janvier" doit viser 2027
    assert parser.parse("Tous les jours jusqu'au 1er janvier") == "today@daily#1d@2027-01-01"