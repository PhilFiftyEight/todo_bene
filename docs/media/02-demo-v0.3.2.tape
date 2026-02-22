Set Shell fish
Set FontSize 16
Set Width 1300
Set Height 800
Set Padding 20
Set Theme "Catppuccin Frappe"

# Navigation dans les vues
Type "tb list -p week" Sleep 500ms Enter
Sleep 4s
Enter

Type "tb list -p month" Sleep 500ms Enter
Sleep 4s

#Type "Détails d'une tâche (exemple l'index 5) / Details of a task (example index 5)"
#Backspace 77
Type "5" Sleep 500ms Enter
Sleep 2s

#Type "création d'une sous-tache / creating a subtask"
#Backspace 46
Type "n" Sleep 500ms Enter
Type "Commiter les derniers changements" Sleep 500ms Enter
Type "Message en Anglais" Sleep 500ms Enter
Type "y" Sleep 500ms Enter
Sleep 500ms Enter
Sleep 500ms Enter
Sleep 3s Enter
Sleep 2s

#Type "Modification d'une tache / Changing a todo"
#Backspace 42
Type "1" Sleep 500ms Enter
Sleep 3s
Type "m" Sleep 500ms Enter
Sleep 1s Enter
Type "Write the commit message in English." Sleep 500ms Enter
Sleep 500ms Enter
Sleep 500ms Enter
Sleep 500ms Enter
Type "22/02/2026 16:00" Sleep 500ms Enter
Sleep 3s Enter
Sleep 4s Enter

#Type "Terminer un Todo / finish Todo"
#Backspace 30
Type "4" Sleep 500ms Enter
Type "t" Sleep 2s Enter
Type "y" Sleep 2s Enter
Type "o" Sleep 500ms Enter
Type "Lundi, Mercredi et Vendredi pendant 6 semaines" Sleep 2s Enter

# TODO terminer avec enfant et répéter à une date pour montrer la répétition avec enfants
Sleep 4s Enter

# Action de retour et quitter
Type "q" Sleep 1s Enter
Type "tb list -p all" Sleep 500ms Enter
Sleep 4s Enter
