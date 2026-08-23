# Genesis GitHub GWave V1

Distribution minimale sur le modèle de Genesis GitHub V2, entièrement publiée sous forme GWAVE.

## Contenu du dépôt

- `genesis-complet-v1.gwave` : seed unique compressée qui installe Genesis Wave au complet ;
- `lancer-genesis-v1.sh` : télécharge la seed depuis GitHub, vérifie son SHA-256 et l'installe ;
- `genesis_wave_core.py` et `genesis_core.py` : moteur de restauration autonome ;
- `SHA256SUMS` : empreintes de tous les fichiers publiés ;
- `.gitignore` : exclut le cache et les installations restaurées.

La seed unique contient l'application, les configurations d'amélioration et automatique, la connaissance Genesis, les catalogues de modèles et d'outils, les interfaces, ainsi que les seeds utilisées par le logiciel. Aucun téléchargement complémentaire n'est nécessaire pour restaurer la version complète. Les fonctions de synchronisation GitHub restent disponibles après installation.

## Installation

```bash
git clone https://github.com/roturoyetan-seed/Genesis-Seed-Originelle-V1.git
cd Genesis-Seed-Originelle-V1
sha256sum -c SHA256SUMS
chmod +x lancer-genesis-v1.sh
./lancer-genesis-v1.sh
python3 Genesis-GWave-V1-restaure/Genesis-Wave-App/genesis_wave_app.py
```

Le lanceur récupère par défaut :

```text
https://raw.githubusercontent.com/roturoyetan-seed/Genesis-Seed-Originelle-V1/main/genesis-complet-v1.gwave
```

Il refuse une empreinte incorrecte et une destination non vide.
