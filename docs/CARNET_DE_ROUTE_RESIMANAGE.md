# Carnet de route — ResiManage

Mise à jour : 3 novembre 2026

## Situation au point de reprise

L'utilisateur a installé deux APK successives. La première a affiché « The local Server did not respond. Close and reopen the app ». La seconde affiche « the local server could not start. System exit 1 ». Incident bloquant : écran blanc et serveur Python local qui ne démarre pas correctement sur le téléphone.

## Chronologie technique

1. Une APK debug issue d'un workflow GitHub Actions a été livrée pour tester l'intégration des sept thèmes.
2. Premier retour : serveur local ne répond pas.
3. Une analyse antérieure a attribué le défaut à l'absence supposée du template `themes/crystal3d.html` dans le paquet Android et annoncé une correction.
4. Run `41655909006` terminé avec succès sur GitHub Actions, commit `d37b57bac4ea015dbb77f1661a870d62f8fd6842`.
5. Après installation, l'utilisateur signale `System exit 1`.
6. Conclusion : incident non résolu; l'hypothèse précédente ne suffit pas. Diagnostiquer le crash réel et renforcer la validation CI.

## Établi / non établi

### Établi

- L'utilisateur rapporte que le serveur local termine avec code système 1.
- Run CI `41655909006` est marqué `success` et vérifiait une réponse HTTP locale.
- HTTP 200 ne garantit pas le rendu WebView.
- La branche candidate contient `templates/`, `static/`, `android/`, `app.py` et `guards.py`.

### Non établi

- Exception Python exacte à l'origine du code 1.
- Échec éventuel à l'import, l'initialisation Flask/SQLite, au chargement d'un template, au binding du port ou à cause d'une dépendance native.
- Présence effective des ressources aux chemins utilisés après extraction Android.
- Compatibilité précise avec le modèle et la version Android du téléphone.

## Procédure impérative

### 1 — Preuves du crash

- Récupérer logcat Android du démarrage, filtré par package et processus Python.
- Collecter stdout/stderr et traceback Python complets, code de sortie et horodatages.

### 2 — Audit du paquet

- Inspecter l'APK exacte (APK Analyzer/unzip).
- Lister scripts Python, `templates/`, `static/`, dépendances et configuration.
- Comparer les chemins avec `BASE` dans `app.py`, le répertoire courant Android et les chemins d'extraction.
- Lire `rotation_server.py`, `MainActivity.java`, `app/build.gradle` et le workflow Android complet.

### 3 — Reproduction et isolation

- Démarrer à froid sur émulateur en collectant les logs avant toute requête HTTP.
- Tester import, initialisation DB, démarrage Flask, binding localhost, puis `/login`.
- Distinguer échec serveur et échec WebView.

### 4 — Correction et tests

- Corriger uniquement la cause démontrée par les logs.
- Faire échouer le smoke test si le processus serveur sort avec code non nul.
- Vérifier rendu WebView réel et ressources requises.
- Relancer tests Python, build APK, smoke test émulateur à froid et test d'affichage.

### 5 — Validation utilisateur

- Fournir une APK candidate après validation technique.
- Faire confirmer sur téléphone réel l'écran de connexion et la navigation de base.
- Ne pas fusionner PR #91 avant accord explicite.

## Branches connues

- `resimanage-2-work` : branche officielle.
- `work/resimanage-refonte-themes-gardes-2026-11-02` : branche de travail citée dans le suivi.
- `integration/resimanage-refonte-themes-2026-11-03` : branche candidate avec portage des sept thèmes et correctifs.
- PR #91 vers `resimanage-2-work`, ouverte/non fusionnée selon dernier état consigné.
- Le dépôt comprend aussi des branches historiques `backup/`, `baseline/`, `docs/`, `feature/`, `fix/`, `resimanage-2-*` et `ui/`. Comparer les commits et contenus avant toute décision; aucun nettoyage n'est autorisé par cette note.

## Liens

- PR #91 : https://github.com/samyrius/ResiManage/pull/91
- Run HTTP : https://github.com/samyrius/ResiManage/actions/runs/41655909006
- Run build précédent : https://github.com/samyrius/ResiManage/actions/runs/41647148965