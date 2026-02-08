# todo_bene/i18n/lexicons.py

LEXICONS = {
    "fr": {
        # Fréquences de base
        "toutes les": "every", 
        "chaque": "every", 
        "tous les": "every",
        
        # Unités de temps
        "semestre": "semester",
        "semaines": "w", 
        "semaine": "w", 
        "jours": "d", 
        "jour": "d",
        "mois": "m", 
        "ans": "y", 
        "an": "y",
        
        # Jours de la semaine
        "lundis": "mon", "lundi": "mon",
        "mardis": "tue", "mardi": "tue",
        "mercredis": "wed", "mercredi": "wed",
        "jeudis": "thu", "jeudi": "thu",
        "vendredis": "fri", "vendredi": "fri",
        "samedis": "sat", "samedi": "sat",
        "dimanches": "sun", "dimanche": "sun",

        # Conjonction de coordination
        "et": ",",

        # Préposition
        "jusqu'à la fin de l'": "until_end",
        "jusqu'à la fin de": "until_end",
        "jusqu'à la fin du": "until_end",
        "jusqu'à la fin": "until",  
        "jusqu'à fin": "until",
        "jusqu'au": "until",
        "jusqu'à": "until",
        "trimestre": "quarter",
        "semestre": "semester",
        "quinzaine": "fortnight",                           

        # projection "ex: prochaine semaine"
        "prochaines": "next",
        "prochains": "next",
        "prochain": "next",
        "pendant": "for",
        "durant": "for",
        "pour": "for",

        # Mois
        "janvier": "01", "février": "02", "mars": "03", "avril": "04", 
        "mai": "05", "juin": "06", "juillet": "07", "août": "08", 
        "septembre": "09", "octobre": "10", "novembre": "11", "décembre": "12",
        "1er": "1",

        # stop words
        "stopwords": ["le", "la", "les", "des", "du", "de", "l'"],
    },

    "en": {
        # Base frequencies
        "every": "every", 
        "each": "every",
        
        # Time units
        "semester": "semester",
        "weeks": "w", 
        "week": "w", 
        "days": "d", 
        "day": "d",
        "months": "m", 
        "month": "m", 
        "years": "y", 
        "year": "y",
        
        # Days of the week
        "mondays": "mon", "monday": "mon",
        "tuesdays": "tue", "tuesday": "tue",
        "wednesdays": "wed", "wednesday": "wed",
        "thursdays": "thu", "thursday": "thu",
        "fridays": "fri", "friday": "fri",
        "saturdays": "sat", "saturday": "sat",
        "sundays": "sun", "sunday": "sun",

        # coordinating conjunction
        "and": ",",

        # preposition
        "until the end of": "until_end",
        "until end of": "until_end",
        "until": "until",
        "until": "until",
        "till": "until",
        "up to": "until",
        
        "quarter": "quarter",
        "semester": "semester",
        "fortnight": "fortnight",

        # projection, example: "next week"
        "next": "next",
        "for": "for",
        "during": "for",

        # Months
        "january": "01", "february": "02", "march": "03", "april": "04",
        "may": "05", "june": "06", "july": "07", "august": "08",
        "september": "09", "october": "10", "november": "11", "december": "12",

        # stop words
        "stopwords": ["the", "a", "an", "of"],
    }
}