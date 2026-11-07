# Audit des sources de garde — octobre 2026

Date de contrôle : 2 novembre 2026  
Branche de travail : `work/resimanage-refonte-themes-gardes-2026-11-02`

## Sources examinées

- `liste_garde_residents_octobre_2026.html` : 31 journées, colonnes UMC et Réanimation chirurgicale, horaires.
- `residents_anesthesie_reanimation_2025-2026.html` : promotions 1re à 4e année, D.E.M.S. et encadrement.

## Effectifs de la liste nominative

| Groupe | Effectif |
|---|---:|
| 1re année | 26 |
| 2e année | 12 |
| 3e année | 24 |
| 4e année | 11 |
| D.E.M.S. | 18 |

Les D.E.M.S. sont une rubrique distincte et ne doivent pas être ajoutés automatiquement aux promotions actives.

## Contrôle des 70 libellés distincts présents dans le planning

- 52 libellés correspondent à un nom de famille unique dans la liste nominative.
- 5 libellés sont ambigus et nécessitent une validation humaine :
  - `ARAB.A` et `ARAB.H` : la liste contient ARAB HAFSA (1re année) et ARAB ANIS (3e année).
  - `BERKANE.A` et `BERKANE.K` : la liste contient BERKANE AMINE et BERKANE KHALIDA, mais les initiales de prénom ne sont pas fournies dans le planning.
  - `HADJI` : la liste contient HADJI YASMINE (4e année) et HADJI DYHIA (D.E.M.S.).
- 3 libellés semblent être des variantes typographiques ou des noms composés, sans correspondance automatique sûre :
  - `BENMOUSSA` / BEN MOUSSA ;
  - `HAMROUNE` / HAMROUN ;
  - `SAID AISSA` / SAID AISSA HAMMOU.
- 10 libellés ne sont pas retrouvés dans les promotions ni dans la liste D.E.M.S. :
  - `BENSADOK`, `FERHAT.FZ`, `FERHAT.S`, `HANED`, `MAHIEDDINE`, `MEDJEDOUB`, `NEHAL`, `SADOUNE`, `SARNI`, `ZANOUNE`.

Le planning contient aussi des formes abrégées et des graphies différentes. Aucun rapprochement incertain ne doit être transformé en identifiant de résident sans validation.

## Conséquence pour le développement

Le planning d'octobre doit être conservé comme historique source, sans réécriture des noms. Le futur module de gardes doit :

1. stocker la date, le secteur, l'équipe affichée, les horaires et la provenance ;
2. permettre une saisie ou correction manuelle ;
3. proposer des correspondances nominatives seulement lorsqu'elles sont uniques ;
4. signaler les ambiguïtés et les noms non retrouvés ;
5. exclure les D.E.M.S. du roulement actif par défaut ;
6. conserver les effectifs et roulements propres à chaque promotion, sans supposer des groupes de taille identique.

## Limite actuelle

Les deux fichiers donnent le planning d'octobre et les listes nominatives 2025-2026. Ils ne décrivent pas explicitement la règle mathématique de succession entre les équipes, les jours de repos, ni les règles de répartition entre promotions pour novembre. Il serait donc risqué de fabriquer automatiquement le planning de novembre en répétant ou en décalant mécaniquement les 31 lignes d'octobre. Le calendrier de novembre devra rester en brouillon tant que ces règles n'auront pas été déduites d'un roulement validé ou confirmées dans l'application.
