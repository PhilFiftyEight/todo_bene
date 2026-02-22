Set Shell fish
Output ./01-setup.gif
Set FontSize 18
Set Width 1200
Set Height 600
Set Padding 40
Set Theme "Catppuccin Frappe"

# Lancement de l'app
Type "tb" Sleep 1s Enter
Sleep 2s

# Saisie du profil
Type "username@localhost" Sleep 500ms Enter
Enter
Type "y" Sleep 500ms Enter
Sleep 5s

# Affichage du fichier config pour montrer que c'est propre
Type "cat /Users/philippe/.config/todo_bene/config.json" Sleep 500ms Enter
Sleep 4s
Enter
Type "Tour rapide des commandes / Quick tour of the command lines" Sleep 500ms
Backspace 60
Enter

# Type command help
Type "tb add --help" Sleep 500ms Enter
Sleep 5s

Type "tb list --help" Sleep 500ms Enter
Sleep 5s

Type "tb list-dev --help " Sleep 500ms Enter
Sleep 5s
