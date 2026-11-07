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
- Les choix d’affectation sont limités aux résidents locaux actifs des années 1 à 4. Les résidents archivés dans le DEMS et ceux explicitement marqués « préparation DEMS » sont exclus.
- Les libellés ambigus ou absents de la liste restent à traiter manuellement.

## Génération future
Le mois courant qui ne possède aucune affectation reste vide. Le module ne fabrique pas de gardes et ne répète pas mécaniquement octobre : les règles mathématiques de succession, les repos et les contraintes de roulement doivent être confirmés avant d’activer un générateur automatique.

## Stockage et portabilité
Le schéma guard_sources / guard_assignments est ajouté à la base existante de manière additive ; aucune table de résidents, d’affectations de stages ou d’historique de rotations n’est remplacée.
Le module Python et la source JSON sont inclus dans les tâches de préparation Android. La source JSON est également ajoutée aux données embarquées du paquet Windows.

## Tests
tests/test_guards.py couvre l’import idempotent, les 233 affectations, les 70 libellés, les horaires du week-end, le calendrier mensuel vide, les modifications manuelles, la validation des correspondances, l’éligibilité des nouveaux 4e années et l’exclusion individuelle des préparants DEMS, ainsi que les exports CSV/PDF.


## Évolution du calendrier — sélecteurs journaliers et correctifs motivés

- Chaque cellule UMC et Réanimation chirurgicale dispose de son propre sélecteur multiple, ouvert aux résidents locaux actifs de 1re à 4e année.
- La dispense de garde pour préparation DEMS est un statut individuel géré par un Super Admin depuis la rubrique DEMS. Seuls les résidents explicitement marqués « en préparation DEMS » sont désactivés ; les nouveaux 4e années sont admissibles par défaut. L'historique d'octobre et son rapprochement nominatif restent consultables.
- Le retrait d'une affectation n'efface plus sa trace : un motif d'au moins cinq caractères est obligatoire ; la ligne passe inactive et le correctif conserve le résident, la date, le secteur, le motif, l'auteur et l'horodatage.
- Les affectations retirées ne figurent plus dans le calendrier actif ni dans les exports CSV/PDF. Le journal des correctifs est visible sur le mois et inclus dans le PDF.
- Un export PDF mensuel paysage A4 est disponible à côté du calendrier.
- Les changements sont réservés au Super Admin ; l'ajout multiple est atomique : si un résident est invalide ou déjà affecté ce jour-là dans le même secteur, toute la sélection est refusée.

## Génération automatique : étape bloquée volontairement

Le générateur mensuel n'est pas activé tant que les règles de composition et de roulement ne sont pas confirmées. Le planning d'octobre contient des libellés non résolus et ambigus ; il ne peut pas être converti sans risque en identités ni servir à inférer les quotas de promotion. La génération devra créer un brouillon cinq jours avant la fin du mois, calculer l'équité séparément par promotion, exclure uniquement les résidents explicitement marqués en préparation DEMS, puis conserver les corrections humaines avec leur motif. Le PDF du brouillon devra rester rééditable pendant tout le mois.


## Édition centrale et document signé — novembre 2026

- Le calendrier mensuel conserve la vue d'ensemble des deux secteurs et permet d'ajouter plusieurs résidents dans chaque cellule.
- Sur ordinateur, un glisser-déposer déplace une affectation vers une autre date ou un autre secteur. Sur écran tactile, un appui long suivi d'un glissement effectue le déplacement à un doigt.
- Déposer un résident sur un autre résident permute leurs deux affectations. Le serveur vérifie les doublons, la validité des affectations et la cohérence du mois avant l'enregistrement.
- Un clic sur le nom d'un résident ouvre sa fiche dans une fenêtre superposée, avec ses informations de dossier, l'historique des stages, les affectations, les examens, les congés, les stages externes et les objectifs.
- L'éditeur de document permet de préparer un texte d'accompagnement avec gras, italique, souligné, taille, police et couleur. Le contenu est filtré côté serveur avant stockage et export.
- La signature peut être saisie au clavier (nom et fonction) ou dessinée au doigt / à la souris dans une zone dédiée. Elle est ajoutée à la fin du PDF mensuel.
- L'export PDF paysage A4 contient le calendrier actif, le texte mis en forme, la signature et l'historique des correctifs. Les affectations retirées restent exclues du calendrier actif.
- Les actions d'édition, de déplacement, de permutation, de suppression et de signature restent réservées au Super Admin. Les suppressions conservent un motif obligatoire et une trace d'audit.
