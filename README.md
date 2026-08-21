# Genesis — Seeds publiques

Dépôt attendu : `https://github.com/roturoyetan-seed/seed-inport`

Fichiers consommés par le lanceur Genesis :

- `seed-genesis-installer.gseed` : micro-installateur initial ;
- `seed-essencial.gseed` : environnement complet avec 8 agents et un 9e coordinateur interactif ;
- `seed-outils-5000.gseed` : répertoire GDR1 de 5 000 outils déclaratifs ;
- `seed-repertoire.gseed` : répertoire GDR1 des modules Genesis ;
- `seed-modeles.gseed` : 32 recettes d'installation de modèles Ollama ;
- `model-catalog.json` : tailles et besoins matériels des modèles ;
- `catalog.json` : catalogue des modules ;
- `SHA256SUMS` : empreintes de contrôle.

Ces fichiers ne contiennent ni mots de passe, ni clés API, ni poids de modèles IA.
Genesis vérifie la signature et le SHA-256 avant toute expansion.

Au lancement d'une mission, un second terminal ouvre automatiquement le 9e agent
coordinateur. Il peut modifier l'objectif, mettre l'équipe en pause, reprendre,
arrêter proprement et activer ou désactiver un agent entre deux réponses.
