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

## Relevé des branches — 3 novembre 2026


- Comparaison GitHub entre `resimanage-2-work` (base) et `integration/resimanage-refonte-themes-2026-11-03` (candidate) : statut `ahead`, candidate en avance de **110 commits**, **0 commit en retard** au moment du relevé. Base SHA `7e87d7f6d6d425336c3f17d72c5dabf962f3c89b`.
- Fichiers modifiés/ajoutés signalés par la comparaison : workflow Android et Windows, CI, registre, `android/app/build.gradle`, `MainActivity.java`, `app.py` (+531/-43), données de gardes `data/gardes_octobre_2026.json`, `guards.py` (nouveau), tests `test_app.py` et `test_guards.py`, sept CSS de thèmes, sept templates HTML et documents d'audit/fonctionnalité des gardes.
- Cette comparaison décrit précisément l'écart de la branche candidate par rapport à la branche officielle; elle ne signifie pas que tous les changements ont été testés sur téléphone ni qu'ils sont prêts à fusionner.
- Le dépôt expose également de nombreuses branches historiques et spécialisées (`backup/`, `baseline/`, `docs/`, `feature/`, `fix/`, `integration/`, `resimanage-2-*`, `ui/`). Leur contenu intégral n'a pas été copié dans ce registre : chaque branche doit être comparée à sa base et ses commits inspectés avant classement. Aucun nettoyage/suppression n'a été effectué.

##  Audit global du dépôt, des branches et des routes — 4 novembre 2026

### Périmètre et niveau de preuve

Audit statique effectué sur le dépôt GitHub à partir de l'inventaire des branches, des comparaisons GitHub, de la PR #91, des sources de la branche candidate, des routes Flask, du module Gardes, des schémas SQLite, des tests, des fichiers Android/Gradle et des workflows.

**Limite importante :** les 105 branches ont été inventoriées et comparées à la branche de référence, et les familles de branches ainsi que plusieurs branches représentatives ont été inspectées en profondeur. Cela ne signifie pas que chaque fichier et chaque commit de chacune des 105 branches a fait l'objet d'une lecture intégrale ligne par ligne. Les branches anciennes très divergentes doivent encore être examinées par lots avant tout cherry-pick ou suppression. Aucune branche n'a été modifiée ou supprimée pendant cet audit. Aucun test ni build n'a été relancé localement pendant cette inspection ; les nombres de tests ci-dessous sont des définitions de tests présentes dans les sources, pas un nouveau résultat d'exécution.

### Référence Git et gouvernance

- Dépôt : https://github.com/samyrius/ResiManage
- Branche officielle de travail définie pour le projet : `resimanage-2-work`, commit de base `7e87d7f6d6d425336c3f17d72c5dabf962f3c89b`.
- GitHub indique cependant `main` comme branche par défaut du dépôt. La branche par défaut GitHub et la branche de travail officielle du projet ne sont donc pas la même chose.
- L'API GitHub indique que `resimanage-2-work` n'est pas protégée et qu'aucun contrôle obligatoire n'est configuré. Risque de gouvernance : une poussée directe pourrait modifier la référence officielle sans garde-fou GitHub.
- PR #91 : https://github.com/samyrius/ResiManage/pull/91 — état ouvert, non fusionné ; base `resimanage-2-work` ; head `integration/resimanage-refonte-themes-2026-11-03` ; base SHA `7e87d7f6d6d425336c3f17d72c5dabf962f3c89b` ; head SHA `aefe539e298acf1782fdb09ed04864bbb5891243` ; 113 commits ; 31 fichiers ; +2437/-81.
- La PR #91 ne doit pas être fusionnée avant résolution de l'incident Android et validation des thèmes, conformément à la gouvernance déjà convenue.

### Inventaire des 105 branches

L'API de branches a renvoyé 100 noms sur la première page et 5 sur la seconde, soit 105 références :

- Sauvegardes / repères : `backup/resimanage-before-new-features-2026-11-01`, `backup/resimanage-reference-2026-10-28`, `baseline/resimanage-icon-confirmed`, `repere-avant-agents-2026-10-19`, `repere-resimanage2-2026-10-19`.
- Documentation / prototypes : `docs/resitrack-icon-concept-2026-10-14`, `prototype/verification-2026-10-13`.
- Fonctionnalités : `feature/profiles-admin-accounts`, `feature/resimanage-dual-official-progression-votes`, `feature/resimanage-leave-external-current-main`, `feature/resitrack-approved-branding-2026-10-14`, `feature/resitrack-branding`, `feature/resitrack-launcher-icon-no-cross`, `feature/resitrack-leave-external-rotation`, `feature/resitrack-mockup-navy-ui`, `feature/resitrack-vibrant-login`.
- Correctifs : `fix/android-password-autofill-launcher-icon`, `fix/custom-period-dates`, `fix/legacy-decision-year-scope`, `fix/legacy-decision-year-scope-v2`, `fix/mobile-scroll-resimanage2`, `fix/mobile-vertical-scroll`, `fix/resimanage-full-backup-and-export`, `fix/resimanage-icon-no-cross-on-current-main`, `fix/resimanage-leave-and-external-rotation-rules`, `fix/resimanage-login-brand-and-theme`, `fix/resimanage-remove-cross-like-ui-glyphs`, `fix/year-period-validation-smoke`.
- Intégration / branches générales : `integration/resimanage-refonte-themes-2026-11-03`, `main`.
- Livraisons : `release/resitrack-beautification-test`, `release/rotation-app-candidate`, `release/rotation-app-final`, `release/rotation-app-ready`, `release/rotation-app-tested`, `release/rotation-app-verified`.
- Anciennes versions / APK repères : `resimanage2-apk-baseline-20261020`, `resimanage2-apk-repere-2026-10-20`, `resimanage2-apk-repere-20261020`, `resimanage-1-backup`, `resimanage-1-photo-ui-candidate`.
- Série ResiManage 2 : `resimanage-2-active-progression-guard`, `resimanage-2-admin-id-validation`, `resimanage-2-apk-baseline-2026-10-19`, `resimanage-2-apk-baseline-build`, `resimanage-2-apk-candidate`, `resimanage-2-assignment-permission-guard`, `resimanage-2-capacity-input-validation`, `resimanage-2-completion-evidence-guard`, `resimanage-2-completion-evidence-guard-v2`, `resimanage-2-dems-future-date-guard`, `resimanage-2-dems-status-guard`, `resimanage-2-documented-history-import`, `resimanage-2-eligibility-guard`, `resimanage-2-exam-input-validation`, `resimanage-2-exam-record-stage-guard`, `resimanage-2-external-local-conflict-guard`, `resimanage-2-first-year-evaluation-guard`, `resimanage-2-history-future-date-guard`, `resimanage-2-history-future-date-guard-v2`, `resimanage-2-history-undated-future-guard`, `resimanage-2-history-validation-guard`, `resimanage-2-import-confirmation-recheck`, `resimanage-2-import-confirmation-recheck-v2`, `resimanage-2-import-confirmation-recheck-v3`, `resimanage-2-import-confirmation-recheck-v4`, `resimanage-2-import-year-validation`, `resimanage-2-inactive-terrain-eligibility`, `resimanage-2-navigation-redesign`, `resimanage-2-objective-input-validation`, `resimanage-2-objective-input-validation-v2`, `resimanage-2-objective-input-validation-v3`, `resimanage-2-password-strength-guard`, `resimanage-2-pending-assignment-revalidation`, `resimanage-2-period-completion-migration`, `resimanage-2-photo-picker-fix`, `resimanage-2-photo-picker-fix-clean`, `resimanage-2-photo-preview-fix`, `resimanage-2-photo-ui-port`, `resimanage-2-photo-ui-port-refresh`, `resimanage-2-profile-input-validation`, `resimanage-2-promotion-active-resident-guard`, `resimanage-2-promotion-active-resident-guard-v2`, `resimanage-2-promotion-state-guard`, `resimanage-2-repeat-eligibility-cross-year`, `resimanage-2-repeat-eligibility-cross-year-v2`, `resimanage-2-requirements-completion`, `resimanage-2-resident-input-validation`, `resimanage-2-session-revocation-guard`, `resimanage-2-terrain-classification-history-guard`, `resimanage-2-terrain-classification-migration`, `resimanage-2-themes-academic-year-2026-10-21`, `resimanage-2-verification-status-archive`, `resimanage-2-work`.
- Sécurité : `security/harden-authentication`, `security/resimanage-csrf-and-official-admins`.
- Tests : `test/resimanage2-latest-regression-suite`, `test/resimanage2-photo-sync-idempotency-guard`, `test/resimanage-sync-client-directory`.
- Interface : `ui/mobile-clean-bottom-nav`, `ui/mobile-scroll-fix-from-baseline`, `ui/seven-isolated-theme-templates`.
- Travaux : `work/resimanage-branding-2026-10-15`, `work/resimanage-navy-ui-2026-10-15`, `work/resimanage-refonte-themes-gardes-2026-11-02`.

### Comparaisons de branches représentatives

Comparaisons effectuées par rapport au SHA de `resimanage-2-work`. « En avance / en retard » décrit l'historique Git, pas la qualité fonctionnelle :

| Branche | En avance | En retard | Lecture |
|---|---:|---:|---|
| `integration/resimanage-refonte-themes-2026-11-03` | 113 | 0 | Candidate de PR #91 |
| `work/resimanage-refonte-themes-gardes-2026-11-02` | 73 | 0 | Ancêtre de travail de la candidate |
| `ui/seven-isolated-theme-templates` | 68 | 0 | Base intermédiaire des thèmes |
| `backup/resimanage-before-new-features-2026-11-01` | 49 | 0 | Sauvegarde, ne pas prendre comme version de livraison |
| `main` | 4 | 648 | Branche par défaut GitHub très divergente et ancienne |
| `release/rotation-app-final` | 58 | 750 | Divergente, pas un successeur direct |
| `release/rotation-app-tested` | 63 | 750 | Divergente, pas un successeur direct |
| `release/rotation-app-verified` | 121 | 750 | Divergente, contient une ligne Android distincte |
| `security/harden-authentication` | 37 | 750 | Ancienne ligne de sécurité divergente |
| `security/resimanage-csrf-and-official-admins` | 4 | 651 | Correctifs ciblés sur une base plus ancienne |
| `feature/resimanage-dual-official-progression-votes` | 3 | 650 | Fonctionnalité ciblée sur une base plus ancienne |
| `feature/resimanage-leave-external-current-main` | 3 | 655 | Congés / stages externes, base divergente |
| `fix/custom-period-dates` | 4 | 20 | Correctif ciblé, base plus proche mais divergente |
| `fix/mobile-scroll-resimanage2` | 2 | 19 | Correctif ciblé, base plus proche mais divergente |
| `fix/resimanage-full-backup-and-export` | 5 | 649 | Correctif de sauvegarde sur ancienne ligne |
| `resimanage-2-session-revocation-guard` | 0 | 586 | Ancêtre déjà dépassé par la référence officielle |
| `resimanage-2-import-confirmation-recheck-v4` | 0 | 553 | Ancêtre déjà dépassé par la référence officielle |
| `resimanage-2-requirements-completion` | 14 | 636 | Ligne historique divergente |

Les comparaisons montrent que les branches `release/*`, `security/*`, plusieurs `feature/*` et correctifs plus anciens ne doivent pas être fusionnés directement. Leur nom décrit l'intention, pas leur compatibilité avec la base actuelle. Les changements utiles doivent être identifiés au niveau des commits/fichiers et portés avec tests ciblés.

### Architecture et routes recensées
- `app.py` : 3 602 lignes au SHA inspecté ; 44 routes Flask déclarées directement.
- `guards.py` : 402 lignes ; 4 routes supplémentaires enregistrées dynamiquement : `/guards`, `/guards/mapping`, `/guards/source/<source_id>`, `/guards/export.csv`. Total recensé : 48 routes applicatives, sans compter les routes statiques Flask.
- Principaux groupes : authentification/inscription/langue ; accueil et résidents ; services, capacités, périodes, tableau de rotation, affectations et historique ; décisions, objectifs, examens et DEMS ; utilisateurs, paramètres, audit, corbeille, export, sauvegarde/restauration ; congés et stages externes ; synchronisation appareil/API ; gardes.
- Routes API sync : `/api/sync/v1/status`, `/bootstrap`, `/pull`, `/push`, transfert photo GET/PUT.
- Les routes métier sont majoritairement protégées par `guard()` ou `super_guard()`. Les POST navigateur passent par un contrôle CSRF global ; les POST API bearer sont exemptés du CSRF de session et contrôlés par le jeton d'appareil.
- Les routes de consultation de source de garde et d'export CSV demandent une session authentifiée mais pas explicitement le rôle Super Admin. C'est un choix d'accès à confirmer, surtout si les plannings sont considérés comme données internes.
- Le modèle de données est initialisé par `init()` au premier accès, avec `CREATE TABLE IF NOT EXISTS` et `ensure_column`. Pas de framework de migrations versionnées observé dans le code inspecté : les évolutions de schéma sont intégrées au démarrage. Il faut maintenir des tests de migration sur copies de bases historiques.

### Sécurité, comptes et données

Éléments positifs observés dans la candidate :
- mots de passe PBKDF2-HMAC-SHA256 avec 310 000 itérations et comparaison constante ; mise à niveau d'anciens hash à la connexion ;
- jeton CSRF pour les POST navigateur ;
- le rôle actif est relu depuis la base lors de la validation de session ;
- jetons de synchronisation stockés sous forme de hash SHA-256, appareils révocables, mode lecture seule/lecture-écriture, refus de la synchronisation distante en HTTP non sécurisé ;
- sauvegarde SQLite cohérente, archive ZIP avec base et photos ; restauration contrôlant l'intégrité SQLite, les chemins ZIP et les tailles, avec sauvegarde préalable de la base courante.

Risques / limites :
- la branche officielle n'est pas protégée dans GitHub ; aucune vérification obligatoire n'est configurée ;
- `/logout` est un GET qui modifie l'état de session ; à convertir en POST protégé CSRF ;
- le code comporte deux mécanismes `before_request` de purge de la corbeille : un dans `boot()` une fois par jour et un autre à chaque requête. Le second parcourt les éléments de corbeille et effectue la purge des photos. Cette duplication augmente le travail SQLite sur chaque requête et crée deux implémentations de la même règle ; les fusionner dans un seul mécanisme testé ;
- le contrôle de sécurité effectué ici est une revue statique, pas un test d'intrusion ni une certification.

### Base SQLite et synchronisation

- Tables métier visibles : résidents, services, périodes, capacités, affectations, historique, décisions, journal d'audit, paramètres, examens, objectifs, archive DEMS, votes, utilisateurs, inscriptions en attente, aperçus d'import, congés, stages externes, corbeille ; tables sync pour journal de changements, versions de lignes, appareils, opérations appliquées et photos.
- La synchronisation est annoncée dans l'interface comme manuelle, dépendante d'un serveur central HTTPS/VPN et non continue en arrière-plan. Le texte de l'application déconseille son utilisation avec des données réelles avant la fin des tests fonctionnels et de sécurité.
- `_SYNC_ENTITY_FIELDS` ne comprend pas les tables Gardes (`guard_sources`, `guard_assignments`), ni les votes de promotion/DEMS, ni l'archive DEMS, ni les comptes/utilisateurs et plusieurs tables administratives. Le journal sync ne représente donc pas toute la base ; la synchronisation ne doit pas être décrite comme une réplication complète.
- Les documents de synchronisation signalent aussi l'absence de résolution interactive des conflits et de file hors connexion complète. Le premier appairage exige une base locale vide pour éviter les collisions d'identifiants.
- Les changements de schéma, les imports et les restaurations doivent être testés en présence des déclencheurs de journalisation sync afin d'éviter les échos et les journaux incohérents.

### Module Gardes

- Le JSON source `data/gardes_octobre_2026.json` contient 31 journées ; les tests attendent 233 affectations et 70 libellés distincts.
- Le premier import crée un enregistrement source avec SHA-256 et conserve les libellés bruts ; les 233 affectations importées restent non identifiées au départ. Le rapprochement est manuel et peut appliquer une correspondance validée à toutes les occurrences d'un libellé.
- Les résidents admissibles sont actifs, locaux, années 1 à 4, non présents dans l'archive DEMS. Cette exclusion est cohérente avec l'exigence de ne pas réaffecter les anciens diplômés.
- Les tests de garde contiennent 8 tests définis : import unique, règles d'horaires week-end, mois futur vide, ajout manuel, correspondance manuelle, exclusion DEMS, week-ends et export CSV.
- Limite fonctionnelle confirmée par le code et le test `test_future_month_is_blank_and_never_autogenerated` : aucun générateur de roulement futur n'existe ; novembre 2026 reste vide. L'écran permet ajout et suppression, mais pas l'édition complète/remplacement d'une affectation existante depuis le calendrier. Pas de gestion des jours fériés observée. La génération automatique, la préservation des corrections manuelles lors d'une régénération et les règles de pondération restent à développer/valider.

### Thèmes et interface

- Sept templates existent et chargent sept feuilles CSS dédiées : Crystal 3D, Aurore boréale, Émeraude, Futuriste, Luxe élégant, Naturel moderne et Rubis.
- Les sept templates ont le même squelette DOM recensé (mêmes nombres de balises et mêmes classes de navigation/layout : 147 balises dans l'échantillon sans les styles, 49 attributs de classe). Les fichiers HTML sont distincts, mais la structure des écrans est pratiquement clonée.
- `crystal3d.css` ne contient qu'un import de `common.css`; les autres CSS importent également la feuille commune et ajoutent des surcharges relativement courtes. Le changement de thème est donc principalement visuel/palette/effets, pas un changement de contenant ou de disposition complète. Cela ne satisfait pas encore l'objectif de comparer de véritables architectures d'interface différentes.
- Les sept thèmes n'ont pas été rendus et comparés visuellement dans un navigateur/appareil pendant cet audit. La séparation par attribut `data-theme-template` est présente, mais le comportement réel doit encore être testé sur chaque thème, notamment mobile, menus, scroll et barre inférieure.

### Android et CI

- Gradle copie dans le bundle Python Android `app.py`, `guards.py`, le JSON de garde, `static/` et `templates/`. `rotation_server.py` place la base et les uploads dans le répertoire privé fourni par Android et démarre Flask sur `127.0.0.1:5000`.
- Dans `MainActivity.java`, l'exception du thread Python est ramenée à `error.getMessage()` ; le traceback Python complet, stdout/stderr et le code de sortie ne sont pas exposés. Le contrôle du serveur attend une réponse HTTP et finit par afficher une erreur générique. Cela ne permet pas d'établir la cause du `System exit 1`.
- Le workflow Android compile l'APK, installe et lance l'application sur émulateur, vérifie l'activité et interroge `/login` via port-forward. Il recherche quelques erreurs dans logcat et dépose une capture, mais ne vérifie pas automatiquement que le WebView affiche effectivement une page de connexion lisible. Le succès CI antérieur ne prouve donc pas le rendu visuel ni le fonctionnement sur le téléphone de l'utilisateur.
- Incident utilisateur `System exit 1` : toujours OUVERT / BLOQUANT ; cause racine inconnue. Ne pas produire une nouvelle APK de validation utilisateur avant collecte du traceback/logcat et amélioration du smoke-test.
- Le bouton Retour système Android utilise `webView.canGoBack()` puis `super.onBackPressed()`. Il n'y a pas de confirmation explicite de sortie depuis l'accueil dans ce code. Le comportement demandé (retour interne, aucune sortie vers l'ancien site, confirmation depuis l'accueil) reste à implémenter et tester.

### Tests présents et couverture

- `tests/test_app.py` : 4 478 lignes et 164 fonctions de test.
- `tests/test_guards.py` : 148 lignes et 8 fonctions de test.
- Total recensé : 172 définitions de tests dans ces deux fichiers. Elles couvrent notamment affectations, capacité, progression, DEMS, congés, stages externes, validation des imports, CSRF, synchronisation, migrations et quelques comportements Android/UI.
- Le compte 172 est un comptage statique des fonctions présentes. Le résultat historique 172/172 réussi est antérieur ; il n'a pas été réexécuté au cours de cet audit.
- Les tests ne remplacent pas les tests physiques Android, l'exercice réel de restauration, la validation des 7 thèmes, les règles de génération des gardes inexistantes, ni les tests de migration sur un corpus de bases historiques.

### Plan de remédiation priorisé

1. **P0 Android :** ajouter journalisation structurée et traceback Python complet côté Java/Chaquopy ; capturer logcat, stdout/stderr, code de sortie ; reproduire sur émulateur à froid ; valider le rendu WebView et le téléphone physique. Garder l'incident ouvert tant que non résolu.
2. **P0 Gouvernance :** protéger `resimanage-2-work`, exiger CI Python et Android, interdire les poussées directes non contrôlées ; garder PR #91 non fusionnée jusqu'à validation et accord utilisateur.
3. **P1 Corbeille :** fusionner les deux purges `before_request` en un mécanisme unique avec test de rétention et suppression photo, sans balayage complet à chaque requête.
4. **P1 Gardes :** spécifier puis implémenter générateur de roulement, édition/remplacement, verrouillage des corrections manuelles, jours fériés algériens et règles de pondération approuvées ; ajouter tests de répartition/équité.
5. **P1 Synchronisation :** décider explicitement si les Gardes et votes doivent être synchronisés ; documenter la matrice des entités, compléter les tables si requis, tester les conflits, l'appairage et la reprise hors ligne.
6. **P1 Thèmes :** concevoir de vrais squelettes HTML/layout différents, pas seulement des CSS de palette ; tester chacun sur téléphone.
7. **P2 Sécurité :** passer `/logout` en POST CSRF, statuer sur les droits de lecture source/export des gardes, effectuer une revue dynamique et vérifier les opérations de sauvegarde/restauration.
8. **P2 Migrations / tests :** formaliser les migrations SQLite versionnées, exécuter les 172 tests et ajouter un corpus de bases antérieures, tests Android/WebView et tests de non-régression par thème.

### Conclusion de l'audit

L'audit statique du dépôt, de l'inventaire des branches, de la candidate, des routes, du schéma, de la synchronisation, des thèmes, du module Gardes et de la chaîne Android est consigné. Il confirme que la candidate rassemble un volume important de travail utile, mais qu'elle n'est pas prête à être fusionnée : Android reste bloquant, les thèmes ne sont pas encore de véritables layouts distincts, le roulement automatique des gardes manque, la synchronisation est partielle et la branche officielle n'est pas protégée.

La revue exhaustive ligne par ligne de chaque commit/fichier de toutes les branches historiques reste un lot distinct avant nettoyage ou cherry-pick. Cette limite est explicite afin de ne pas présenter une comparaison Git comme une lecture intégrale de 105 historiques.


## Décision du 4 novembre 2026 — Revue exhaustive des commits de toutes les branches

### Demande et objectif
L'utilisateur demande que l'ensemble des éléments de cette discussion soit enregistré. Il souhaite une revue de tous les commits de toutes les branches du dépôt afin de retrouver les fonctionnalités, corrections et améliorations utiles, sans perdre de travail historique et sans réintroduire de régressions.

### Estimation de durée
Estimation préliminaire : **3 à 7 jours de travail concentré**, à réviser après mesure du nombre réel de commits uniques et du volume des diffs. Cette estimation n'est pas une durée garantie ni le résultat d'un audit déjà exécuté.

Répartition indicative :
- 2 à 4 heures : inventorier les commits de toutes les branches, calculer les commits uniques et repérer les doublons ;
- 1 à 3 jours : examiner les modifications uniques, fichiers et diffs ;
- 1 à 2 jours : comparer les branches divergentes et repérer fonctionnalités perdues, améliorations et conflits ;
- 1 à 2 jours : vérifier les changements importants, tests associés et risques de régression.

### Méthode de travail retenue
1. Établir l'inventaire complet des branches et des commits accessibles, avec SHA et relations d'ascendance.
2. Dédupliquer les commits communs entre branches ; ne pas recompter comme travaux différents les mêmes commits partagés.
3. Examiner les commits uniques et leurs diffs fichier par fichier, en regroupant les changements par domaine fonctionnel.
4. Comparer les changements avec la branche de référence `resimanage-2-work` et la candidate `integration/resimanage-refonte-themes-2026-11-03`.
5. Classer chaque changement : à conserver, déjà intégré, obsolète, remplacé, à corriger, dangereux ou nécessitant une décision métier.
6. Pour chaque amélioration candidate, identifier dépendances, migrations, impacts de données et tests nécessaires.
7. Produire un rapport traçable : branche, SHA, fichiers touchés, comportement apporté, décision et preuve de validation.
8. Porter uniquement les changements utiles sur une branche candidate dédiée, puis exécuter les tests ciblés et de régression.

### Garde-fous
- Ne pas fusionner la PR #91 sans accord explicite.
- Ne pas modifier la branche officielle `resimanage-2-work` pendant cette revue.
- Ne supprimer aucune branche et ne réécrire aucun historique.
- Ne pas cherry-pick en masse les branches divergentes.
- Ne pas prétendre que les 105 branches ont déjà été lues intégralement : jusqu'ici elles ont été inventoriées et comparées, mais la revue exhaustive de tous les commits et de tous les fichiers reste à faire.
- L'audit doit être fondé sur les diffs et les preuves, pas seulement sur les messages de commit ou les noms de branches.

### Prochaine action
Commencer par mesurer précisément le nombre de commits uniques sur l'ensemble des 105 branches recensées, puis établir l'ordre de revue par domaines et par risque. L'estimation de 3 à 7 jours sera affinée à partir de ce comptage.


## Correctifs de navigation réappliqués — 4 novembre 2026

L'utilisateur précise que **toutes les observations, demandes de correction, corrections réalisées et résultats de validation doivent être consignés systématiquement dans ce carnet de route**. Cette règle s'applique à la suite du projet : ne pas considérer un correctif comme terminé dans le suivi tant que son entrée documentaire n'a pas été ajoutée sur la branche candidate.

### 1. Barre de navigation fixe en bas sur mobile

- **Régression observée :** la barre contenant les icônes de menu n'était plus fixe au bas de l'écran.
- **Correction portée :** dans `static/themes/common.css`, rétablissement d'une barre mobile fixe, avec cinq colonnes, prise en compte de la zone de sécurité inférieure (`safe-area-inset-bottom`), cibles tactiles et menus déroulants positionnés au-dessus de la barre.
- **Tests ajoutés :** assertions dans `tests/test_app.py` pour vérifier le positionnement fixe, la zone de sécurité, les cinq colonnes et le positionnement du sous-menu.
- **Commit CSS :** `e363f4e` (préfixe court communiqué lors du suivi).
- **Commit tests :** `7a7a2030fceeda11cddcb51068affc7f7f3d9535`.
- **Validation :** les workflows Python et Android ont été déclenchés après ce correctif, mais leur résultat final n'est pas établi dans le relevé disponible. Ne pas déclarer le correctif validé par CI avant vérification des runs.

### 2. Flèche « page précédente »

- **Régression observée :** la flèche de retour vers la page précédente avait disparu visuellement.
- **Diagnostic :** le lien `.rt-back-link` et son balisage dans `app.py` étaient toujours présents ; le défaut a été traité comme un problème de visibilité/priorité CSS.
- **Correction portée :** surcharge dans `static/themes/common.css` pour garantir l'affichage du contrôle au-dessus des thèmes et de la navigation mobile : position fixe, visibilité/opacité forcées, zone tactile 44 × 44 px, contraste renforcé, prise en charge RTL et focus clavier.
- **Tests ajoutés :** assertions dans `tests/test_app.py` sur les règles CSS et sur la présence du lien dans la réponse HTML d'une page intérieure.
- **Commit CSS :** `f5a3b8ab7fadef966ac6b905752ce0ce8b778a27`.
- **Commit de test initial :** `fd6735aa157fe24f971ae307b8c76969bdf140f8` (assertion d'ordre corrigée dans le commit suivant).
- **Commit de test corrigé / HEAD candidat au relevé :** `0c1f23c5342ef3fbcbbbcd80178cc7d6726a0ba2`.
- **Validation :** le contenu CSS, le lien HTML et le test corrigé ont été relus sur la branche candidate. Aucun résultat de workflow associé au HEAD `0c1f23c` n'était encore disponible au dernier contrôle ; tests Python/Android à confirmer.

### Règle de suivi

Pour chaque prochaine observation : consigner le symptôme rapporté, le diagnostic et son niveau de certitude, les fichiers touchés, la correction, les tests ajoutés/exécutés, les commits et le statut CI. Distinguer clairement « appliqué », « testé », « validé CI » et « confirmé par l'utilisateur sur appareil ». Ne jamais transformer un correctif en validation acquise sans preuve.


## Séparation autonome des feuilles CSS des thèmes — 4 novembre 2026

### DemandeAprès la séparation des sept pages HTML, l'utilisateur demande de terminer la séparation des CSS afin que chaque thème dispose de sa propre feuille de styles et puisse évoluer indépendamment.

### État initial constaté
Les sept templates HTML existaient déjà et chargeaient chacun un fichier CSS dédié. Cependant, les feuilles thématiques importaient `static/themes/common.css`. Les règles de structure, composants, formulaires, tableaux, navigation, responsive et correctifs communs restaient mutualisées : la séparation CSS était nominale, pas autonome.

### Changement appliqué
Chaque feuille `static/themes/<theme>.css` embarque désormais directement la base CSS précédemment partagée, puis conserve sa propre couche de styles et de layout. Les sept feuilles ne chargent plus `common.css` par import. Les dispositions thématiques existantes sont conservées : Crystal 3D (base), Aurore boréale (grille), Émeraude (rail latéral), Futuriste (bandeau horizontal), Luxe élégant (navigation à droite), Naturel moderne (grille aérée), Rubis (ruban horizontal). Les correctifs de barre inférieure mobile fixe et de flèche de retour sont présents dans chaque CSS autonome. Une surcharge mobile finale propre à chaque thème empêche les règles de disposition des variantes d'écraser le contrat de barre fixe. `common.css` est conservé comme référence, mais n'est plus une dépendance au chargement des thèmes.

### Tests
Le test de navigation existant lit désormais le CSS autonome Crystal 3D. Un test paramétré vérifie les sept thèmes : absence d'import, présence des styles communs essentiels, cohérence template/CSS et présence des sélecteurs spécifiques aux six variantes. Les tests n'ont pas encore été exécutés ; le résultat CI sera ajouté après les workflows.

### Fichiers concernés
Les sept fichiers `static/themes/*.css` et `tests/test_app.py`.

### Validation restante
Les tests statiques ne remplacent pas le contrôle visuel des sept thèmes sur navigateur et Android : menus, défilement, navigation fixe, formulaires et tableaux restent à vérifier. Aucune fusion de PR n'est autorisée par ce changement.


### CI : réparation du lien de retour dans les templates actifs — 4 novembre 2026

Le premier workflow Python a mis en évidence deux points dans les tests :
- plusieurs tests historiques utilisaient encore le helper `read_common_theme_css()`. Un alias de compatibilité a été conservé ; il lit maintenant la feuille autonome Crystal 3D.
- le lien de retour existait dans une ancienne chaîne HTML de `app.py`, mais cette chaîne n'est pas le template effectivement rendu par la nouvelle architecture à sept templates. Le lien n'apparaissait donc pas dans la réponse HTML réelle.

Le lien conditionnel « page précédente » a été ajouté directement dans chacun des sept templates actifs, juste après `</head>`. Le test de navigation vérifie désormais ce balisage réellement rendu sur une page intérieure. Ce correctif rétablit le comportement demandé précédemment et évite de se fier à une chaîne HTML non utilisée.


### Préparation de l'APK de test — 4 novembre 2026

- **Demande :** produire une APK Android installable pour tester la version candidate.
- **Blocage constaté :** les workflows Python et Android associés au commit précédent ont échoué dans le job de tests Python : 173 tests réussis et 7 échecs, tous sur l'assertion qui cherchait une chaîne CSS compacte exacte. Le CSS réel applique bien le sélecteur de navigation mobile, mais le bloc est formaté sur plusieurs lignes ; l'assertion ne tolérait pas cet espacement.
- **Correction appliquée :** remplacement de la comparaison textuelle stricte par une expression régulière qui accepte les espaces et retours à la ligne tout en vérifiant le sélecteur du thème et la déclaration `position:fixed!important`. Aucun CSS de production n'a été modifié pour masquer l'échec.
- **Commits de correction :** `fed26bd026d4881caa35d67526865e1a7b75edc7` puis `c94d48078c2d6b51702f34459465a9236b5d2b8c` (correction de l'échappement de l'expression régulière).
- **Validation en cours :** les workflows déclenchés sur la PR #91 doivent être vérifiés sur le HEAD exact `c94d480`. Le run Android précédent avait ignoré les jobs de compilation APK et d'émulateur, car le job Python requis avait échoué ; aucun artefact APK n'avait donc été produit à ce stade.
- **Règle :** ne fournir un lien APK qu'après confirmation de la réussite de la compilation et de la présence d'un artefact téléchargeable. Ne pas confondre compilation APK, test sur émulateur et essai sur téléphone physique.


### Régression du défilement mobile et de la barre d'icônes — 4 novembre 2026

- **Référence utilisateur :** APK Android générée le 1er novembre 2026 à 14:39 UTC (workflow `41317007135`), commit source `b01cf32d75bf50808afa1cb8e11623e70ba562a5`, artefact `13088310002` (`resimanage2-debug-apk`, SHA-256 `799bc46a5be8c7dbce323de1470ee4c0a5f221d14c8b5b74992fc0f96a561422`).
- **Constat de comparaison :** le code de référence neutralisait sur mobile `transform`, `filter`, `perspective` et `transform-style` sur `body` et `.rt-app-shell`, rétablissait le défilement vertical de `html`, fixait `.main-nav` au bas du viewport et masquait les libellés pour n'afficher que les cinq icônes. Le CSS actuel des thèmes avait remplacé ce contrat par une barre avec libellés visibles et ne neutralisait plus complètement les transformations 3D du conteneur. Ces différences expliquent la régression observée : barre qui accompagne le défilement et retour des boutons textuels.
- **Correctif appliqué :** réintégration d'un contrat mobile final, après les couches de styles propres à chaque thème, dans les sept feuilles CSS autonomes et dans `common.css`. Le contrat restaure le défilement vertical, supprime les transformations susceptibles de faire défiler un élément fixe avec son parent, fixe la navigation au bord inférieur, masque les libellés, conserve les icônes, et affiche les sous-menus en surimpression au-dessus de la barre. Le padding inférieur réserve la place du contenu et prend en compte la zone de sécurité Android.
- **Tests ajoutés :** chaque thème doit contenir les règles de défilement vertical, les neutralisations 3D, le masquage des libellés, l'affichage des icônes et le sous-menu superposé.
- **Portée :** aucun changement de logique métier ni de code Android natif ; le fichier `MainActivity.java` est identique à celui de la référence du 1er novembre. La correction porte sur les CSS des thèmes actifs.
- **Validation :** les workflows Python et Android doivent être vérifiés sur le commit résultant. Le succès de compilation APK et les essais sur appareil ne sont pas présumés tant que les workflows correspondants n'ont pas terminé.

### Résultat de compilation et de validation Android — 4 novembre 2026

- **Commit testé :** `51910a0b91e8ea1eb47174a90320d5a4b5aa3c56` sur `integration/resimanage-refonte-themes-2026-11-03`.
- **Tests Python :** workflow `41834000015`, job `test` terminé avec succès ; installation des dépendances et étape `Run tests` terminées avec `success`.
- **Workflow Android :** `41834000425`, état global `completed / success`.
- **Régression Python Android :** job `python-regression` réussi.
- **Compilation APK :** job `build-debug-apk` réussi ; étape `Build debug APK` et téléversement de l'artefact réussis.
- **Émulateur Android :** job `android-emulator-smoke` réussi ; installation/lancement de l'application, contrôle du serveur et téléversement des preuves terminés avec succès.
- **Artefact APK :** `resimanage2-debug-apk`, ID `13324622470`, taille 38 541 127 octets, SHA-256 `94fb7cd45bf53c497362a056759584b6a8d0be49c7edfa94d89565ca13f71d07`, disponible jusqu'au 18 novembre 2026.
- **Preuves émulateur :** artefact `resimanage2-android-emulator-evidence`, ID `13324937456`, SHA-256 `e88613582d9b334d3084884b778ebacbf678437f2bf243f2b792c1543d3d6ecc`.
- **Lien du workflow et de ses artefacts :** https://github.com/samyrius/ResiManage/actions/runs/41834000425
- **Conclusion :** la compilation est validée et le smoke test sur émulateur est réussi pour ce commit. Cela ne remplace pas encore la vérification sur le téléphone physique de l'utilisateur, en particulier du défilement dans plusieurs écrans et de la barre d'icônes fixe.
- **Gouvernance :** PR #91 reste ouverte et non fusionnée ; aucune modification de `resimanage-2-work`.


### Navigation mobile : icônes seules, sous-menus empilés et retour conditionnel — 4 novembre 2026

- **Observations rapportées après installation :** les libellés textuels réapparaissaient sous les icônes de la barre fixe ; les icônes de navigation manquaient de relief/couleur ; l'ouverture d'une catégorie fermait la précédente ou superposait son sous-menu ; la navigation vers une rubrique refermait les catégories déjà ouvertes ; la flèche Retour apparaissait également sur l'écran extérieur de connexion.
- **Diagnostic confirmé dans le code :**
  - les sept templates HTML utilisaient des pictogrammes monochromes et contenaient un script qui fermait explicitement tous les groupes après chaque navigation ;
  - un ancien écouteur global fermait les autres éléments `details` à chaque ouverture ;
  - les sous-menus partageaient le même point d'ancrage CSS au-dessus de la barre fixe, donc plusieurs menus ouverts se recouvraient ;
  - la condition du lien Retour ne vérifiait que l'URL et pas l'état authentifié, ce qui autorisait son affichage sur les écrans extérieurs comme `/login`.
- **Corrections appliquées sur les sept thèmes :**
  - remplacement des cinq glyphes de navigation par des pictogrammes emoji colorés (accueil, résidents, planning, rapports, paramètres) ; ajout d'ombres et de relief CSS ;
  - masquage explicite de tous les libellés de la barre mobile, y compris du libellé Accueil ajouté par pseudo-élément ;
  - suppression de la fermeture automatique des autres groupes ; attribution de clés stables aux quatre catégories ;
  - mémorisation de l'ordre des catégories ouvertes dans `sessionStorage`, restauration après navigation, et calcul d'un décalage vertical cumulatif afin que chaque nouveau sous-menu apparaisse au-dessus du précédent sans le recouvrir ;
  - affichage du lien Retour uniquement si une session utilisateur est authentifiée et si la page n'est pas la racine.
- **Fichiers modifiés :** les sept `templates/themes/*.html`, les sept `static/themes/*.css`, `tests/test_app.py`.
- **Tests de régression ajoutés :** présence des clés de groupes, pictogrammes colorés, persistance des catégories, empilement CSS et masquage des libellés dans chaque thème ; absence du lien Retour sur l'écran de connexion.
- **Validation :** modifications appliquées sur la branche candidate. Les workflows Python et Android doivent encore être exécutés sur le HEAD résultant. Aucun test sur téléphone physique n'est encore confirmé.
- **Gouvernance :** PR #91 reste ouverte et non fusionnée ; la branche officielle `resimanage-2-work` n'a pas été modifiée.


### État CI après correctif de navigation — 4 novembre 2026

- **HEAD :** `f6778cb8bf37a0eb125c294a39ff38983b72977b`.
- **Tests Python :** workflow `41837659968` terminé avec succès ; étape `Run tests` réussie.
- **Régression Python du workflow Android :** dans le workflow `41837660235`, job `python-regression` terminé avec succès.
- **Compilation Android :** job `build-debug-apk` encore en cours au dernier contrôle ; l'installation du SDK Android était en cours. Aucun artefact APK n'était encore disponible à ce contrôle.
- **Émulateur :** en attente de la réussite du job de compilation.
- **Conclusion provisoire :** correctif couvert par les tests Python réussis ; ne pas annoncer une APK disponible ni un smoke test Android avant la fin du workflow.


### Résultat de compilation APK après corrections de navigation — 4 novembre 2026

- **Commit source compilé :** `305f2843fb62fd107adda87ef78c715dd5803d1a` (inclut les corrections des sept thèmes et les tests de régression).
- **Tests Python :** workflow `41838031034` terminé avec succès ; job `test` réussi.
- **Build Android :** workflow `41838031211`, job `build-debug-apk` terminé avec succès ; étape `Build debug APK` réussie.
- **Artefact généré :** `resimanage2-debug-apk`, ID `13325938987`, taille `38,552,051` octets ; non expiré au moment du contrôle.
- **Émulateur Android :** job `android-emulator-smoke` toujours en cours au dernier contrôle ; l'étape `Run app on Android emulator` n'avait pas encore rendu son résultat. Ne pas annoncer le smoke test comme réussi avant sa conclusion.
- **Lien de suivi et téléchargement de l'artefact :** https://github.com/samyrius/ResiManage/actions/runs/41838031211
- **Vérification sur téléphone physique :** à effectuer après installation de l'APK.


## Ajustement de la navigation mobile et des retours visuels — 4 novembre 2026

### Observations de l'utilisateur
- La flèche « page précédente » apparaît encore sur l'interface extérieure.
- Les cinq commandes fixes du bas doivent afficher un libellé court, sans débordement de leur bouton.
- Les sous-menus se recouvrent ou passent derrière d'autres menus selon le sens d'ouverture ; un seul doit rester ouvert, toujours au premier plan.
- Les raccourcis du tableau de bord semblent parfois ramener visuellement vers la barre fixe au lieu de présenter la page de destination.
- Les messages flash s'affichent dans le haut du document et obligent à remonter la page pour les lire.
- L'utilisateur demande un rendu 3D plus marqué et une animation tactile crédible des icônes.

### Diagnostic dans la candidate
- Les templates conservaient un mécanisme d'empilement multi-menus avec état sauvegardé sous forme de liste ; ce comportement contredisait la règle désormais demandée d'un seul sous-menu actif.
- Les styles mobiles masquaient les libellés de la barre fixe et certaines couches CSS de thème pouvaient replacer les sous-menus dans le flux normal.
- Les raccourcis du tableau de bord possèdent des destinations explicites (/residents, /assign, /rotation-board, /terrains, /import, /leave, /external-rotations, /guards). Le comportement de restauration de défilement pouvait néanmoins conserver une position précédente ; un retour explicite en haut est maintenant demandé pour ces liens.
- Le conteneur global des messages flash était rendu avant le contenu de page, sans positionnement dans le viewport.

### Correctifs appliqués sur les sept thèmes
- Dans les sept templates : ouverture exclusive d'un seul groupe de navigation ; fermeture des autres à l'ouverture ; conservation/restauration d'une seule clé de menu ; le menu actif reçoit un niveau d'affichage supérieur.
- Dans les sept CSS : barre mobile en cinq colonnes avec pictogramme et libellé compact, texte tronqué proprement si nécessaire, sélecteur de langue masqué dans la barre fixe, boutons avec ombrage multicouche, relief, et enfoncement (translateY/scale) à l'appui.
- Dans les sept CSS : sous-menu en panneau fixe au-dessus de la barre, largeur disponible, défilement interne et z-index élevé ; son positionnement ne dépend plus du sens gauche-droite ou droite-gauche.
- Dans les sept templates : les raccourcis du tableau de bord demandent une restauration de défilement à zéro lors de la navigation vers leur vraie destination.
- Dans les sept templates : exclusion explicite des pages /login et /register pour le lien de retour, en plus de la racine.
- Dans les sept CSS : les messages flash deviennent des notifications visibles dans le viewport courant, sans exiger de remonter au début du document.

### Outil 3D
Le catalogue de capacités disponibles comprend un workflow de modélisation Blender/Contour3D. Il est destiné à créer ou modifier des objets 3D natifs ; il ne constitue pas une bibliothèque d'icônes d'interface directement branchée à l'application. Pour cette correction, le relief et l'animation d'appui sont réalisés en CSS sur les pictogrammes/SVG existants, afin de conserver des boutons légers, accessibles et réactifs. Aucun fichier Blender ni nouvel asset 3D externe n'a été créé.

### Fichiers et tests
- Sept templates templates/themes/*.html.
- Sept feuilles static/themes/*.css.
- tests/test_app.py : assertions mises à jour pour l'unicité du sous-menu, les libellés compacts, le panneau au premier plan et les notifications dans le viewport.
- Les destinations des huit raccourcis du tableau de bord sont conservées ; leur navigation doit être vérifiée par les tests et sur appareil.

### Statut de validation
- Modifications de code appliquées sur la branche candidate uniquement.
- Tests locaux non exécutés via le connecteur GitHub ; le workflow CI doit être contrôlé sur le HEAD final.
- Vérification visuelle sur téléphone physique encore requise, notamment pour la lisibilité des cinq libellés sur différentes largeurs d'écran et le placement des messages après enregistrement.
- PR #91 demeure ouverte et non fusionnée ; resimanage-2-work n'a pas été modifiée.


## Correction des raccourcis du tableau de bord et des messages flash — 4 novembre 2026

### Symptômes rapportés
- Un appui sur une icône du tableau de bord donnait l'impression d'ouvrir la catégorie correspondante dans le sous-menu, imposant un second appui.
- Les messages flash étaient jaunes et positionnés en haut du document, donc invisibles tant que l'utilisateur restait plus bas dans la page.

### Cause identifiée
- Les éléments de navigation `<details>` étaient ouverts automatiquement côté serveur dès que l'URL de destination appartenait à leur liste de routes. Même quand un raccourci du tableau de bord naviguait correctement vers `/residents`, `/assign`, `/rotation-board`, etc., le nouveau rendu rouvrait le groupe associé et son panneau pouvait recouvrir la page de destination. Le script restaurait aussi le dernier groupe de navigation mémorisé.
- Le style flash précédent imposait `position:fixed` en haut de l'écran avec un fond jaune hérité de `.msg`.

### Correctifs
- Sept templates : suppression de l'ouverture automatique des groupes à partir de `request.path`. L'ouverture est maintenant pilotée par l'action de navigation utilisateur.
- Sept templates : au clic sur une tuile `.rt-icon-dashboard .rt-action-card`, suppression de la clé de menu mémorisée, fermeture de tous les groupes et remise à zéro de la restauration de défilement. Le lien natif conserve sa destination et conduit directement à la page cible en un seul appui.
- Sept feuilles CSS : remplacement du flash jaune supérieur par un message rouge contrasté, blanc sur rouge, visible en bas de la fenêtre courante (au-dessus de la barre fixe sur mobile), sans demander de remonter le document.
- `app.py` : ajout de `role="alert"` et `aria-live="assertive"` aux messages flash pour les technologies d'assistance.
- `tests/test_app.py` : assertions ajoutées pour l'absence d'ouverture automatique par URL, la fermeture du sous-menu mémorisé au clic sur un raccourci, et le style rouge visible dans le viewport.

### Limite à distinguer
Les messages flash sont produits après redirection et sont communs à de nombreux traitements. Ils sont maintenant affichés immédiatement dans la fenêtre visible, près du bas de l'écran, au lieu du haut du document. Les erreurs propres à un champ de formulaire qui doivent apparaître exactement à côté de ce champ nécessitent en plus une validation locale et un rendu d'erreur spécifique à ce formulaire ; ce chantier transversal n'a pas été entrepris ici afin de ne pas modifier le comportement de centaines de formulaires à l'aveugle.

### Validation
- Correctifs appliqués sur `integration/resimanage-refonte-themes-2026-11-03` uniquement.
- Tests CI à lancer/contrôler sur le dernier commit ; aucune réussite de test n'est présumée à ce stade.
- Vérification sur appareil réel requise pour confirmer l'absence de panneau de navigation superposé après les huit raccourcis et la visibilité des messages sur différentes tailles d'écran.
- PR #91 reste ouverte et non fusionnée ; aucune modification de `resimanage-2-work`.


## Distinction visuelle des messages d'erreur et d'information — 4 novembre 2026

### Comportement demandé
- Les erreurs de validation, les refus techniques et les opérations impossibles doivent apparaître en rouge.
- Les confirmations et informations doivent apparaître en vert.
- Les messages restent fixés dans la fenêtre courante, en bas de l'écran, avec un décalage au-dessus de la navigation mobile.

### Implémentation
- app.py : les messages flash reçoivent désormais une catégorie Flask (error ou info). Les appels existants sont classés à partir de marqueurs d'erreur français, anglais et arabes ; un appel peut aussi imposer explicitement sa catégorie.
- Les sept templates récupèrent les catégories et appliquent des classes et rôles accessibles distincts : alerte assertive pour une erreur, statut informatif pour une confirmation.
- Les sept feuilles CSS affichent les erreurs en rouge et les informations en vert, sans changer le positionnement inférieur ni l'animation.
- tests/test_app.py : ajout d'un test de catégorisation et d'assertions de présence des deux styles dans chaque thème.

### Point de vigilance
La catégorisation automatique couvre les messages existants à partir de marqueurs multilingues. Les nouveaux messages dont la formulation est ambiguë doivent préciser leur catégorie au moment de l'appel (error ou info) afin de garantir le résultat attendu.

### Validation
- À exécuter sur le commit final : tests Python, build APK debug et smoke test Android.
- Vérification visuelle sur téléphone réel à effectuer pour les deux types de messages et les sept thèmes.
- PR #91 reste ouverte et non fusionnée ; branche officielle inchangée.
