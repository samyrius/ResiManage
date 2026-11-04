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


## Évolution du calendrier — sélecteurs journaliers et correctifs motivés

- Chaque cellule UMC et Réanimation chirurgicale dispose désormais de son propre sélecteur multiple, limité aux résidents locaux actifs de 1re à 3e année.
- Les résidents de 4e année restent visibles dans le sélecteur mais désactivés pour les nouvelles gardes, conformément à la dispense DEMS actuellement indiquée. L'historique d'octobre et son rapprochement nominatif restent consultables.
- Le retrait d'une affectation n'efface plus sa trace : un motif d'au moins cinq caractères est obligatoire ; la ligne passe inactive et le correctif conserve le résident, la date, le secteur, le motif, l'auteur et l'horodatage.
- Les affectations retirées ne figurent plus dans le calendrier actif ni dans les exports CSV/PDF. Le journal des correctifs est visible sur le mois et inclus dans le PDF.
- Un export PDF mensuel paysage A4 est disponible à côté du calendrier.
- Les changements sont réservés au Super Admin ; l'ajout multiple est atomique : si un résident est invalide ou déjà affecté ce jour-là dans le même secteur, toute la sélection est refusée.

## Génération automatique : étape bloquée volontairement

Le générateur mensuel n'est pas activé tant que les règles de composition et de roulement ne sont pas confirmées. Le planning d'octobre contient des libellés non résolus et ambigus ; il ne peut pas être converti sans risque en identités ni servir à inférer les quotas de promotion. La génération devra créer un brouillon cinq jours avant la fin du mois, calculer l'équité séparément par promotion, exclure les 4e années actuellement dispensées, puis conserver les corrections humaines avec leur motif. Le PDF du brouillon devra rester rééditable pendant tout le mois.
