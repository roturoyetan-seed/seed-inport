# Genesis Wave — seed complète et lanceur V1

Ce dossier réduit permet l'envoi GitHub sans dépasser 100 fichiers.

Il contient une seed unique avec Genesis Wave, la configuration automatique, les neuf agents, les prompts, la connaissance Wave et les fichiers nécessaires à la dernière version.

## Restaurer

```bash
chmod +x lancer-genesis-v1.sh
./lancer-genesis-v1.sh
```

## Lancer Genesis Wave

```bash
python3 Genesis-Wave-V1-restaure/Genesis-Wave-App/genesis_wave_app.py
```

Le lanceur vérifie l'empreinte SHA-256 et refuse de restaurer dans un dossier non vide.
