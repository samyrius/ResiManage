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