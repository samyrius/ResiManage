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


## Tableau de garde : sélection par journée, correctifs et PDF — 4 novembre 2026

### Réalisé sur la branche candidate
- Sélecteur multiple indépendant dans chaque journée et chaque secteur ; les ajouts multiples sont validés atomiquement.
- Les résidents actifs locaux des promotions 1 à 3 sont sélectionnables. Les résidents de 4e année restent visibles mais désactivés pendant leur dispense DEMS ; les libellés historiques d'octobre et le rapprochement des identités ne sont pas supprimés.
- Retrait désormais motivé et traçable : les affectations ne sont plus effacées, elles sont marquées inactives avec motif, auteur et date ; un journal des correctifs est conservé.
- Calendrier actif et export CSV excluent les gardes retirées. Nouveau PDF mensuel paysage A4 avec le calendrier et l'historique des correctifs.
- Les icônes de l'accueil et de la barre inférieure bénéficient d'un relief CSS renforcé, d'ombres multicouches, d'une légère perspective et d'un enfoncement à l'appui dans les sept thèmes.

### Plugin 3D
La compétence Contour3D est disponible dans l'environnement, mais aucun exécuteur Blender ni outil de création de maillage 3D n'est exposé pour ce dépôt dans cette session. Le rendu 3D des commandes est donc renforcé en CSS, sans prétendre avoir créé des modèles Blender natifs.

### Génération mensuelle automatique : non activée
Le générateur à J-5 n'est pas encore activé : le planning d'octobre conserve 70 libellés distincts, dont plusieurs ambigus ou sans correspondance nominative fiable. Les quotas exacts par promotion et la règle de composition quotidienne UMC / Réanimation chirurgicale doivent être confirmés avant de générer une liste nominative. Aucune rotation arbitraire ni répartition supposée n'est introduite.

### Vérifications à exécuter
- Tests du module de garde : sélecteurs journaliers, ajout multiple atomique, dispense 4e année, motif obligatoire, conservation du journal, export PDF.
- Tests complets Python, puis build APK et smoke test Android.
- Vérification manuelle sur mobile de la sélection multiple et de l'enfoncement des boutons.
- PR #91 reste ouverte et non fusionnée ; branche officielle inchangée.

### Résultat des tests — commit 24201b8
- Workflow Python application checks : **succès, 186 tests passés** (run 41909792030).
- Workflow Android : régression Python réussie ; build debug APK : **succès**, artefact `resimanage2-debug-apk` (run 41909792328, artefact 13361783889). Le smoke test sur émulateur est encore en cours ; le contrôle visuel sur téléphone réel reste à faire.


## Catégories des résidents, import de la liste nominative et navigation des périodes — 4 novembre 2026

### Modifications engagées sur la branche candidate

- Éditeur des dates des périodes : chaque formulaire dispose désormais d'une ancre stable par période. Après sauvegarde, le navigateur revient sur la même carte de période, au lieu de remonter en haut du tableau.
- Messages d'action : le conteneur de notification est déplacé au chargement vers la zone concernée lorsque l'action fournit une ancre ; les formulaires de la page Affectations et les actions de gestion des résidents ont également un ciblage local.
- Sélecteur d'année depuis la page Affectations : l'année choisie ouvre directement le tableau général de répartition (/rotation-board) afin de consulter l'historique ou préparer l'année sélectionnée.
- Listes des résidents : trois catégories distinctes sont affichées, y compris lorsqu'une catégorie ne contient encore aucun résident :
  1. CHU Nedir Mohamed — Anesthésie-Réanimation (type local).
  2. CHU Nedir Mohamed — Médecine d'urgence (type emergency).
  3. Établissements externes (type external), avec établissement d'origine.
- Super Admin : action dédiée pour déplacer un dossier entre catégories. Le changement est inscrit dans l'audit ; l'identifiant du résident et son historique de stages sont conservés. Un déplacement vers un établissement externe exige le nom de l'hôpital et des dates de présence valides.
- Import des listes : un formulaire réservé au Super Admin accepte le fichier HTML nominatif 2025–2026. Il lit les quatre promotions actives et les notes « médecine d'urgence », puis archive la liste D.E.M.S. L'import exige la présence des cinq groupes nominatifs et évite de recréer un diplômé déjà archivé ; les effectifs 26, 12, 24, 11 et 18 sont ceux vérifiés dans le fichier source fourni.
- Les 18 dossiers D.E.M.S sont créés ou rapprochés des dossiers existants, marqués comme diplômés / réussite DEMS et insérés dans dems_archive avec instantané de profil. Le fichier source ne fournit pas la date de réussite au DEMS : le champ de date reste vide et l'interface affiche explicitement que la date n'est pas renseignée. Aucun historique de stage antérieur n'est fabriqué.
- Les cinq mentions « médecine d'urgence » repérées dans les promotions de 1re et 2e année sont classées dans la catégorie Urgences ; les autres résidents des quatre listes sont classés en Anesthésie-Réanimation.
- Les établissements externes proposés restent CAC DBK, EHS Cardio DBK et un champ libre pour préciser un autre hôpital.

### Données du document source vérifiées

- 1re année : 26 résidents.
- 2e année : 12 résidents.
- 3e année : 24 résidents.
- 4e année : 11 résidents.
- Liste D.E.M.S : 18 diplômés.
- Total des quatre promotions actives : 73 résidents.
- La liste contient cinq observations « médecine d'urgence » : trois en 1re année et deux en 2e année.

### Tests ajoutés / mis à jour

- Transfert de catégorie par Super Admin avec conservation de l'historique et trace d'audit.
- Import HTML : création des catégories actives, classification Urgences, archivage DEMS, absence de date inventée et idempotence.
- Présence des trois catégories et du formulaire d'import dans la page Résidents.
- Sélecteur d'année de la page Affectations dirigé vers le tableau général.
- Ancre de retour vers la carte de période après enregistrement des dates.
- Les résultats CI sont à contrôler sur le dernier commit après cette mise à jour ; aucune réussite n'est présumée avant la fin des workflows.

### Gouvernance et limites

- Changements réalisés uniquement sur integration/resimanage-refonte-themes-2026-11-03.
- PR #91 reste ouverte et non fusionnée ; resimanage-2-work reste inchangée.
- L'import des résidents ne s'exécute pas automatiquement au démarrage : un Super Admin doit sélectionner explicitement le fichier HTML depuis la page Résidents. Cela évite de modifier les données locales sans action autorisée.
- L'archive conserve les diplômés dans dems_archive ; le statut graduated les exclut des listes actives et des affectations courantes.


### Précision sur le positionnement des messages et résultat CI — 4 novembre 2026

- Les notifications sont injectées dans le contenu des modèles HTML isolés. Quand une zone d'action est identifiée, le conteneur reçoit une classe locale et les sept thèmes neutralisent explicitement le positionnement fixe inférieur ; le message reste dans le formulaire ou la cellule concernée.
- Validation GitHub Actions sur le commit de code 0c8a38d543e839b2c54643c3a202fbdce506005d :
  - Workflow Android — régression Python : succès, 191 tests passés en 46,47 s.
  - Build APK debug : en cours au moment du relevé.
  - Smoke test sur émulateur : en attente du résultat du build.
- Le workflow Python autonome sur le commit précédent ada18b19bb1ca4263de951a22f82bb75ede9c308 a également réussi avec 191 tests passés en 72,66 s. Le commit 0c8a38d ajoute ensuite le correctif de positionnement local dans les sept feuilles CSS et la classe JS correspondante ; la régression Android sur ce dernier commit a réussi.
- PR #91 reste ouverte et non fusionnée ; aucune modification de la branche officielle.

---

## Reconstitution de l'historique antérieur — 4 novembre 2026

Cette section rassemble les décisions et travaux antérieurs déjà consignés dans `docs/PROJECT_ARCHIVE.md`, `REGISTRE_PROJET_RESIMANAGE.md` et les échanges du projet. Elle évite de limiter le carnet de route aux seuls changements du 3 et 4 novembre. Les éléments sont classés selon leur niveau de preuve : exigences validées, code présent, CI réussie, ou vérification physique encore nécessaire.

### 13–14 octobre 2026 — prototype, fondations métier et identité

- Le prototype Flask de gestion des stages a été créé, installé et lancé sur le téléphone de l'utilisateur. La phase de création initiale est donc terminée.
- Les bases métier ont été définies : quatre années de résidence, quatre périodes par année, priorité d'affectation 4e puis 3e, 2e et 1re année, capacité par terrain/période et interdiction d'une double affectation d'un résident sur une même période.
- La règle de répétition a été précisée : les terrains obligatoires/de base doivent être accomplis avant répétition ; les terrains optionnels ne bloquent pas cette règle. Gynécologie n'est pas optionnelle. Les cinq terrains optionnels confirmés sont Sédation (7), Maxillo-faciale (8), Chirurgie cardiaque (11), Brûlés (18) et CAC DBK (19).
- Les premières fondations vérifiées ont inclus les comptes individuels, les rôles Super Admin, l'audit, les profils, l'historique, les objectifs, les examens, les règles de progression de 1re année, les décisions de progression des années supérieures, l'archive DEMS, l'import avec aperçu, l'export CSV et les sauvegardes/restaurations SQLite.
- Le 13 octobre, une version de référence a passé 25 tests automatisés après fusion du premier lot de fondations. Ces tests utilisaient des bases temporaires ; aucune base réelle de résident n'a été ajoutée au dépôt.
- L'identité a évolué vers le nom ResiManage. Les demandes visuelles comprennent l'icône médicale 3D fournie, sans croix, le nom visible ResiManage, un écran de connexion médical, le cœur/ECG, les drapeaux de langue et une interface française, arabe et anglaise avec RTL en arabe.
- Les demandes d'ergonomie mobile ont inclus la suppression des débordements horizontaux, des boutons accessibles, des formulaires lisibles et une navigation adaptée aux petits écrans. Les corrections CSS antérieures ont été consignées comme code modifié, mais leur validation physique doit être distinguée des tests automatisés.

### 15–17 octobre 2026 — séparation des versions et amélioration des profils

- Décision de conserver ResiManage 1 comme sauvegarde et de poursuivre le travail actif dans ResiManage 2. La sauvegarde `resimanage-1-backup` doit rester intacte.
- Les changements approuvés doivent être intégrés directement au projet actif après vérification, sans accumuler inutilement les modifications en attente.
- Les travaux profils/photos ont couvert l'acceptation PNG/JPG/WEBP, la validation réelle du contenu, la prévisualisation, la conservation de l'ancienne photo si le nouveau fichier est invalide, et l'amélioration de la présentation du profil.
- Le benchmark UX a été consigné dans `docs/UX_BENCHMARK.md` : revue documentaire de 10 plateformes comparables et 14 sites. Il s'agit d'une étude documentaire, pas d'une validation pratique de chacune de ces interfaces.
- Les PR et branches candidates ont été utilisées pour isoler les changements. Les résultats CI d'une ancienne tête de branche ne doivent jamais être attribués à une nouvelle tête sans vérification exacte du SHA.

### 18–21 octobre 2026 — architecture locale, progression et règles métier

- Décision de commencer par un fonctionnement local : PC Windows du secrétariat comme serveur/base centrale et téléphones Android comme clients, avec synchronisation sur le même réseau Wi-Fi/LAN. Aucun hébergement Internet public n'est demandé à ce stade.
- La synchronisation doit prévoir authentification, permissions, sauvegardes, journalisation, gestion des conflits et reprise après perte de réseau. La consultation/modification hors ligne complète et la synchronisation de toutes les entités ne doivent pas être déclarées disponibles sans preuve.
- Le projet doit pouvoir évoluer plus tard vers un serveur web central sécurisé sans rendre inutile l'architecture locale.
- Les périodes doivent être configurables par année de post-graduation ; ne pas imposer des dates prédéfinies lorsque le responsable doit pouvoir les saisir.
- Les intitulés institutionnels confirmés sont « Centre Hospitalo-universitaire Nedir Mohamed Tizi Ouzou », « Département d'anesthésie-réanimation » et « Chef de service Professeur Benhocine ». Remplacer partout « année universitaire » par « année de post-graduation ».
- Les règles de progression, examens, rattrapages, DEMS, objectifs, congés annuels (30 jours par année depuis la première inscription au CHU) et conservation de l'historique doivent être appliquées sans inventer de données.
- Les Super Admins sont Pr Benhocine et Dr Dris ; les autorisations sont contrôlées côté serveur et les opérations sensibles sont auditées.

### 21–25 octobre 2026 — résidents externes, contrôle et intégrité des données

- Les résidents externes venant notamment de l'EHS Cardio DBK, du CAC DBK et d'un établissement « Autre » avec nom d'hôpital libre doivent suivre les mêmes règles d'affectation et de rotation. Leur origine doit rester distincte de la spécialité et du service d'accueil.
- Les résidents du même CHU mais d'une autre spécialité doivent également être distinguables des résidents internes d'Anesthésie-Réanimation.
- Les corrections de validation ont progressivement couvert les identifiants mal formés, les notes d'examen, les dates futures DEMS, les objectifs, les promotions, les imports, les historiques, les capacités, les affectations, les conflits externes/locaux et les permissions.
- Les imports doivent rester prévisualisés, confirmés explicitement et revalidés au moment de la confirmation. Aucun historique de stage ne doit être fabriqué.
- La corbeille, les sauvegardes et l'archive DEMS doivent préserver les données et l'historique ; aucune base réelle, photo, sauvegarde, clé ou mot de passe ne doit être versionné dans Git.

### 25 octobre–1er novembre 2026 — audit du dépôt et amélioration des affectations

- Demande d'audit étendu du dépôt : code principal, sauvegarde, branches, PR et branche de test. Les branches doivent être comparées avant toute fusion ou suppression.
- La sauvegarde ResiManage 1 et les repères APK d'octobre doivent être préservés. Ne pas lancer une compilation APK sans demande explicite ; cette présente demande du 4 novembre autorise une compilation de contrôle.
- Les affectations doivent permettre de définir le nombre de postes par terrain et période directement dans le tableau, puis de choisir les résidents sans perdre le contexte.
- Après sauvegarde d'une capacité ou d'une affectation, rester sur la même page, à la même position, avec les filtres et la période conservés ; ne pas renvoyer en haut de page.
- Les résidents d'établissements périphériques et ceux du CHU relevant d'une autre spécialité doivent pouvoir être gérés sans mélanger leurs catégories.
- Les demandes de correction et les comportements réellement livrés doivent être suivis séparément ; un ticket ou une branche ne constitue pas une preuve d'intégration.

### 2–4 novembre 2026 — module Gardes, navigation et thèmes

- Le module Gardes a été ajouté à la candidate avec deux secteurs (UMC et Réanimation chirurgicale), un historique d'octobre 2026 importé depuis une source structurée, des libellés initiaux non résolus, une validation nominative réservée au Super Admin, les modifications manuelles, un journal des correctifs, CSV et PDF mensuel paysage A4.
- Le générateur automatique mensuel n'est pas activé : les libellés d'octobre sont encore ambigus et les quotas/règles de roulement doivent être confirmés. Ne pas inventer les gardes.
- Les modifications manuelles doivent survivre à une régénération ; les jours fériés algériens doivent être éditables. Les règles de pondération des jours fériés restent à définir avant automatisation.
- Les corrections récentes portent sur les sept modèles HTML/CSS, la navigation mobile, les retours visuels, les messages d'erreur rouges et les confirmations vertes, les raccourcis du tableau de bord, les sélecteurs de résidents par journée et le retour aux formulaires après enregistrement.
- Le tableau de garde ne doit pas affecter les résidents dispensés pour préparation du DEMS. Cette règle doit toutefois tenir compte de la clarification de promotion ci-dessous et de l'état réel de chaque résident.
- Le 4 novembre, la candidate a passé 191 tests Python sur le commit testé. Le workflow Android du run 41914073691 a ensuite réussi les trois jobs : régression Python, build debug APK et smoke test sur émulateur. Ces preuves ne remplacent pas le test physique sur le téléphone de l'utilisateur.

### Clarification officielle des promotions et de la liste de garde — 4 novembre 2026

La liste nominative reçue a été rédigée en octobre 2025. Les numéros d'année qu'elle affiche décrivent la situation de cette date et ne sont pas contradictoires avec la situation actuelle.

| Promotion indiquée sur la liste d'octobre 2025 | Situation après la rentrée d'octobre 2026 |
|---|---|
| 4e année 2025 | Fin de 4e année ; préparation du DEMS, examen de fin d'études pour obtenir le diplôme de spécialiste |
| 3e année 2025 | Nouvelle 4e année depuis octobre 2026 |
| 2e année 2025 | Nouvelle 3e année depuis octobre 2026 |
| 1re année 2025 | Nouvelle 2e année depuis octobre 2026 |
| Nouvelle cohorte admise récemment | Nouvelle 1re année ; intégration prévue dans la liste de garde de décembre 2026 |

- Le DEMS se déroule à la fin de la quatrième année.
- Les résidents de l'ancienne 4e année (cohorte ayant commencé en octobre 2025) sont en fin de cursus et sont généralement dispensés de la liste de garde pendant leur préparation au DEMS.
- Les résidents de l'ancienne 3e année sont les nouveaux 4e années depuis octobre 2026 ; ils ne doivent pas être confondus avec la cohorte qui prépare le DEMS.
- Les anciennes 2e et 1re années deviennent respectivement 3e et 2e années en octobre 2026.
- Une nouvelle promotion de 1re année vient d'arriver ; ses noms seront communiqués ultérieurement et elle doit rejoindre la liste de garde à partir de décembre 2026.
- Pour novembre 2026, l'utilisateur confirme qu'il n'y a aucun résident inactif ou en congé dans la liste à préparer.
- Ne pas déduire automatiquement l'année actuelle à partir d'un simple libellé historique sans tenir compte de la date de la liste et de la promotion d'origine. Conserver l'année d'étude historique et l'année courante comme deux informations distinctes.
- À réception des noms de la nouvelle cohorte, les ajouter à la liste de décembre sans réécrire l'historique d'octobre/novembre.

### Preuves de compilation et d'émulateur — 4 novembre 2026

- PR candidate : https://github.com/samyrius/ResiManage/pull/91
- Branche : `integration/resimanage-refonte-themes-2026-11-03`
- Commit testé : `50fd4d398a9752bda251f7e2d0ca98110ea8db26`
- Run Android : https://github.com/samyrius/ResiManage/actions/runs/41914073691
- Régression Python : 191 tests réussis.
- Build debug APK : job réussi ; artefact GitHub Actions ID `13364477136`.
- Smoke test Android émulateur : job réussi ; capture d'écran et logcat conservés dans l'artefact ID `13363358996`.
- Archive ZIP de l'APK : SHA-256 `b42fa54dd5c7340e6f3bae02b8880be80d0d90a00cf208482f10ed2644d00e31`.
- APK extraite et vérifiée dans l'environnement de contrôle : SHA-256 `a9cb9be9c4ba2ece7aea069447ae9e9e2d1e3e843d691b4f2ba8e3c8c593a2d2`.
- La capture émulateur montre l'écran de connexion ResiManage avec les choix de langue et l'identité visuelle. Cela établit le démarrage et le rendu initial sur cet émulateur, pas le fonctionnement complet de toutes les pages ni le succès sur téléphone physique.

### État de fusion et prochaines étapes

- PR #91 est ouverte et GitHub la signale mergeable, mais le carnet et les décisions antérieures imposent de ne pas fusionner sans accord explicite distinct.
- La branche officielle `resimanage-2-work` est restée inchangée pendant cette vérification.
- La sauvegarde `resimanage-1-backup` n'a pas été modifiée.
- L'audit des 105 branches est un inventaire et une revue statique de branches représentatives ; la lecture exhaustive de chaque commit/fichier des branches anciennes reste à terminer avant tout nettoyage.
- Prochaine étape : faire valider l'APK sur le téléphone réel, puis poursuivre les corrections métier restantes (générateur de gardes, jours fériés et règles d'équité, conservation du contexte dans toutes les pages, retour Android, synchronisation complète et validation des migrations historiques). Ne pas marquer ces éléments comme terminés avant preuves.

---

## Dispense DEMS par cohorte : correction métier appliquée — 4 novembre 2026

### Problème corrigé

La première version du module Gardes excluait automatiquement tous les résidents de 4e année. Cette règle confondait la cohorte qui termine la 4e année et prépare le DEMS avec la nouvelle cohorte promue en 4e année en octobre 2026.

### Implémentation

- Le statut existant `residents.dems_status` porte désormais la valeur `preparing` lorsqu'un résident est en préparation DEMS ; aucune nouvelle colonne ni migration destructive n'est nécessaire.
- Depuis la rubrique DEMS, un Super Admin peut marquer individuellement un résident actif de 4e année comme « en préparation DEMS » ou lui rendre son admissibilité aux gardes.
- Chaque changement est consigné dans le journal d'audit (`dems.preparation_status_changed`).
- Le sélecteur des gardes accepte désormais les résidents locaux actifs des années 1 à 4, sauf ceux explicitement marqués `preparing` ou déjà archivés au DEMS.
- La validation serveur des ajouts individuels, multiples et des rapprochements nominaux applique la même règle ; masquer une option dans l'interface ne suffit pas.
- La liste des candidats au vote DEMS ne présente que les résidents marqués en préparation DEMS. Les nouveaux 4e années ne sont donc pas proposés par erreur.
- La dispense reste distincte du statut inactif et des congés. Marquer une préparation DEMS ne transforme pas le résident en inactif.
- Aucun résident n'a été marqué automatiquement à partir de son seul numéro d'année. Le Super Admin devra identifier les membres de l'ancienne cohorte 4e année et leur appliquer le statut depuis la rubrique DEMS. Les nouveaux 4e années sont admissibles par défaut.

### Tests et compilation

- Commit code validé : `74560794c42243c03bf3d3bccede5e4294bcad6e`.
- Tests Python : 193 réussis dans le workflow de régression autonome et dans le job de régression Android.
- Workflow Android : https://github.com/samyrius/ResiManage/actions/runs/41918864436
- Build debug APK : job réussi.
- Artefact APK GitHub Actions : `13366910443`.
- APK extraite et vérifiée : SHA-256 `4f8eb7bf4a3989944a13d6b8a261eb69f910bf2c10125eb74037b77c7ea08d09`.
- Au moment de cette mise à jour, le smoke test sur émulateur est encore en cours ; ne pas le déclarer réussi avant son résultat final.
- Le test sur le téléphone physique reste nécessaire après installation.

### Gouvernance

- Modifications appliquées sur la branche candidate `integration/resimanage-refonte-themes-2026-11-03`.
- PR #91 reste ouverte et non fusionnée ; aucune fusion automatique n'a été effectuée.
- `main`, `resimanage-2-work` et `resimanage-1-backup` n'ont pas été modifiées par ce lot.


---

## Mise au point générale du projet — 5 novembre 2026

### Référence technique vérifiée

- Dépôt : `samyrius/ResiManage`.
- Branche candidate active pour les travaux examinés : `integration/resimanage-refonte-themes-2026-11-03`.
- HEAD vérifié : `5eabfdff499dc536c98bdf09207e9c63bfff0259`.
- Dernier commit : `Consigner la correction DEMS par cohorte et les preuves de test` (mise à jour documentaire de la correction déjà portée au commit `74560794c42243c03bf3d3bccede5e4294bcad6e`).
- PR #91 vers `resimanage-2-work` : ouverte, non fusionnée. Aucune fusion autorisée implicitement.
- Branche officielle `resimanage-2-work` et sauvegarde `resimanage-1-backup` : non modifiées par le travail candidat contrôlé ici.

### Dernière APK effectivement produite et vérifiée

- Workflow Android : https://github.com/samyrius/ResiManage/actions/runs/41919570043
- Commit compilé : `5eabfdff499dc536c98bdf09207e9c63bfff0259`.
- Artefact `resimanage2-debug-apk`, ID `13367056402`, généré le 4 novembre 2026 à 21:52:47 UTC (22:52:47 heure algérienne), taille 38 570 751 octets ; expiration annoncée le 18 novembre 2026.
- Régression Python : **193 tests réussis** en 73,58 secondes (job `126888557252`).
- Build debug APK : succès (job `126889365587`).
- Smoke test Android émulateur : succès (job `126890237958`). Les logs montrent l'installation/démarrage, la vérification de la page de connexion, la recherche d'erreurs fatales ciblées dans logcat et la capture d'écran. Preuve disponible dans l'artefact `resimanage2-android-emulator-evidence`, ID `13365658882`.
- Cela valide le build et le parcours de démarrage contrôlé sur l'émulateur CI. **Cela ne constitue pas une validation sur le téléphone physique de l'utilisateur**, ni une vérification exhaustive de toutes les pages et interactions.

### Fonctionnalités et corrections présentes dans la candidate

- Gestion des résidents, services, capacités, périodes, affectations, progression, examens, objectifs, DEMS, congés, stages externes, corbeille, audit et sauvegarde/restauration.
- Import explicite par Super Admin du fichier HTML des promotions 2025–2026 : 73 résidents dans les quatre promotions actives (26, 12, 24, 11), cinq résidents classés en médecine d'urgence, et 18 diplômés archivés DEMS. Aucune date DEMS ni aucun historique de stage n'est inventé.
- Trois catégories de résidents : anesthésie-réanimation locale, médecine d'urgence au CHU, établissements externes.
- Correction DEMS par résident : les nouveaux 4e années ne sont plus exclus automatiquement des gardes ; seuls les résidents explicitement marqués `preparing` ou déjà archivés DEMS sont dispensés. Le marquage individuel reste à effectuer par le Super Admin pour les membres de l'ancienne cohorte préparant effectivement le DEMS.
- Module Gardes : historique d'octobre importé, sélection multiple par journée/secteur, retrait motivé et audité, exports CSV et PDF, règles serveur cohérentes avec le statut DEMS.
- Sept thèmes disposent de templates et feuilles CSS séparés ; les corrections de navigation, sous-menus, notifications, barre mobile et défilement ont été portées dans la candidate.
- Le carnet décrit aussi le retour au formulaire après sauvegarde, les catégories des notifications (erreur rouge / information verte) et les raccourcis du tableau de bord.

### Limites et travaux encore ouverts

1. **Validation sur téléphone réel :** installer l'APK du commit exact ci-dessus et vérifier à froid le démarrage, la barre d'icônes, le scroll, les menus, les notifications, les formulaires et les sept thèmes. Ne pas confondre le smoke test émulateur avec cette validation.
2. **Génération automatique des gardes :** non implémentée/activée. Le planning d'octobre conserve des libellés historiques à rapprocher ; les quotas, règles UMC/Réanimation chirurgicale, pondérations et jours fériés algériens doivent être définis avant toute génération nominative. La nouvelle cohorte de 1re année est attendue pour décembre 2026.
3. **Synchronisation :** implémentation partielle, pas une réplication complète de toutes les entités ; synchronisation hors ligne, conflits et validation physique restent incomplets. Ne pas utiliser avec des données réelles avant validation de bout en bout et sécurité.
4. **Thèmes :** les sept modèles et CSS sont isolés et ont des variations de navigation/layout, mais le rendu comparatif réel sur téléphone reste à confirmer. L'audit antérieur note que les squelettes HTML conservent une structure commune ; ne pas prétendre que chaque écran a été entièrement redessiné indépendamment sans revue visuelle.
5. **Android / diagnostic :** les nouveaux workflows démontrent le démarrage sur émulateur et le rendu du login. L'ancien signalement utilisateur `System exit 1` n'est donc pas une preuve que le dernier APK échoue ; il n'est pas non plus considéré comme résolu sur l'appareil réel avant essai de cette dernière APK.
6. **Sécurité et gouvernance :** la branche officielle n'est pas protégée selon l'audit précédent ; les règles GitHub de protection et les contrôles obligatoires restent à mettre en place. La revue de sécurité est statique, pas un audit d'intrusion.
7. **Historique Git :** l'inventaire des branches a été réalisé et des branches représentatives comparées, mais la revue exhaustive de chaque commit unique et de chaque diff des branches historiques n'est pas terminée. Aucune branche ne doit être supprimée ou fusionnée en masse.
8. **Documentation :** le README de la candidate affirme encore que `resimanage-2-work` est la source active où appliquer les corrections, alors que le travail courant et la PR #91 utilisent la branche candidate. Cette contradiction documentaire doit être clarifiée dans une tâche séparée avant toute modification de branche ou fusion.
9. **Carnet de route :** plusieurs paragraphes historiques conservent leur statut au moment où ils ont été écrits (par exemple « smoke test en attente » ou « incident bloquant »). La présente mise au point constitue le statut consolidé le plus récent ; les anciennes entrées restent conservées comme historique et ne doivent pas être lues comme le statut actuel.

### Décisions de gouvernance conservées

- Continuer les changements sur la branche candidate tant qu'aucune nouvelle instruction explicite n'est donnée.
- Ne pas pousser sur `resimanage-2-work`, ne pas fusionner PR #91, ne pas supprimer ni réécrire de branche.
- Pour chaque observation future, consigner symptôme, diagnostic et degré de certitude, fichiers/commits, tests, résultats CI et validation physique distinctement.
- Un correctif est « appliqué » lorsqu'il est dans le code ; « testé » lorsque le test correspondant a été exécuté ; « validé CI » lorsque le workflow exact réussit ; « confirmé sur appareil » uniquement après retour du test physique.



---

## Correctifs UX et refonte réelle des thèmes — 5 novembre 2026

### Retour utilisateur à l'origine du lot

Après examen de l'APK précédente, l'utilisateur a signalé que les thèmes ne changeaient essentiellement que les couleurs, sans proposer de dispositions réellement distinctes. Il a également précisé les attentes suivantes :

1. Les boutons doivent avoir un relief 3D nettement perceptible et une animation d'enfoncement à l'appui.
2. Les icônes des raccourcis intérieurs du tableau de bord ne doivent pas avoir de libellé textuel.
3. Les cinq icônes de la barre fixe inférieure doivent avoir leur libellé sous l'icône, sans déformation ni largeur incohérente.
4. L'ouverture d'un sous-menu doit fermer automatiquement le sous-menu précédemment ouvert ; un second appui sur le sous-menu actif doit pouvoir le refermer.
5. Les notifications informatives et les erreurs doivent être compactes, ne pas encombrer l'écran, se fermer avec un bouton ou par appui à l'extérieur et disparaître automatiquement.

### Modifications portées dans la branche candidate

Branche : `integration/resimanage-refonte-themes-2026-11-03`.

- Sept dispositions distinctes ont été ajoutées au niveau du conteneur principal et des feuilles CSS dédiées :
  - Crystal 3D : espace de travail centré et tableau de bord en grille ;
  - Futuriste : rail de navigation latéral et espace de travail compact ;
  - Luxe élégant : présentation éditoriale, navigation horizontale et colonne de lecture aérée ;
  - Naturel moderne : navigation latérale et raccourcis en liste verticale ;
  - Émeraude : navigation latérale à droite et grand espace de travail ;
  - Aurore boréale : rail d'icônes étroit avec panneaux de sous-menu flottants ;
  - Rubis : barre de commande horizontale et sections fortement hiérarchisées.
- Les variantes sont ciblées avec l'attribut `data-layout` du conteneur `.rt-app-shell`, afin de conserver la classe historique `rt-app-shell` attendue par les tests et les styles existants.
- Le changement de thème applique immédiatement l'attribut de disposition correspondant, en plus de la feuille CSS du thème.
- Les libellés de la navigation inférieure sont rétablis et stylés sous les icônes ; les libellés textuels des raccourcis intérieurs sont masqués visuellement tout en conservant un texte accessible.
- Les groupes de sous-menus sont rendus exclusifs : l'ouverture d'un groupe ferme les autres ; l'appui sur le groupe déjà ouvert le referme.
- Les messages flash sont présentés comme notifications compactes en haut de l'écran, avec fermeture explicite, fermeture par clic extérieur et temporisation automatique. Le marqueur caché `rt-action-context` est conservé pour ne pas casser le retour au formulaire et les tests historiques.
- Un relief plus marqué a été ajouté aux cartes/icônes du tableau de bord et aux contrôles de navigation, avec ombres internes et externes et animation d'enfoncement à l'appui.

### Commits du lot

Les commits suivants portent les ajustements de cette séquence sur la branche candidate :

- `3b141d2c9833f687226f684396df8de59f6989c6` — libellés de navigation et fermeture exclusive des sous-menus ;
- `f38a2fd2d8b2b72773704782c7fa0be5ec19dcb1` — premières dispositions spécifiques et notifications compactes ;
- `445547ce7505b393d67ed2f60f87d1d1e5f96b27` — conservation du marqueur de contexte des formulaires ;
- `15f0d97563b8ff26ca96970a5f921cc7c0dfaa20` — ciblage des feuilles CSS par attribut de disposition en préservant la classe du conteneur ;
- `9d2de2a0e1448b11970dd8d2d28e7c071baef020` — renforcement du relief 3D des boutons ;
- `17a8bd787a01d5fe9f7ab9c4cfe67f22365f407c` — application immédiate de la disposition lors du changement de thème ;
- `a9d3c762dc33480a896762434997b8aa116cd3d8` — conservation de la classe historique du conteneur dans les sept templates et tête candidate soumise aux workflows de validation.

Les modifications sont portées dans la branche candidate. Les noms des commits ne constituent pas à eux seuls une preuve visuelle : le rendu final de chaque thème doit encore être vérifié sur téléphone.

### Vérifications CI sur la tête exacte

- Commit contrôlé : `a9d3c762dc33480a896762434997b8aa116cd3d8`.
- Workflow Python : https://github.com/samyrius/ResiManage/actions/runs/42058315107 — terminé avec succès ; **193 tests réussis** (74,00 secondes).
- Workflow Android : https://github.com/samyrius/ResiManage/actions/runs/42058317186 — terminé avec succès :
  - régression Python : succès ;
  - compilation de l'APK debug : succès ;
  - smoke test Android sur émulateur : succès.
- Artefact APK : `resimanage2-debug-apk`, ID `13430455560`, taille 38 584 272 octets ; SHA-256 `c9efd52a2b8c92600bc246e7bbe9a2c7afbfdf5639daf3e8219ff904766137db`. L'artefact expire le 19 novembre 2026 à 15:49:12 UTC.
- Preuve émulateur : artefact `resimanage2-android-emulator-evidence`, ID `13431525314`, SHA-256 `510deb5951bcf4836075970150eef3f384ad2bf39fc6ad87a6277a8889b78ffc`.
- Ces résultats confirment la régression automatisée, la compilation et le smoke test sur émulateur. Ils ne prouvent pas encore que les sept dispositions sont visuellement conformes sur le téléphone physique.

### État Git et validations restantes

- PR #91 : https://github.com/samyrius/ResiManage/pull/91 — ouverte et non fusionnée au moment de cette mise à jour.
- La branche officielle `resimanage-2-work` n'a pas été modifiée par ce lot.
- L'APK issue du commit exact `a9d3c762dc33480a896762434997b8aa116cd3d8` doit maintenant être installée sur le téléphone réel.
- Contrôles à effectuer sur appareil : comparer les sept dispositions (et pas seulement leurs couleurs), vérifier la présence des cinq libellés sous les icônes de la barre inférieure, l'absence de libellés visibles sur les raccourcis intérieurs, le relief et l'animation des boutons, l'exclusivité des sous-menus, ainsi que la fermeture et la disparition automatique des notifications.
- Si une disposition reste trop proche d'une autre ou si un élément déborde sur petit écran, consigner le thème, la page, l'action et une capture avant le correctif suivant.
- La validation physique reste en attente du retour utilisateur. Ne pas fusionner PR #91 avant cet accord explicite.


---

## Refonte de l’architecture de navigation intérieure — 5 novembre 2026

### Diagnostic utilisateur

L’utilisateur a signalé que la navigation ressemblait à un labyrinthe : trop de rubriques, menus et sous-menus, textes explicatifs qui prennent de la place, défilement pour retrouver les fonctions et trop d’appuis successifs. La priorité de ce lot est donc l’orientation et l’accès rapide aux fonctions, avant toute nouvelle modification purement esthétique.

### Architecture appliquée

- Remplacement des anciens groupes déroulants par cinq destinations principales directement visibles dans les sept modèles de thème :
  1. Accueil ;
  2. Résidents ;
  3. Stages ;
  4. Gardes ;
  5. Plus.
- Les cinq destinations sont des liens directs, sans sous-menu intermédiaire. Sur mobile, elles conservent cinq colonnes égales et un libellé court sous chaque pictogramme ; sur ordinateur, elles gardent la présentation propre au thème.
- La destination « Plus » ouvre la page `/plus`, qui sert de répertoire de toutes les fonctions secondaires. Les fonctions sont regroupées par activité et présentées sous forme de raccourcis visibles, sans menus imbriqués.
- Une recherche instantanée filtre les raccourcis du répertoire. Elle recherche dans les libellés et synonymes français, anglais et arabes, et neutralise les accents français pour éviter qu’une recherche sans accent ne manque un résultat.
- Les fonctions avancées et d’administration ne sont affichées dans le répertoire que pour le rôle `super_admin`. Les contrôles d’autorisation côté serveur restent inchangés et continuent de faire autorité.
- Retrait de l’ancien gestionnaire JavaScript de sous-menus et de la flèche de retour navigateur qui pouvait créer un repère de navigation ambigu.
- Les longs paragraphes explicatifs non critiques (190 caractères ou plus) sont repliés dans une aide consultable. Les paragraphes de formulaire, les messages, les avertissements identifiés comme importants, les contenus avec liens ou mise en évidence forte restent visibles.
- Suppression du court texte de priorité devenu inutile sur le tableau de bord. Les routes métier et les données ne sont pas modifiées par cette refonte.

### Fichiers concernés

- `templates/themes/crystal3d.html`
- `templates/themes/futuriste.html`
- `templates/themes/luxe-elegant.html`
- `templates/themes/naturel-moderne.html`
- `templates/themes/emeraude.html`
- `templates/themes/aurore-boreale.html`
- `templates/themes/rubis.html`
- `app.py` : nouvelle route `/plus`, répertoire filtrable, suppression du texte d’introduction inutile sur l’accueil.
- `tests/test_app.py` : mise à jour des tests de navigation et ajout d’un test du répertoire à cinq accès directs et de la recherche.

### Vérifications et compilation

- Commit exact compilé : `9b921ac73d3927db8aa6f3c2c74d7a2b3087f4a1`.
- Workflow Python : https://github.com/samyrius/ResiManage/actions/runs/42074391086 — succès, **194 tests réussis**.
- Workflow Android : https://github.com/samyrius/ResiManage/actions/runs/42074391563 — succès :
  - régression Python Android : **194 tests réussis** ;
  - compilation APK debug : succès ;
  - smoke test sur émulateur Android : succès.
- Le smoke test confirme l’installation et le démarrage de l’application, l’accès HTTP à la page de connexion, la présence des libellés de connexion et l’absence des erreurs fatales ciblées dans logcat. Il ne teste pas visuellement l’ensemble des pages ni l’ergonomie de la nouvelle navigation sur téléphone physique.
- Artefact APK GitHub Actions : `resimanage2-debug-apk`, ID `13438215858`, taille de l’archive 38 583 926 octets ; SHA-256 de l’archive `6454f7826f183725bf28c3e07b8837e6f7924f7a62aa0a99134b4c13cbde25e1`.
- APK extraite pour test manuel : 59 039 297 octets ; SHA-256 `2021d1b0cd122cb0b486782edab69d1629c09af8c45f21463ba7bb1bae5cbacc`.
- Preuve émulateur : artefact `resimanage2-android-emulator-evidence`, ID `13438560570`, SHA-256 `aee2f38556708e9b5630d35619d7b5fcad3dee61e2f60760c91ad0319dc7586d`.
- Les deux artefacts expirent le 19 novembre 2026. L’APK issue du commit ci-dessus a été récupérée et extraite dans l’environnement de travail pour installation manuelle.

### Gouvernance et validation restante

- Branche candidate : `integration/resimanage-refonte-themes-2026-11-03`.
- PR #91 vers `resimanage-2-work` : ouverte, non fusionnée.
- La branche officielle `resimanage-2-work` et la sauvegarde `resimanage-1-backup` ne sont pas modifiées par ce lot.
- Installer l’APK du commit exact `9b921ac73d3927db8aa6f3c2c74d7a2b3087f4a1` sur le téléphone physique et vérifier : les cinq destinations fixes, les libellés sous les icônes, l’accès direct au tableau des stages et aux gardes, le répertoire « Plus », la recherche avec/sans accents, le comportement des aides repliables et le défilement.
- Le smoke test CI ne remplace pas cette validation physique. Ne pas fusionner PR #91 sans accord explicite distinct.

## Refonte de l'accès aux fonctions — 5 novembre 2026

### Constat vérifié sur la branche candidate
- La navigation des sept thèmes dispose de cinq accès principaux : Accueil, Résidents, Stages, Gardes et Plus.
- « Plus » ouvrait un long catalogue vertical de fonctions regroupées en blocs, avec une recherche mais sans filtre de catégories. Les utilisateurs devaient parcourir ce catalogue pour trouver les outils moins fréquents.
- Plusieurs fonctions de suivi, de formation, d'administration et de gestion des stages étaient mélangées dans cette page.

### Modifications réalisées sur la branche candidate
- Le libellé « Plus » devient « Outils » dans les sept modèles, sans changer les cinq accès principaux ni les destinations.
- Le lanceur Outils présente une recherche globale et des catégories compactes : Résidents, Stages, Formation et Administration (Administration uniquement pour Super Admin).
- Une seule catégorie est affichée à la fois. La recherche traverse toutes les catégories, ignore la casse et les accents et masque les groupes sans résultat.
- Les outils sont reclassés selon les tâches : import et formulaires résidents ; services, capacités, affectations, historique, congés et stages externes ; examens, objectifs, DEMS, synthèse et décisions ; paramètres, utilisateurs, synchronisation, audit, sauvegardes, exports, restauration et corbeille.
- Les routes métier, les URL, les données et les règles d'autorisation n'ont pas été modifiées.
- Le plan détaillé et les critères de validation sont consignés dans docs/PLAN_NAVIGATION_2026-11-05.md.

### Vérifications à effectuer
- Ajouter/maintenir des tests sur la présence des catégories, l'affichage d'une seule catégorie et la recherche inter-catégories.
- Exécuter la suite Python et le workflow Android/émulateur sur le nouveau commit.
- Contrôler visuellement les sept thèmes sur ordinateur et téléphone ; la validation CI ne remplace pas ce contrôle d'ergonomie.
- Ne pas fusionner la PR #91 sans accord explicite distinct.

## Planification groupée des capacités et affectations — 5 novembre 2026

### Problème constaté
Le parcours antérieur obligeait à répéter une saisie de capacité puis une affectation résident par résident et service par service. La vue générale affichait déjà les 19 services et les quatre périodes, mais les modifications restaient réparties dans des formulaires unitaires.

### Première évolution livrée sur la branche de travail
- Nouvelle page /planning, accessible depuis l’entrée Affectations (/assign redirige désormais les consultations GET vers cette page ; le POST historique reste pris en charge).
- Vue unique des 19 services actifs pour une période sélectionnée.
- Saisie des capacités service par service dans une seule grille, avec effectif utilisé et places restantes.
- Recherche de résidents via une liste de suggestions commune, ajout sous forme de pastilles, plusieurs résidents pouvant être préparés dans une même ligne.
- Enregistrement groupé unique pour les capacités et les nouvelles affectations.
- Contrôle serveur conservé via check() : résident actif, capacité définie et disponible, affectation déjà existante, stages externes, historique et règles d'année obligatoire.
- Transaction atomique : si une capacité ou une affectation du lot est invalide, le lot entier est annulé ; aucune partie n'est enregistrée.
- Événements d'audit conservés pour chaque capacité et affectation modifiée.
- Les opérations avancées de déplacement/retrait et l'aperçu PDF restent dans le tableau général /rotation-board.
- La page Capacités propose un accès direct à la planification groupée.

### Limites connues à traiter ensuite
- Première version organisée par période : l'utilisateur sélectionne une période, prépare tous les services, puis enregistre. La préparation simultanée des quatre périodes dans une seule grille reste une amélioration distincte.
- En cas de validation serveur négative, les modifications du lot sont annulées et un message est affiché ; les saisies préparées ne sont pas encore restaurées automatiquement dans le formulaire. À améliorer avant de considérer le parcours finalisé.
- Le sélecteur de résident utilise une liste de suggestions partagée. Une recherche plus riche (filtre par promotion, disponibilité en temps réel et conflits visibles avant validation) reste à concevoir.
- Les tests CI doivent confirmer le comportement Flask et Android sur le SHA de cette évolution ; aucune APK ne doit être annoncée comme validée avant la fin des workflows correspondants.

### Validation ajoutée
- Affichage des 19 services dans la grille.
- Redirection de l'entrée Affectations vers /planning.
- Enregistrement de plusieurs capacités et d'une affectation dans un seul POST.
- Vérification du rollback atomique en cas de résident invalide.

## Retour utilisateur après essai de la planification groupée — 5 novembre 2026

### Nouveau retour d'expérience
Après essai de l'APK de planification groupée, l'utilisateur indique que le parcours n'est toujours pas pratique :
- Les informations nécessaires ne sont pas toutes visibles et accessibles au même endroit.
- La présentation en deux tableaux est jugée peu pratique.
- Le besoin principal est une vue générale centralisée, permettant de comprendre l'ensemble de la répartition sans naviguer entre plusieurs tableaux ou listes.

### Orientation UX retenue pour la prochaine conception
Ne pas poursuivre avec deux tableaux séparés (liste des résidents d'un côté, services de l'autre). Repenser l'écran autour d'un tableau matriciel unique qui sert à la fois de vue d'ensemble et d'espace d'édition.

Piste de conception à valider par prototype :
- Lignes : services actifs (les 19 services).
- Colonnes : les quatre périodes.
- Chaque cellule présente au minimum la capacité prévue, le nombre de résidents affectés, les places disponibles et les résidents affectés (nom et promotion).
- Ajout, retrait et déplacement de résidents directement depuis la cellule concernée, sans basculer vers un second tableau.
- Recherche globale et filtres promotion/période conservés dans une barre d'outils compacte.
- Alertes directement dans les cellules : capacité dépassée, résident déjà affecté, indisponibilité ou conflit.
- Sur tablette, conserver les en-têtes visibles, limiter les défilements inutiles et permettre l'ouverture/édition d'une cellule sans perdre la vue d'ensemble.

### Décision de méthode
Cette orientation est une proposition de conception issue du retour utilisateur, pas encore une implémentation validée. Préparer d'abord une maquette/prototype centré sur le tableau unique et le faire évaluer avant de modifier davantage les règles métier ou de lancer une nouvelle APK. Ne pas fusionner la branche candidate dans la branche officielle sans autorisation explicite.
