import pytest
import pendulum
from todo_bene.domain.services.frequency_engine import FrequencyEngine
from todo_bene.domain.services.frequency_parser import FrequencyParser

@pytest.fixture
def engine():
    return FrequencyEngine()

@pytest.fixture
def parser():
    def _make_parser(lang="fr"):
        return FrequencyParser(language=lang)
    return _make_parser

@pytest.fixture
def tz():
    return pendulum.local_timezone()

# --- TEST DES CADENCES (La logique Pendulum) ---
@pytest.mark.parametrize("freq_str, base_date, expected_dates", [
    # "2026-03-22@monthly@3" -> On veut les 3 mois SUIVANTS
    (
        "2026-03-22@monthly@3", 
        None, 
        ["2026-04-22", "2026-05-22", "2026-06-22"]
    ),
    # Cas "tomorrow" @daily@2 (Aujourd'hui = 01/01, Tomorrow = 02/01)
    # Répétition 1 = 03/01, Répétition 2 = 04/01
    (
        "tomorrow@daily@2", 
        pendulum.datetime(2026, 1, 1), 
        ["2026-01-03", "2026-01-04"]
    ),
     # Test fin de mois (Jan 31 -> Fév 28 -> Avr 30)
    (
        "2026-01-31@monthly@3", 
        None, 
        ["2026-02-28", "2026-03-31", "2026-04-30"]
    ),   
    # Ton cas Yearly bissextile (29 Fév 2024 @ 1)
    (
        "2024-02-29@yearly@1", 
        None, 
        ["2025-02-28"] 
    )
])
def test_frequency_engine_cadence_logic(engine, freq_str, base_date, expected_dates):
    # Si on a une base_date, on voyage dans le temps
    if base_date:
        pendulum.travel_to(base_date, freeze=True)
    try:
        occurrences = engine.get_occurrences(freq_str, base_now=base_date)
    
        assert len(occurrences) == len(expected_dates)
        for i, date_str in enumerate(expected_dates):
            assert occurrences[i].to_date_string() == date_str
    finally:
        pendulum.travel_back()

# --- TEST DES LIMITES (Le Tableau Métier) ---
@pytest.mark.parametrize("freq_str, expected_count", [
    # Yearly : "only single duplicate" -> Max 1
    ("2026-01-01@yearly@5", 1), 
    
    # Daily : Max 366 (1 an)
    ("2026-01-01@daily@500", 366),
    
    # Weekly : Max 52 (1 an)
    ("2026-01-01@weekly@100", 52),
    
    # Monthly : Max 12 (1 an)
    ("2026-01-01@monthly@24", 12),
])
def test_frequency_engine_business_limits(engine, freq_str, expected_count):
    occurrences = engine.get_occurrences(freq_str)
    assert len(occurrences) == expected_count

# --- TEST DES CAS D'ERREURS (Fail-Fast) ---
@pytest.mark.parametrize("invalid_str", [
    "2026-03-22@unknown@3",   # Cadence invalide
    "2026-03-22@monthly@X",   # Limite non numérique
    "wrong-date@daily@1",     # Date invalide
    "2026-03-22@monthly@-1",  # Limite négative
    "2026-03-22@monthly",     # Format incomplet
])
def test_frequency_engine_parsing_errors(engine, invalid_str):
    with pytest.raises(ValueError) as excinfo:
        engine.get_occurrences(invalid_str)
    assert "Instruction de fréquence" in str(excinfo.value)


# -------- TESTS avec l'utilisation du parser -----------------
def test_mirror_frequency_parser_simple_interval(engine, parser):
    """
    Vérifie que l'Engine peut traiter les sorties du SimpleIntervalExtractor.
    """
    # Fixation au 1er Janvier 2026 (Année non bissextile : 365 jours)
    base_date = pendulum.datetime(2026, 1, 1)
    fr_parser = parser(lang="fr")
    
    with pendulum.travel_to(base_date, freeze=True):
        # --- CAS 1 : "Chaque jour" -> today@daily#1d@∞ ---
        # Ici, l'Engine doit comprendre que ∞ = 365 jours (limite métier 2026)
        instruction_1 = fr_parser.parse("Chaque jour") 
        occurrences_1 = engine.get_occurrences(instruction_1)
        
        assert occurrences_1[0].to_date_string() == "2026-01-02"
        assert occurrences_1[-1].to_date_string() == "2027-01-01"
        assert len(occurrences_1) == 365 # Car 2026 n'est pas bissextile

        # --- CAS 2 : "Toutes les 2 semaines" -> today@weekly#2w@∞ ---
        instruction_2 = fr_parser.parse("Toutes les 2 semaines")
        occurrences_2 = engine.get_occurrences(instruction_2)
        
        # 52 semaines / 2 = 26 occurrences
        assert occurrences_2[0].to_date_string() == "2026-01-15"
        assert len(occurrences_2) == 26

        # --- CAS 3 : English Mirror "Every 3 weeks" ---
        instruction_3 = parser(lang="en").parse("Every 3 weeks")
        occurrences_3 = engine.get_occurrences(instruction_3)
        
        # 52 / 3 = 17.33 -> 17 occurrences
        assert occurrences_3[0].to_date_string() == "2026-01-22"
        assert len(occurrences_3) == 17

def test_mirror_frequency_parser_multi_days(engine, parser, tz):
    # Fixation au jeudi 1er Janvier 2026
    base_date = pendulum.datetime(2026, 1, 1, tz=tz)
    fr_parser = parser(lang="fr")
    
    with pendulum.travel_to(base_date, freeze=True):
        # "Lundi et Jeudi"
        instruction = fr_parser.parse("Lundi et Jeudi") 
        # On s'attend à recevoir le lundi et le jeudi suivants
        occurrences = engine.get_occurrences(instruction, base_date)
        
        # Le 01/01/2026 est un jeudi. 
        # Selon la logique, on veut le 1er lundi (05/01) et le 1er jeudi (08/01)
        assert len(occurrences) == 2
        assert occurrences[0].to_date_string() == "2026-01-05"
        assert occurrences[1].to_date_string() == "2026-01-08"
    
    with pendulum.travel_to(base_date, freeze=True):
        instruction = fr_parser.parse("Lundi, Mercredi et Vendredi") 
        occurrences = engine.get_occurrences(instruction, base_date)
        
        # On attend 3 occurrences
        assert len(occurrences) == 3
        # 1er Janvier = Jeudi.
        # Prochain Lundi = 05/01
        # Prochain Mercredi = 07/01
        # Prochain Vendredi = 02/01
        
        # Après le tri chronologique, l'ordre doit être :
        assert occurrences[0].to_date_string() == "2026-01-02" # Vendredi
        assert occurrences[1].to_date_string() == "2026-01-05" # Lundi
        assert occurrences[2].to_date_string() == "2026-01-07" # Mercredi

def test_mirror_frequency_parser_specific_day(engine, parser, tz):
    # Fixation au jeudi 1er Janvier 2026
    base_date = pendulum.datetime(2026, 1, 1, tz=tz) # C'est un jeudi
    fr_parser = parser(lang="fr")
    
    with pendulum.travel_to(base_date, freeze=True):
        # --- ASSERT 1 : "Tous les lundis" ---
        # Parser -> "today@weekly#1mon@∞"
        instruction_1 = fr_parser.parse("Tous les lundis")
        occurrences_1 = engine.get_occurrences(instruction_1, base_date)

        # On attend la limite métier hebdomadaire (52)
        assert len(occurrences_1) == 52
        # Premier lundi après le 01/01/2026 (jeudi) -> 05/01/2026
        assert occurrences_1[0].to_date_string() == "2026-01-05"
        # Vérification de la récurrence (Lundi suivant)
        assert occurrences_1[1].to_date_string() == "2026-01-12"

        # --- ASSERT 2 : "Chaque vendredi" ---
        # Parser -> "today@weekly#1fri@∞"
        instruction_2 = fr_parser.parse("Chaque vendredi")
        occurrences_2 = engine.get_occurrences(instruction_2, base_date)

        # On attend aussi 52 occurrences
        assert len(occurrences_2) == 52
        # Premier vendredi après le 01/01/2026 (jeudi) -> 02/01/2026
        assert occurrences_2[0].to_date_string() == "2026-01-02"
        # Vérification de la récurrence (Vendredi suivant)
        assert occurrences_2[1].to_date_string() == "2026-01-09"

def test_mirror_frequency_parser_sequence_days(engine, parser, tz):
    """
    Test Miroir Strict :
    Valide "1, 2, 4, 8, 16 jours" -> today@sequence#1,2,4,8,16d@5
    """
    # Fixation au 1er Janvier 2026
    base_date = pendulum.datetime(2026, 1, 1, tz=tz)
    fr_parser = parser(lang="fr")
    
    with pendulum.travel_to(base_date, freeze=True):
        instruction = fr_parser.parse("1, 2, 4, 8, 16 jours")
        occurrences = engine.get_occurrences(instruction, base_date)

        # On attend exactement 5 occurrences
        assert len(occurrences) == 5
        
        # Calcul des dates attendues :
        # 01/01 + 1j = 02/01
        # 01/01 + 2j = 03/01 (Attention: l'extracteur sequence semble souvent cumulatif ou relatif)
        # Selon le format "1, 2, 4... d", on attend généralement des offsets par rapport à aujourd'hui
        assert occurrences[0].to_date_string() == "2026-01-02"
        assert occurrences[1].to_date_string() == "2026-01-03"
        assert occurrences[2].to_date_string() == "2026-01-05"
        assert occurrences[3].to_date_string() == "2026-01-09"
        assert occurrences[4].to_date_string() == "2026-01-17"

def test_mirror_frequency_parser_sequence_variable_spaces(engine, parser, tz):
    """
    Test Miroir Strict :
    Vérifie la robustesse aux espaces dans les séquences.
    """
    # Fixation au 1er Janvier 2026
    base_date = pendulum.datetime(2026, 1, 1, tz=tz)
    fr_parser = parser(lang="fr")
    
    with pendulum.travel_to(base_date, freeze=True):
        # --- ASSERT 1 : "1,2,3 jours" (Serré) ---
        instruction_1 = fr_parser.parse("1,2,3 jours")
        # Instruction attendue : "today@sequence#1,2,3d@3"
        occ_1 = engine.get_occurrences(instruction_1, base_date)
        
        assert len(occ_1) == 3
        assert occ_1[0].to_date_string() == "2026-01-02" # +1j
        assert occ_1[1].to_date_string() == "2026-01-03" # +2j
        assert occ_1[2].to_date_string() == "2026-01-04" # +3j

        # --- ASSERT 2 : "10, 20 jours" (Avec espace) ---
        instruction_2 = fr_parser.parse("10, 20 jours")
        # Instruction attendue : "today@sequence#10,20d@2"
        occ_2 = engine.get_occurrences(instruction_2, base_date)
        
        assert len(occ_2) == 2
        assert occ_2[0].to_date_string() == "2026-01-11" # +10j
        assert occ_2[1].to_date_string() == "2026-01-21" # +20j

def test_mirror_frequency_parser_next_occurrences(engine, parser, tz):
    """
    Test Miroir Strict :
    Valide "Les 5 prochains jours" et "3 prochaines semaines".
    """
    # Fixation au 1er Janvier 2026 (Jeudi)
    base_date = pendulum.datetime(2026, 1, 1, tz=tz)
    fr_parser = parser(lang="fr")
    
    with pendulum.travel_to(base_date, freeze=True):
        # --- ASSERT 1 : "Les 5 prochains jours" ---
        # Parser -> "today@sequence#1,2,3,4,5d@5"
        instruction_1 = fr_parser.parse("Les 5 prochains jours")
        occ_1 = engine.get_occurrences(instruction_1, base_date)
        
        assert len(occ_1) == 5
        # On vérifie le premier et le dernier bond
        assert occ_1[0].to_date_string() == "2026-01-02" # J+1
        assert occ_1[4].to_date_string() == "2026-01-06" # J+5

        # --- ASSERT 2 : "3 prochaines semaines" ---
        # Parser -> "today@sequence#1,2,3w@3"
        instruction_2 = fr_parser.parse("3 prochaines semaines")
        occ_2 = engine.get_occurrences(instruction_2, base_date)
        
        assert len(occ_2) == 3
        # On vérifie les bonds hebdomadaires
        assert occ_2[0].to_date_string() == "2026-01-08" # W+1 (8 Janvier)
        assert occ_2[1].to_date_string() == "2026-01-15" # W+2 (15 Janvier)
        assert occ_2[2].to_date_string() == "2026-01-22" # W+3 (22 Janvier)

def test_mirror_frequency_parser_post_processing_duration(engine, parser, tz):
    """
    Test Miroir Strict :
    Valide "Tous les lundis pour 1 mois" et "Chaque jour pendant 15 jours".
    """
    # Fixation au jeudi 1er Janvier 2026
    base_date = pendulum.datetime(2026, 1, 1, tz=tz)
    fr_parser = parser(lang="fr")
    
    with pendulum.travel_to(base_date, freeze=True):
        # --- ASSERT 1 : "Tous les lundis pour 1 mois" ---
        # Parser -> "today@weekly#1mon@+1m"
        # Du 01/01 au 01/02, les lundis sont : 05/01, 12/01, 19/01, 26/01.
        instruction_1 = fr_parser.parse("Tous les lundis pour 1 mois")
        occ_1 = engine.get_occurrences(instruction_1, base_date)
        
        assert len(occ_1) == 4
        assert occ_1[0].to_date_string() == "2026-01-05"
        assert occ_1[-1].to_date_string() == "2026-01-26"

        # --- ASSERT 2 : "Chaque jour pendant 15 jours" ---
        # Parser -> "today@daily#1d@+15d"
        # Du 01/01 + 15 jours = 16/01.
        # Comme on commence à J+1 (daily#1d), on attend 15 occurrences (du 02 au 16 inclus).
        instruction_2 = fr_parser.parse("Chaque jour pendant 15 jours")
        occ_2 = engine.get_occurrences(instruction_2, base_date)
        
        assert len(occ_2) == 15
        assert occ_2[0].to_date_string() == "2026-01-02"
        assert occ_2[-1].to_date_string() == "2026-01-16"

def test_mirror_frequency_parser_post_processing_duration_extended(engine, parser, tz):
    """
    Test Miroir Strict :
    Valide les combinaisons complexes Cadence + Durée (+2w, +6m, +1y).
    """
    base_date = pendulum.datetime(2026, 1, 1, tz=tz)
    fr_parser = parser(lang="fr")
    
    with pendulum.travel_to(base_date, freeze=True):
        # 1. Multi-jours + Durée
        # "Lundi et Mercredi pendant 2 semaines" -> weekly#1mon,wed@+2w
        # Attendus : 05/01, 07/01, 12/01, 14/01 (Le 19/01 est > 15/01)
        inst_1 = fr_parser.parse("Lundi et Mercredi pendant 2 semaines")
        occ_1 = engine.get_occurrences(inst_1, base_date)
        assert len(occ_1) == 4
        assert occ_1[-1].to_date_string() == "2026-01-14"

        # 2. Intervalle + Durée
        # "Toutes les 2 semaines pour 6 mois" -> weekly#2w@+6m
        inst_2 = fr_parser.parse("Toutes les 2 semaines pour 6 mois")
        occ_2 = engine.get_occurrences(inst_2, base_date)        
        # 181 jours / 14 jours = 12.92 -> 12 occurrences est le chiffre correct.
        assert len(occ_2) == 12 
        assert occ_2[0].to_date_string() == "2026-01-15"
        # La dernière : 1er Janvier + (12 * 14 jours) = 168 jours plus tard -> 18 Juin
        assert occ_2[-1].to_date_string() == "2026-06-18"

        # 3. Unités variées (10d, 1y)
        assert len(engine.get_occurrences(fr_parser.parse("Chaque jour pour 10 jours"), base_date)) == 10
        # 2026 n'est pas bissextile -> 365 jours
        assert len(engine.get_occurrences(fr_parser.parse("Chaque jour pendant 1 an"), base_date)) == 365

        # 4. Test de robustesse (espaces multiples et majuscules)
         # "Tous les lundis    pendant   3   semaines"
        assert len(engine.get_occurrences(fr_parser.parse("Tous les lundis    pendant   3   semaines"), base_date)) == 3

        # 5. Chaque jour + 2 prochaines semaines -> daily#1d@+2w
        inst_6 = fr_parser.parse("chaque jour les 2 prochaines semaines")
        occ_6 = engine.get_occurrences(inst_6, base_date)
        assert len(occ_6) == 14

def test_mirror_frequency_parser_next_with_duration_fixed(engine, parser, tz):
    # Lundi 5 Janvier 2026
    base_date = pendulum.datetime(2026, 1, 5, tz=tz)
    fr_parser = parser(lang="fr")
    
    with pendulum.travel_to(base_date, freeze=True):
        inst = fr_parser.parse("Les 5 prochains jours pendant 2 semaines")
        occ = engine.get_occurrences(inst, base_date)
        
        # 10 occurrences (2 semaines de 5 jours)
        assert len(occ) == 10
        
        # Semaine 1 : du 06/01 au 10/01 (offsets 1 à 5)
        # Note : Si 'today' est le lundi 5, +1j = mardi 6.
        assert occ[0].to_date_string() == "2026-01-06" # Mardi
        assert occ[4].to_date_string() == "2026-01-10" # Samedi (5 jours après lundi)

        # Semaine 2 : On ajoute 7 jours de cycle
        assert occ[5].to_date_string() == "2026-01-13" # Mardi suivant
        assert occ[9].to_date_string() == "2026-01-17" # Samedi suivant

    # Fixation au 1er Janvier 2026
    base_date = pendulum.datetime(2026, 1, 1, tz=tz)
    fr_parser = parser(lang="fr")
    
    with pendulum.travel_to(base_date, freeze=True):
        # --- ASSERT 2 : "Les 3 prochains mois" ---
        # Parser -> "today@sequence#1,2,3m@3"
        # Ici pas de date de fin (+), juste une limite numérique.
        inst_2 = fr_parser.parse("Les 3 prochains mois")
        occ_2 = engine.get_occurrences(inst_2, base_date)
        
        assert len(occ_2) == 3
        assert occ_2[0].to_date_string() == "2026-02-01"
        assert occ_2[1].to_date_string() == "2026-03-01"
        assert occ_2[2].to_date_string() == "2026-04-01"

def test_mirror_frequency_parser_absolute_deadlines(engine, parser, tz):
    """
    Test Miroir : Validation des limites par dates fixes (Fin de mois, semestre, date précise).
    Fige le temps au Lundi 9 Février 2026.
    """
    base_date = pendulum.datetime(2026, 2, 9, tz=tz)
    fr_parser = parser(lang="fr")
    
    with pendulum.travel_to(base_date, freeze=True):
        # 1. Jusqu'à la fin du mois (28 fév 2026)
        # Parser -> "today@daily#1d@2026-02-28"
        inst_1 = fr_parser.parse("Chaque jour jusqu'à la fin du mois")
        occ_1 = engine.get_occurrences(inst_1, base_date)
        # Du 10 fév au 28 fév inclus = 19 jours
        assert len(occ_1) == 19
        assert occ_1[-1].to_date_string() == "2026-02-28"

        # 2. Jusqu'au 15 juin (Date fixe)
        # Parser -> "today@weekly#1fri@2026-06-15"
        inst_2 = fr_parser.parse("Chaque vendredi jusqu'au 15 juin")
        occ_2 = engine.get_occurrences(inst_2, base_date)
        # Les vendredis jusqu'au 15/06 (le dernier est le 12/06)
        assert occ_2[-1].to_date_string() == "2026-06-12"
        assert all(o.day_of_week == pendulum.FRIDAY for o in occ_2)

        # 3. Jusqu'au 1er janvier (Année suivante si passé)
        # Parser -> "today@daily#1d@2027-01-01"
        inst_3 = fr_parser.parse("Tous les jours jusqu'au 1er janvier")
        occ_3 = engine.get_occurrences(inst_3, base_date)
        # On vérifie juste la fin du tunnel
        assert occ_3[-1].to_date_string() == "2027-01-01"
    
    # Test Miroir : Validation de la limite "Fin du semestre".
    # Du 9 février 2026 au 30 juin 2026.    
    # Lundi 9 Février 2026
    base_date = pendulum.datetime(2026, 2, 9, tz=tz)
    fr_parser = parser(lang="fr")
    
    with pendulum.travel_to(base_date, freeze=True):
        # Parser -> "today@weekly#1mon@2026-06-30"
        instruction = fr_parser.parse("Tous les lundis jusqu'à la fin du semestre")
        occurrences = engine.get_occurrences(instruction, base_date)

        # Calcul manuel pour validation :
        # Fév : 16, 23 (2)
        # Mars : 2, 9, 16, 23, 30 (5)
        # Avr : 6, 13, 20, 27 (4)
        # Mai : 4, 11, 18, 25 (4)
        # Juin : 1, 8, 15, 22, 29 (5)
        # Total attendu : 20 occurrences
        
        assert len(occurrences) == 20
        
        # Le premier lundi généré (Lundi suivant le 9 fév)
        assert occurrences[0].to_date_string() == "2026-02-16"
        
        # Le dernier lundi du semestre
        assert occurrences[-1].to_date_string() == "2026-06-29"
        
        # On vérifie qu'on n'a pas débordé en juillet
        assert occurrences[-1] <= pendulum.datetime(2026, 6, 30, tz=tz)

def test_mirror_frequency_parser_exception_single_day(engine, parser, tz):
    """
    Test Miroir : Validation de l'exclusion d'un jour spécifique.
    "Chaque jour sauf le lundi" à partir du dimanche 01/02/2026.
    """
    # Dimanche 1er Février 2026
    base_date = pendulum.datetime(2026, 2, 1, tz=tz)
    fr_parser = parser(lang="fr")
    
    with pendulum.travel_to(base_date, freeze=True):
        # Parser -> "today@daily#1d@∞!mon"
        # On va demander les 7 premières occurrences pour voir si le lundi saute.
        instruction = fr_parser.parse("Chaque jour sauf le lundi")
        occurrences = engine.get_occurrences(instruction, base_date)

        # On vérifie les 6 premières occurrences (puisque le lundi est exclu)
        # Attendus : Lundi 2 (EXCLU), Mardi 3, Mercredi 4, Jeudi 5, Vendredi 6, Samedi 7, Dimanche 8.
        
        # Le premier doit être le mardi 3 car le lundi 2 est banni
        assert occurrences[0].to_date_string() == "2026-02-03"
        # On vérifie que le lundi a bien été banni sur toute la chaîne
        assert all(occ.day_of_week != pendulum.MONDAY for occ in occurrences)
        
        # On vérifie la cohérence du volume
        # 312 selon la clôture de ta boucle de 365 jours
        assert len(occurrences) == 312 
        
        # Le dernier jour est bien un dimanche (fin de cycle)
        assert occurrences[-1].to_date_string() == "2027-01-31"
        assert occurrences[-1].day_of_week == pendulum.SUNDAY

def test_mirror_frequency_parser_exception_multiple_days(engine, parser, tz):
    """
    Test Miroir : Validation de l'exclusion du week-end.
    "Tous les jours sauf samedi et dimanche" à partir du vendredi 06/02/2026.
    """
    # Vendredi 6 Février 2026
    base_date = pendulum.datetime(2026, 2, 6, tz=tz)
    fr_parser = parser(lang="fr")
    
    with pendulum.travel_to(base_date, freeze=True):
        # Parser -> "today@daily#1d@∞!sat,sun"
        instruction = fr_parser.parse("Tous les jours sauf samedi et dimanche")
        occurrences = engine.get_occurrences(instruction, base_date)

        # Vérification sur les premières occurrences :
        # J+1 : Samedi 07/02 (EXCLU)
        # J+2 : Dimanche 08/02 (EXCLU)
        # J+3 : Lundi 09/02 -> OK (1ère occurrence)
        # J+4 : Mardi 10/02 -> OK (2ème occurrence)
        
        assert occurrences[0].to_date_string() == "2026-02-09"
        assert occurrences[0].day_of_week == pendulum.MONDAY
        
        # Sur un cycle complet, on ne doit trouver ni samedi ni dimanche
        assert all(occ.day_of_week not in [pendulum.SATURDAY, pendulum.SUNDAY] for occ in occurrences[:20])

def test_mirror_frequency_parser_exception_with_duration(engine, parser, tz):
    """
    Test Miroir : Durée relative + Exclusion.
    "Every day for 2 weeks but not on Wednesday"
    Départ : Lundi 09/02/2026.
    """
    base_date = pendulum.datetime(2026, 2, 9, tz=tz)
    en_parser = parser(lang="en")
    
    with pendulum.travel_to(base_date, freeze=True):
        # Parser -> "today@daily#1d@+2w!wed"
        instruction = en_parser.parse("Every day for 2 weeks but not on Wednesday")
        occurrences = engine.get_occurrences(instruction, base_date)

        # Calcul : 
        # 14 jours générés (du 10/02 au 23/02 inclus).
        # Dans ces 14 jours, il y a 2 mercredis (le 11/02 et le 18/02).
        # Total attendu : 14 - 2 = 12 occurrences.
        
        assert len(occurrences) == 12
        
        # Vérification qu'aucun mercredi n'est présent
        assert all(occ.day_of_week != pendulum.WEDNESDAY for occ in occurrences)
        
        # Vérification des frontières
        assert occurrences[0].to_date_string() == "2026-02-10" # Mardi (OK)
        # Mercredi 11 est sauté, donc l'index 1 est le Jeudi 12
        assert occurrences[1].to_date_string() == "2026-02-12"

def test_mirror_frequency_parser_exception_before_duration(engine, parser, tz):
    """
    Test Miroir : Validation que l'ordre des composants (Exclusion vs Durée) 
    dans la chaîne n'altère pas le résultat de l'Engine.
    """
    base_date = pendulum.datetime(2026, 2, 9, tz=tz)
    en_parser = parser(lang="en")
    
    with pendulum.travel_to(base_date, freeze=True):
        # Les deux phrases doivent produire la même chaîne d'instruction
        inst_1 = en_parser.parse("Every day for 2 weeks but not on Wednesday")
        inst_2 = en_parser.parse("Every day but not on Wednesday for 2 weeks")
        
        assert inst_1 == inst_2 == "today@daily#1d@+2w!wed"
        
        # Et donc exactement les mêmes occurrences
        occ_1 = engine.get_occurrences(inst_1, base_date)
        occ_2 = engine.get_occurrences(inst_2, base_date)
        
        assert occ_1 == occ_2
        assert len(occ_1) == 12

def test_mirror_frequency_parser_before_duration_fr(engine, parser, tz):
    """
    Test Miroir : Validation de la tournure "à l'exception de" + Durée.
    """
    # Lundi 9 Février 2026
    base_date = pendulum.datetime(2026, 2, 9, tz=tz)
    fr_parser = parser(lang="fr")
    
    with pendulum.travel_to(base_date, freeze=True):
        # Parser -> "today@daily#1d@+2w!wed"
        instruction = fr_parser.parse("Tous les jours à l'exception du mercredi pendant 2 semaines")
        occurrences = engine.get_occurrences(instruction, base_date)

        # On attend toujours 12 occurrences sur les 14 jours glissants
        assert len(occurrences) == 12
        
        # On vérifie spécifiquement que le mercredi 11 février a été sauté
        # occ[0] = Mardi 10
        # occ[1] = Jeudi 12
        assert occurrences[0].to_date_string() == "2026-02-10"
        assert occurrences[1].to_date_string() == "2026-02-12"

def test_mirror_frequency_parser_complex_ordinals(engine, parser, tz):
    """
    Test Miroir : Validation des jours ordinaux (position absolue).
    "Le cent trente-cinquième jour de l'année"
    "Le vingt-septième jour du trimestre"
    """
    base_date = pendulum.datetime(2026, 1, 1, tz=tz) # On part du début d'année
    fr_parser = parser(lang="fr")
    
    with pendulum.travel_to(base_date, freeze=True):
        # 1. Année : 135ème jour de 2026
        # Janvier(31) + Fév(28) + Mars(31) + Avril(30) = 120 jours.
        # 135 - 120 = 15 Mai.
        inst_year = fr_parser.parse("Le cent trente-cinquième jour de l'année")
        occ_year = engine.get_occurrences(inst_year, base_date)
        assert occ_year[0].to_date_string() == "2026-05-15"

        # 2. Trimestre : 27ème jour du trimestre actuel (T1 2026)
        # T1 commence le 01/01. Le 27ème jour est le 27/01.
        inst_q = fr_parser.parse("Le vingt-septième jour du trimestre")
        occ_q = engine.get_occurrences(inst_q, base_date)
        assert occ_q[0].to_date_string() == "2026-01-27"

def test_mirror_frequency_parser_workdays_position(engine, parser, tz):
    """
    Test Miroir : Validation de la position en jours ouvrés.
    "Le deuxième jour ouvré du mois"
    En Février 2026 : 
    - Lundi 02/02 est le 1er jour ouvré.
    - Mardi 03/02 est le 2ème jour ouvré.
    """
    # On se place en Février 2026
    base_date = pendulum.datetime(2026, 2, 1, tz=tz) 
    fr_parser = parser(lang="fr")
    
    with pendulum.travel_to(base_date, freeze=True):
        # Parser -> "today@monthly#2ndworkday@∞"
        instruction = fr_parser.parse("Le deuxième jour ouvré du mois")
        occurrences = engine.get_occurrences(instruction, base_date)

        # Le 1er février est un dimanche (non ouvré)
        # Le 2 février est un lundi (1er ouvré)
        # Le 3 février est un mardi (2ème ouvré)
        assert occurrences[0].to_date_string() == "2026-02-03"

def test_mirror_frequency_parser_last_friday_year(engine, parser, tz):
    """
    Test Miroir : Le dernier vendredi de l'année.
    En 2026, le 31 décembre est un jeudi.
    Le dernier vendredi est donc le 25 décembre 2026.
    """
    base_date = pendulum.datetime(2026, 1, 1, tz=tz)
    en_parser = parser(lang="en")
    
    with pendulum.travel_to(base_date, freeze=True):
        # Parser -> "today@yearly#lastfri@∞"
        instruction = en_parser.parse("The last friday of the year")
        occurrences = engine.get_occurrences(instruction, base_date)

        assert occurrences[0].to_date_string() == "2026-12-25"

def test_mirror_frequency_parser_shift_weekend(engine, parser, tz):
    """
    Test Miroir : Vérifie le décalage au jour ouvré suivant.
    'Le 1er du mois, reporter si week-end'
    En Février 2026, le 1er est un Dimanche. Il doit être reporté au Lundi 2.
    """
    fr_parser = parser(lang="fr")
    # Simulation du temps au 1er Janvier
    base_date = pendulum.datetime(2026, 1, 1, tz=tz)
    
    with pendulum.travel_to(base_date, freeze=True):
        # Instruction générée par le parser : "today@monthly#1stday@∞|next_workday"
        instruction = fr_parser.parse("Le 1er du mois, reporter si week-end")
        occurrences = engine.get_occurrences(instruction)

        # 1er Février 2026 = Dimanche -> Report au Lundi 2 Février
        february_occ = next(occ for occ in occurrences if occ.month == 2)
        assert february_occ.to_date_string() == "2026-02-02"
        assert february_occ.day_of_week == pendulum.MONDAY

        # 1er Mars 2026 = Dimanche -> Report au Lundi 2 Mars
        march_occ = next(occ for occ in occurrences if occ.month == 3)
        assert march_occ.to_date_string() == "2026-03-02"

def test_mirror_frequency_parser_shift_business_context(engine, parser, tz):
    """
    Test Miroir : Cas de la facturation/paie le 5 du mois.
    'Le 5 du mois décaler si jour non ouvré'
    En Juillet 2026, le 5 est un Dimanche.
    """
    fr_parser = parser(lang="fr")
    # On se place au 1er Juin 2026
    base_date = pendulum.datetime(2026, 6, 1, tz=tz)
    
    with pendulum.travel_to(base_date, freeze=True):
        # Le parser doit générer : "today@monthly#5thday@∞|next_workday"
        instruction = fr_parser.parse("Le 5 du mois décaler si jour non ouvré")
        occurrences = engine.get_occurrences(instruction)

        # 5 Juin 2026 = Vendredi (OK)
        june_occ = next(occ for occ in occurrences if occ.month == 6)
        assert june_occ.to_date_string() == "2026-06-05"

        # 5 Juillet 2026 = Dimanche -> Report au Lundi 6 Juillet
        july_occ = next(occ for occ in occurrences if occ.month == 7)
        assert july_occ.to_date_string() == "2026-07-06"
        assert july_occ.day_of_week == pendulum.MONDAY

def test_mirror_frequency_parser_shift_explicit_instruction(engine, parser, tz):
    """
    Test Miroir : Le dernier vendredi du trimestre.
    Q1 2026 : Fin mars. Le dernier vendredi est le 27 mars.
    Q2 2026 : Fin juin. Le dernier vendredi est le 26 juin.
    """
    fr_parser = parser(lang="fr")
    # On se place au 1er Janvier 2026
    base_date = pendulum.datetime(2026, 1, 1, tz=tz)
    
    with pendulum.travel_to(base_date, freeze=True):
        # Instruction : "today@quarter#lastfri@∞|next_workday"
        instruction = fr_parser.parse("Le dernier vendredi du trimestre, si férié décaler")
        occurrences = engine.get_occurrences(instruction)

        # Vérification Q1 (Mars)
        q1_occ = next(occ for occ in occurrences if occ.month == 3)
        assert q1_occ.to_date_string() == "2026-03-27"
        assert q1_occ.day_of_week == pendulum.FRIDAY

        # Vérification Q2 (Juin)
        q2_occ = next(occ for occ in occurrences if occ.month == 6)
        assert q2_occ.to_date_string() == "2026-06-26"
        assert q2_occ.day_of_week == pendulum.FRIDAY

def test_mirror_frequency_parser_mixed_units_arbitration(engine, tz):
    """
    Test Miroir : Toutes les 2 semaines pendant 3 mois.
    Si on commence le 1er Janvier, on doit s'arrêter fin Mars.
    """
    # 1er Janvier 2026
    base_date = pendulum.datetime(2026, 1, 1, tz=tz)
    
    with pendulum.travel_to(base_date, freeze=True):
        # Instruction : toutes les 2 semaines, limite +3 mois
        instruction = "today@weekly#2w@+3m"
        occurrences = engine.get_occurrences(instruction)

        # On attend environ 6 à 7 occurrences sur 3 mois (toutes les 2 semaines)
        # Janvier : 1, 15, 29
        # Février : 12, 26
        # Mars : 12, 26
        assert len(occurrences) >= 6
        assert len(occurrences) <= 7
        
        # La dernière doit être avant le 1er Avril 2026
        limit_date = base_date.add(months=3)
        assert all(occ < limit_date for occ in occurrences)
        
        # Vérification de l'intervalle de 14 jours entre deux dates
        assert (occurrences[1] - occurrences[0]).days == 14

def test_mirror_frequency_parser_yearly_position(parser, engine, tz):
    """
    Test Miroir : Le 1er lundi d'octobre.
    En 2026, le 1er octobre est un jeudi. Le 1er lundi est le 5.
    """
    # On se place en début d'année 2026
    base_date = pendulum.datetime(2026, 1, 1, tz=tz)
    fr_parser = parser(lang="fr")
    
    with pendulum.travel_to(base_date, freeze=True):
        # Format attendu par le parser : today@yearly#1stmon@oct@∞
        #instruction = "today@yearly#1stmon@oct@∞"
        instruction = fr_parser.parse("Le 1er lundi d'octobre")
        occurrences = engine.get_occurrences(instruction, base_date)

        assert len(occurrences) == 1
        # La première occurrence de 2026 doit être le 5 Octobre
        assert occurrences[0].to_date_string() == "2026-10-05"
        assert occurrences[0].day_of_week == pendulum.MONDAY

        # 1er remplacé par premier
        instruction = fr_parser.parse("Le premier lundi d'octobre")
        assert instruction == "today@yearly#1stmon@oct@∞"
            
        # Vérification du Moteur (le DSL reste identique)
        occurrences = engine.get_occurrences(instruction, base_date)
        assert len(occurrences) == 1
        assert occurrences[0].to_date_string() == "2026-10-05"

def test_mirror_frequency_engine_working_day_position(engine, tz):
    """
    Test Miroir : Le 5ème jour ouvré du mois.
    Mai 2026 :
    - Ven 1 : Férié
    - Sam 2 / Dim 3 : Week-end
    - Lun 4 (JO 1), Mar 5 (JO 2), Mer 6 (JO 3), Jeu 7 (JO 4), Ven 8 (JO 5)
    """
    # On se place au 1er Mai 2026
    base_date = pendulum.datetime(2026, 5, 1, tz=tz)
    
    # L'instruction telle que produite par le parser
    instruction = "today@monthly#5thworkday@∞"

    with pendulum.travel_to(base_date, freeze=True):
        occurrences = engine.get_occurrences(instruction, base_now=base_date)

        # On vérifie la première occurrence
        # Note : Si le 8 mai est férié dans ton service, ce sera le lundi 11 mai.
        assert occurrences[0].to_date_string() == "2026-05-11"

def test_mirror_frequency_engine_last_day_of_month(engine, tz):
    """
    Test Miroir : Le dernier vendredi du mois.
    Février 2026 :
    - Sam 28 : Dernier jour du mois.
    - Ven 27 : Dernier vendredi -> Cible.
    """
    # On se place au 1er Février 2026
    base_date = pendulum.datetime(2026, 2, 1, tz=tz)
    
    # L'instruction issue du parser
    instruction = "today@monthly#lastfri@∞"

    with pendulum.travel_to(base_date, freeze=True):
        occurrences = engine.get_occurrences(instruction, base_now=base_date)

        # On vérifie la première occurrence (Février 2026)
        assert occurrences[0].to_date_string() == "2026-02-27"
        
        # On vérifie la deuxième occurrence (Mars 2026)
        # Mars se termine le 31 (Mardi), le dernier vendredi est le 27.
        assert occurrences[1].to_date_string() == "2026-03-27"

def test_mirror_frequency_engine_exclusion_month(engine, tz):
    """
    Test Miroir : Tous les lundis sauf en août.
    En 2026 :
    - Juillet finit le mercredi 29 (dernier lundi le 27).
    - Août : lundis les 3, 10, 17, 24, 31 -> Doivent être exclus.
    - Septembre : premier lundi le 7.
    """
    base_date = pendulum.datetime(2026, 7, 20, tz=tz) # Un lundi de juillet
    instruction = "today@weekly#1mon@∞!aug"

    with pendulum.travel_to(base_date, freeze=True):
        occurrences = engine.get_occurrences(instruction, base_now=base_date)        
        # On vérifie qu'on n'a pas de dates en août (mois 8)
        months_found = [o.month for o in occurrences]
        assert 8 not in months_found
        
        # La date après le 27 juillet doit être le 7 septembre
        # (On saute les 5 lundis d'août)
        idx_july = next(i for i, o in enumerate(occurrences) if o.to_date_string() == "2026-07-27")
        assert occurrences[idx_july + 1].to_date_string() == "2026-09-07"
    
    #. Tous les jours sauf en mai (!may)
    #  Quotidien sauf Mai 2026
    # On se place fin avril
    base_may = pendulum.datetime(2026, 4, 30, tz=tz)
    parser = FrequencyParser(language="fr")
    instruction_may = parser.parse("Tous les jours sauf en mai")

    with pendulum.travel_to(base_may, freeze=True):
        occurrences = engine.get_occurrences(instruction_may, base_now=base_may)
        # La date après le 30 avril doit être le 1er juin
        assert occurrences[0].to_date_string() == "2026-06-01"

    #  Hebdomadaire (Lundi) sauf Août 2026
    # in english
    base_aug = pendulum.datetime(2026, 7, 20, tz=tz) # Dernier lundi de juillet
    parser = FrequencyParser(language="en")
    instruction = parser.parse("Every Monday except in August")

    with pendulum.travel_to(base_aug, freeze=True):
        occurrences = engine.get_occurrences(instruction, base_now=base_aug)
        # On vérifie que l'occurrence suivante saute tout le mois d'août
        # Juillet 27 -> (saut des 5 lundis d'août) -> Septembre 7
        assert occurrences[1].to_date_string() == "2026-09-07"

def test_mirror_exclusion_month_short_fr_en(parser, engine, tz):
    """
    Test Miroir : "sauf août" (FR) / "except August" (EN).
    Vérifie que le parser normalise en !aug et que l'engine filtre le mois 8.
    """
    base_date = pendulum.datetime(2026, 7, 27, tz=tz) # Dernier lundi de juillet
    
    # --- ASSERTIONS PARSER (Injectées dans l'Engine) ---
    
    # 1. Cas Français
    fr_parser = parser(lang="fr")
    instruction_fr = fr_parser.parse("Tous les lundis sauf août")
    assert instruction_fr == "today@weekly#1mon@∞!aug"
    
    # 2. Cas Anglais
    en_parser = parser(lang="en")
    instruction_en = en_parser.parse("Every Monday except August")
    assert instruction_en == "today@weekly#1mon@∞!aug"

    # --- VÉRIFICATION MOTEUR ---
    
    with pendulum.travel_to(base_date, freeze=True):
        # On utilise l'instruction générée par le parser
        occurrences = engine.get_occurrences(instruction_fr, base_now=base_date)
        
        # Le premier lundi d'août (03/08) doit être absent
        # Le 27 juillet est occurrences[0], l'indice [1] doit sauter directement en septembre
        assert occurrences[0].to_date_string() == "2026-09-07"
        assert occurrences[1].to_date_string() == "2026-09-14"
        
        # Double vérification : aucun mois d'août dans la liste
        assert all(o.month != 8 for o in occurrences)

def test_mirror_parse_single_day_name_returns_next_occurrence_fr(parser, engine, tz):
    """
    Vérifie que l'engine génère bien la date du mercredi 25 février 
    à partir du DSL produit pour "Mercredi" le 19 février.
    """
    with pendulum.travel_to(pendulum.datetime(2026,2,19, tz=tz)):
        instruction = parser().parse("Mercredi")
        occurrences = engine.get_occurrences(instruction)
        date_expected = pendulum.DateTime(2026, 2, 25, 0, 0, 0, tzinfo=tz)
        assert occurrences == [date_expected]


# def test_mirror_every_two_days_next_fortnight(parser, engine, tz):
#     """
#     Test Miroir : "Tous les 2 jours à partir de la prochaine quinzaine"
#     Si on est le 16 Février 2026 :
#     - Prochaine quinzaine = 2 Mars 2026.
#     - Fréquence = Tous les 2 jours.
#     """
#     # Fixons la date au lundi 16 Février 2026
#     today = pendulum.datetime(2026, 2, 16, tz=tz)
#     fr_parser = parser(lang="fr")

#     with pendulum.travel_to(today, freeze=True):
#         # 1. Le Parser génère l'instruction
#         # Note: Le parser doit calculer 16 Fév + 14 jours = 2 Mars
#         instruction = fr_parser.parse("Tous les 2 jours à partir de la prochaine quinzaine")
        
#         # On vérifie que le segment de date est correct (2026-03-02)
#         assert instruction.startswith("2026-03-02")
#         assert "daily#2d" in instruction

#         # 2. Le Moteur génère les occurrences
#         occurrences = engine.get_occurrences(instruction, base_now=today)

#         # La première occurrence (i=1, interval=2) : 2 Mars + 2 jours = 4 Mars
#         # Car le moteur fait start_date.add(days=step) où step = i * interval
#         assert occurrences[0].to_date_string() == "2026-03-04"
#         assert occurrences[1].to_date_string() == "2026-03-06"