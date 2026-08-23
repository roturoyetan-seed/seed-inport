# Genesis Wave — seed complète et lanceur V1

Ce dossier réduit permet l'envoi GitHub sans dépasser 100 fichiers.

Il contient une seed unique avec Genesis Wave, la configuration automatique, les neuf agents, les prompts, la connaissance Wave et les fichiers nécessaires à la dernière version.

## Installer depuis GitHub

Remplace `<URL_DU_DEPOT>` par l'adresse HTTPS affichée par le bouton vert **Code** de GitHub.

```bash
git clone <URL_DU_DEPOT>
cd Genesis-GitHub-V2
sha256sum -c SHA256SUMS
chmod +x lancer-genesis-v1.sh
./lancer-genesis-v1.sh
python3 Genesis-Wave-V1-restaure/Genesis-Wave-App/genesis_wave_app.py
```

Exemple d'adresse :

```text
https://github.com/TON-COMPTE/Genesis-GitHub-V2.git
```

## Installation en une commande après clonage

```bash
cd Genesis-GitHub-V2 && sha256sum -c SHA256SUMS && chmod +x lancer-genesis-v1.sh && ./lancer-genesis-v1.sh && python3 Genesis-Wave-V1-restaure/Genesis-Wave-App/genesis_wave_app.py
```

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
