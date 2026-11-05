# Carnet de board — ResiManage

Dernière mise à jour : 3 novembre 2026
Dépôt : https://github.com/samyrius/ResiManage

## État général

- **P0 — BLOQUANT :** sur téléphone réel, écran blanc puis « the local server could not start. System exit 1 ».
- APK Android non validée. Le succès du workflow CI ne prouve pas le fonctionnement sur téléphone physique.
- Cause racine du code 1 inconnue; obtenir traceback Python et logcat avant d'affirmer une cause.
- Branche officielle `resimanage-2-work` à préserver. PR #91 ouverte et non fusionnée selon le dernier état consigné.

## Carte des travaux

| ID | Sujet | État | Prochaine action |
|---|---|---|---|
| AND-001 | Serveur local Android quitte avec code 1 | BLOQUANT / ouvert | Collecter logcat + stderr/traceback et reproduire |
| AND-002 | Validation WebView | À renforcer | Vérifier visuellement l'écran de connexion, pas seulement HTTP 200 |
| AND-003 | Ressources embarquées | À vérifier | Inspecter APK et chemins des templates, CSS, Python et dépendances |
| UI-001 | Thèmes HTML/CSS indépendants | Intégrés sur branche candidate | Vérifier les 7 thèmes après résolution Android |
| UI-002 | Navigation, scroll, boutons, barre fixe | À valider sur téléphone | Tests manuels de non-régression |
| GARDES-001 | Tableau de garde et règles métier | Exigences consignées | Poursuivre après stabilisation du démarrage |

## Builds et preuves

- Run `41647148965` : build Android debug rapportée réussie; SHA-256 APK `d73cd4ecb98841b9ef9133208ffcf4a44dc945bdbf74c4d68a940dd7e49335a0`.
- Run `41655909006` (attempt 2), commit `d37b57bac4ea015dbb77f1661a870d62f8fd6842` : GitHub Actions `success`; vérification HTTP locale insuffisante au vu du retour physique.
- Artefact émulateur : `13239662712`.
- Tests Python précédemment rapportés : 172/172 réussis; ils ne valident pas le démarrage Android.

## Branches et gouvernance

- Officielle : `resimanage-2-work`.
- Candidate d'intégration : `integration/resimanage-refonte-themes-2026-11-03`.
- Branche amont de travail citée : `work/resimanage-refonte-themes-gardes-2026-11-02`.
- PR #91 : https://github.com/samyrius/ResiManage/pull/91 — ouverte, non fusionnée à la dernière vérification enregistrée.
- Le dépôt comporte aussi des branches `backup/`, `baseline/`, `docs/`, `feature/`, `fix/`, `integration/`, `resimanage-2-*` et `ui/`. Rafraîchir l'inventaire complet depuis GitHub avant nettoyage/fusion; le nom d'une branche ne prouve pas que son contenu est intégré.

## Règles de clôture

1. Ne déclarer Android corrigé qu'après logs du démarrage et affichage visible de la page de connexion.
2. Distinguer build réussie, test HTTP, test émulateur et validation téléphone réel.
3. Documenter SHA, runs, artefacts, tests et résultats exacts.
4. Préserver la branche officielle; ne fusionner PR #91 qu'après accord explicite.

## Relevé des branches — 3 novembre 2026


- Comparaison GitHub entre `resimanage-2-work` (base) et `integration/resimanage-refonte-themes-2026-11-03` (candidate) : statut `ahead`, candidate en avance de **110 commits**, **0 commit en retard** au moment du relevé. Base SHA `7e87d7f6d6d425336c3f17d72c5dabf962f3c89b`.
- Fichiers modifiés/ajoutés signalés par la comparaison : workflow Android et Windows, CI, registre, `android/app/build.gradle`, `MainActivity.java`, `app.py` (+531/-43), données de gardes `data/gardes_octobre_2026.json`, `guards.py` (nouveau), tests `test_app.py` et `test_guards.py`, sept CSS de thèmes, sept templates HTML et documents d'audit/fonctionnalité des gardes.
- Cette comparaison décrit précisément l'écart de la branche candidate par rapport à la branche officielle; elle ne signifie pas que tous les changements ont été testés sur téléphone ni qu'ils sont prêts à fusionner.
- Le dépôt expose également de nombreuses branches historiques et spécialisées (`backup/`, `baseline/`, `docs/`, `feature/`, `fix/`, `integration/`, `resimanage-2-*`, `ui/`). Leur contenu intégral n'a pas été copié dans ce registre : chaque branche doit être comparée à sa base et ses commits inspectés avant classement. Aucun nettoyage/suppression n'a été effectué.

## Matrice centrale des affectations — 5 novembre 2026

- La matrice unique est implémentée sur la branche candidate : 19 services actifs en lignes, quatre périodes en colonnes.
- Les dates sont modifiables dans l'en-tête des périodes ; l'interrupteur de gestion des capacités est directement accessible depuis le tableau.
- Les capacités peuvent être désactivées pour les affectations manuelles ; lorsqu'elles sont activées, les capacités et places restantes sont contrôlées. Les autres règles métier restent actives dans les deux modes.
- Un clic sur le nom ouvre une fiche superposée avec historique de stages et affectations actuelles.
- Un appui prolongé permet le déplacement tactile ; le déplacement souris et une solution de repli sont également prévus. Le serveur valide et journalise le déplacement.
- La position de défilement est conservée après enregistrement. Les messages temporaires disparaissent sans bouton de fermeture.
- L'affichage est optimisé pour le paysage sur smartphone et s'adapte aux tablettes/ordinateurs.
- La route historique /planning renvoie vers le tableau central ; il n'y a pas de second écran de planification.
- Validation automatisée : le premier run a révélé des tests anciens à adapter ; un nouveau run est en cours au moment de cette note. Ne pas annoncer la suite verte avant lecture du résultat.
- Aucune nouvelle APK n'est encore validée sur émulateur ou téléphone réel. Le contrôle visuel sur appareil reste à faire.
