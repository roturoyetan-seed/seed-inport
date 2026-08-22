# Comparatif Genesis Wave / nuage de points

Mesure locale du 21 août 2026 avec Python 3, sur les mêmes conteneurs GPAK1.
Les temps sont des temps muraux en secondes. Chaque restauration a été contrôlée
bit à bit avec `cmp`.

| Données | Représentation | Taille | Création | Restauration |
|---|---:|---:|---:|---:|
| texte répétitif (360 000 octets) | points `.gen` | 119 875 049 o | 8,02 s | 110,91 s |
| texte répétitif (360 000 octets) | onde `.gwave` | 373 o | 0,80 s | 0,06 s |
| aléatoire (65 536 octets) | points `.gen` | 21 167 114 o | 1,58 s | 20,18 s |
| aléatoire (65 536 octets) | onde `.gwave` | 65 744 o | 0,43 s | 0,04 s |

Sur ces essais, Wave est environ 321 381 fois plus compacte et 1 849 fois plus
rapide à restaurer sur le texte répétitif. Sur les données aléatoires, elle est
322 fois plus compacte et 505 fois plus rapide à restaurer.

Ces résultats ne signifient pas que la transformation ondulatoire compresse seule
le texte par un tel facteur : le `.gwave` utilise aussi Bzip2, tandis que le `.gen`
est une représentation textuelle explicite de douze points par octet. Sur les
données aléatoires, aucune compression n'a été rentable ; Wave évite surtout
l'expansion géométrique des points. Les résultats ne constituent donc pas un ratio
universel et doivent être rebenchés sur les données réellement visées.
