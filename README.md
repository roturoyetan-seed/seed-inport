# Genesis Wave

Version expérimentale de Genesis utilisant une onde numérique réversible à la
place du nuage de points. Les fichiers sont restaurés sans perte et contrôlés par
SHA-256.

## Fichiers publiables

- `seed-essencial-wave.gseed` : seed du pack essentiel (format `GWS1`) ;
- `seed-essencial-wave.gwave` : onde du pack essentiel (format `GWV2`) ;
- `genesis-multi-ia-wave.gseed` : seed de l'environnement multi-IA ;
- `genesis-multi-ia-wave.gwave` : onde de l'environnement multi-IA ;
- `seed-genesis-installer-wave.gseed` : seed du bootstrap installateur ;
- `seed-genesis-installer-wave.gwave` : onde du bootstrap installateur ;
- `seed-outils-5000-wave.gseed` : une seed Wave regroupant les 5 000 seeds d'outils ;
- `seed-outils-5000-wave.gwave` : la représentation ondulatoire du même catalogue ;
- `genesis_wave_core.py` : créateur, lecteur et vérificateur ;
- `test_genesis_wave.py` : tests automatisés ;
- `SHA256SUMS-WAVE` : empreintes des huit artefacts.
- `RAPPORT-WAVE-VS-POINTS.md` : mesures comparatives face au nuage de points.

## Vérification

```bash
sha256sum -c SHA256SUMS-WAVE
python3 genesis_wave_core.py inspect seed-essencial-wave.gwave --verify
python3 -m unittest -v test_genesis_wave.py
```

## Restauration

```bash
python3 genesis_wave_core.py restore \
  --wave seed-essencial-wave.gwave restauration-essential
```

L'onde conserve une transformation réelle (`onde-differentielle`,
`onde-acceleration` ou `onde-xor`). Le programme compare les représentations et
les codecs disponibles, puis conserve le plus petit résultat sans perte.

## Catalogue des 5 000 outils

Le catalogue est repris directement de `seed-outils-5000.gseed` de Genesis normal.
Il contient 5 000 seeds enfants de recettes/outils procéduraux dans dix familles :
texte, données, fichiers, code, tests, sécurité, compression, 3D, web et prompts.
Il ne contient pas les binaires de 5 000 logiciels tiers et ne les installe pas.

```bash
python3 genesis_wave_core.py restore \
  --seed seed-outils-5000-wave.gseed outils-5000
```
