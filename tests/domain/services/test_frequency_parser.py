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

def test_frequency_parser_exception_single_day():
    parser = FrequencyParser(language="fr")
    # "Chaque jour sauf le lundi"
    # Pivot attendu : ! mon
    assert parser.parse("Chaque jour sauf le lundi") == "today@daily#1d@∞!mon"

def test_frequency_parser_exception_multiple_days():
    parser = FrequencyParser(language="fr")
    # "Tous les jours sauf samedi et dimanche"
    # Pivot attendu : ! sat,sun
    assert parser.parse("Tous les jours sauf samedi et dimanche") == "today@daily#1d@∞!sat,sun"

def test_frequency_parser_exception_with_duration():
    parser = FrequencyParser(language="en")
    # "Every day for 2 weeks but not on Wednesday"
    # L'ordre ne doit pas importer
    assert parser.parse("Every day for 2 weeks but not on Wednesday") == "today@daily#1d@+2w!wed"

def test_frequency_parser_exception_before_duration():
    parser = FrequencyParser(language="en")
    # "Every day but not on Wednesday for 2 weeks"
    # L'ordre inversé (Exception avant Durée)
    assert parser.parse("Every day but not on Wednesday for 2 weeks") == "today@daily#1d@+2w!wed"

def test_frequency_parser_exception_before_duration_fr():
    parser = FrequencyParser(language="fr")
    # "Every day but not on Wednesday for 2 weeks"
    # L'ordre inversé (Exception avant Durée)
    assert parser.parse("Tous les jours à l'exception du mercredi pendant 2 semaines") == "today@daily#1d@+2w!wed"

def test_frequency_parser_complex_ordinals():
    parser = FrequencyParser(language="fr")
    # Test avec un nombre complexe
    # "Le cent trente-cinquième jour de l'année"
    assert parser.parse("Le cent trente-cinquième jour de l'année") == "today@yearly#135thday@∞"
    assert parser.parse("Le vingt-septième jour du trimestre") == "today@quarter#27thday@∞"

def test_frequency_parser_workdays_position():
    parser = FrequencyParser(language="fr")
    # "Le deuxième jour ouvré du mois"
    assert parser.parse("Le deuxième jour ouvré du mois") == "today@monthly#2ndworkday@∞"

def test_frequency_parser_last_friday_year():
    parser = FrequencyParser(language="en")
    # "The last friday of the year"
    assert parser.parse("The last friday of the year") == "today@yearly#lastfri@∞"

def test_frequency_parser_shift_weekend():
    parser = FrequencyParser(language="fr")
    # "Le 1er du mois, reporté si week-end"
    # On teste la détection du mot "reporté" ou "si week-end"
    assert parser.parse("Le 1er du mois, reporter si week-end") == "today@monthly#1stday@∞|next_workday"

def test_frequency_parser_shift_business_context():
    parser = FrequencyParser(language="fr")
    # Au lieu de Noël, on prend une date de facturation/paie (le 5 du mois)
    # L'utilisateur demande explicitement le décalage car le système cible ne traite pas les jours non-ouvrables
    assert parser.parse("Le 5 du mois décaler si jour non ouvré") == "today@monthly#5thday@∞|next_workday"

def test_frequency_parser_shift_explicit_instruction():
    parser = FrequencyParser(language="fr")
    # Test d'une position relative avec une instruction de report
    # "Le dernier vendredi du trimestre, si férié décaler"
    assert parser.parse("Le dernier vendredi du trimestre, si férié décaler") == "today@quarter#lastfri@∞|next_workday"

def test_frequency_parser_mixed_units_arbitration():
    parser = FrequencyParser(language="fr")
    # Cadence : toutes les 2 semaines -> weekly#2w
    # Limite : pendant 3 mois -> @+3m
    assert parser.parse("Toutes les 2 semaines pendant 3 mois") == "today@weekly#2w@+3m"