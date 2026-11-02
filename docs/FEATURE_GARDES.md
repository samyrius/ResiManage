# Module Gardes — première intégration

## Accès et fonctions
- Le module est accessible depuis le bouton Gardes du tableau de bord et depuis le menu « Stages et planification ».
- Vue mensuelle des deux secteurs : UMC et Réanimation chirurgicale.
- Ajout/retrait manuel d'affectations, choix de l'horaire, rapprochement nominatif, export CSV et impression du calendrier.
- Les mois sont conservés dans la base locale rotation.db ; le journal d'audit conserve les opérations effectuées.

## Import historique d’octobre 2026
La source data/gardes_octobre_2026.json est la transcription structurée des 31 lignes du fichier HTML transmis. Elle contient 233 affectations individuelles, 70 libellés distincts, les deux secteurs et les horaires figurant dans le document.
L’import est idempotent : il est effectué une seule fois par base, et un instantané de la source ainsi que son empreinte SHA-256 sont conservés dans guard_sources.

## Règles de sécurité des identités
- Chaque libellé importé reste non résolu au départ. Aucun nom n’est automatiquement transformé en résident.
- Une suggestion exacte de nom peut être affichée à titre indicatif ; seul le Super Admin peut confirmer le rapprochement.
- La validation d’un libellé met à jour ses occurrences, sans effacer le libellé d’origine conservé dans la source.
- Les choix d’affectation sont limités aux résidents locaux actifs des promotions 1 à 4. Les résidents archivés dans le DEMS sont exclus.
- Les libellés ambigus ou absents de la liste restent à traiter manuellement.

## Génération future
Le mois courant qui ne possède aucune affectation reste vide. Le module ne fabrique pas de gardes et ne répète pas mécaniquement octobre : les règles mathématiques de succession, les repos et les contraintes de roulement doivent être confirmés avant d’activer un générateur automatique.

## Stockage et portabilité
Le schéma guard_sources / guard_assignments est ajouté à la base existante de manière additive ; aucune table de résidents, d’affectations de stages ou d’historique de rotations n’est remplacée.
Le module Python et la source JSON sont inclus dans les tâches de préparation Android. La source JSON est également ajoutée aux données embarquées du paquet Windows.

## Tests
tests/test_guards.py couvre l’import idempotent, les 233 affectations, les 70 libellés, les horaires du week-end, le calendrier mensuel vide, les modifications manuelles, la validation des correspondances, l’exclusion du DEMS et l’export CSV.
