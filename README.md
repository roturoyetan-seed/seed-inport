# Genesis — Seeds publiques

Dépôt attendu : `https://github.com/roturoyetan-seed/seed-inport`

Fichiers consommés par le lanceur Genesis :

- `seed-genesis-installer.gseed` : micro-installateur initial ;
- `seed-essencial.gseed` : environnement complet avec 8 agents et un 9e coordinateur interactif ;
- `genesis-multi-ia.gseed` : package autonome de l'équipe IA et du coordinateur ;
- `next.gseed` : copie de la seed IA utilisée comme enfant par la seed essentielle ;
- `seed-outils-execution-code.gseed` : outil importable pour exécuter Python, Bash et Node, avec Bubblewrap ou confirmation de repli ;
- `seed-controle-terminal.gseed` : terminal persistant avec les droits utilisateur, confirmation initiale, audit et arrêt d’urgence ;
- `seed-outils-5000.gseed` : répertoire GDR1 de 5 000 outils déclaratifs ;
- `seed-repertoire.gseed` : répertoire GDR1 des modules Genesis ;
- `seed-modeles.gseed` : 32 recettes d'installation de modèles Ollama ;
- `model-catalog.json` : tailles et besoins matériels des modèles ;
- `catalog.json` : catalogue des modules ;
- `SHA256SUMS` : empreintes de contrôle.

Ces fichiers ne contiennent ni mots de passe, ni clés API, ni poids de modèles IA.
Genesis vérifie la signature et le SHA-256 avant toute expansion.

La nouvelle génération conserve les noms publics historiques sans suffixe de version.
La version du produit est déclarée dans les manifestes internes, pas dans les noms de
fichiers. Les quatre fichiers principaux ci-dessus contiennent donc les fonctions les
plus récentes : équipe continue, missions ciblées, agents temporaires, atelier contrôlé
et Drag & Drop.

Au lancement d'une mission, un second terminal ouvre automatiquement le 9e agent
coordinateur. Il peut modifier l'objectif, mettre l'équipe en pause, reprendre,
arrêter proprement et activer ou désactiver un agent entre deux réponses.
