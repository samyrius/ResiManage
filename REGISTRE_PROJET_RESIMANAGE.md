# Registre de décisions et d’archive — ResiManage 2

Dernière mise à jour : 18 octobre 2026  
Dépôt : https://github.com/samyrius/ResiManage  
Branche de travail visée : `resimanage-2-work`

> Ce registre consigne les décisions validées et les exigences connues. Une décision inscrite ici décrit le comportement attendu ; elle ne prouve pas que la fonction est déjà codée ou testée.

## 1. Décision validée le 18 octobre 2026 — fonctionnement local avec synchronisation LAN

**Décision de l’utilisateur : validée.**

- Pour le moment, ResiManage reste une application locale. Aucun serveur web public ni hébergement Internet ne doit être mis en place à cette étape.
- La synchronisation entre le PC Windows du secrétariat et les téléphones Android est conservée comme exigence dès la version locale.
- Le PC Windows héberge la base de données centrale et le service local de synchronisation.
- Le téléphone et le PC doivent pouvoir échanger les données lorsqu’ils sont connectés au même réseau local (Wi-Fi/LAN) et que le PC est allumé.
- En l’absence du PC ou du réseau, le téléphone ne pourra synchroniser qu’au retour de la connexion. Le mode hors connexion (consultation ou modifications locales) doit être défini et implémenté explicitement ; ne pas le considérer comme déjà disponible.
- Prévoir authentification, autorisations par rôle, transport local protégé autant que possible, gestion des conflits de modifications, journalisation et sauvegardes/restauration.
- **Étape future, après finalisation et tests :** adapter l’architecture pour permettre la synchronisation via un serveur web central sécurisé, à l’hôpital et à distance. L’architecture actuelle devra éviter de rendre cette évolution inutilement coûteuse.

## 2. Règles de travail et de versionnement

- La version active de travail est **ResiManage 2**, associée à la branche `resimanage-2-work`.
- **ResiManage 1** est une sauvegarde à préserver. Ne pas la modifier ni la supprimer pendant le travail sur la version 2.
- À chaque correction poussée sur `resimanage-2-work`, la CI compile automatiquement un APK debug et tente des tests de démarrage dans un émulateur Android ; l’APK et les preuves (journaux/capture) sont conservés comme artefacts temporaires. Une compilation EXE ou un APK de diffusion/release reste soumise à une demande explicite. Les tests sur téléphone réel restent complémentaires.
- Après validation d’une modification par l’utilisateur, l’intégrer directement au projet actif dès que possible, puis documenter le changement et les tests réellement effectués.
- Ne jamais annoncer qu’une fonction est terminée, compilée, synchronisée ou testée sans preuve vérifiable.
- Préserver la base de données réelle et ses sauvegardes. Ne jamais ajouter de données personnelles fictives dans les données réelles ; utiliser une base de test séparée et des données fictives pour les tests.
- Ne jamais publier de mots de passe, jetons, clés API ou chaînes de connexion dans le dépôt ou dans les conversations.
- Avant une migration ou modification risquée, vérifier l’état du dépôt et créer une sauvegarde appropriée.

## 3. Ordre de priorité actuel

1. Vérifier l’état réel du code sur la branche de travail active avant de modifier quoi que ce soit.
2. Corriger l’interface : thème moderne et cohérent, identité visuelle médicale 3D fournie par l’utilisateur, icône d’application sans symbole de croix, nom visible « ResiManage », mise en page pratique, titres qui restent dans leurs conteneurs, ordre des boutons fonctionnel.
3. Corriger l’affichage et la taille de la photo dans le profil du résident. L’import de photo a été signalé comme fonctionnant lors du dernier essai, mais son cadre est trop petit.
4. Stabiliser la version Windows locale, sans console noire visible ni adresse à saisir par l’utilisateur, avec base locale persistante et sauvegarde/restauration.
5. Implémenter et tester la synchronisation locale PC ↔ Android, avec gestion explicite des conflits et des pertes de connexion.
6. Finaliser les fonctions métier, les rôles et l’audit.
7. Effectuer des tests complets avec des données fictives ; les APK debug et smoke-tests Android sont automatisés à chaque mise à jour de la branche de travail. Demander l’accord avant une compilation de diffusion/release.
8. Après finalisation, étudier l’évolution vers le serveur web central hybride.

## 4. Exigences métier à préserver

### Organisation des stages
- Résidence médicale de quatre années.
- Quatre périodes annuelles : 1 février–30 avril ; 1 mai–30 juillet ; 1 août–30 octobre ; 1 novembre–31 janvier.
- Ordre de priorité des affectations : 4e année, puis 3e, 2e et 1re année.
- Les capacités des terrains sont définies par le responsable. Les conflits entre priorité et stage obligatoire doivent être signalés et faire l’objet d’une décision traçable.
- Terrains obligatoires/de base avant terrains optionnels.
- Empêcher la répétition d’un même terrain tant que tous les terrains obligatoires et de base ne sont pas accomplis ; les terrains optionnels ne doivent pas être une condition de cette règle.
- Rendre les conflits visibles en rouge et les répétitions autorisées en vert ; afficher les objectifs par terrain et année et l’état d’accomplissement clairement.

### Résidents et dossiers
- Importer des listes DOC/DOCX/PDF/XLS/CSV avec aperçu, validation et signalement des erreurs avant import.
- Ne jamais inventer l’historique de stages manquant.
- Le dossier résident doit pouvoir contenir les coordonnées, date/lieu de naissance, photo, résultats d’examens annuels, rattrapages, notes DEMS en deux parties, congés et jours restants/reportés, demandes et détails de stages à l’étranger et dates des stages passés/en cours.
- Congé annuel : 30 jours par année ; prévoir le calcul des jours utilisés, restants et reportés.
- Après réussite au DEMS, archiver le résident et le retirer de la liste active.
- Pour la promotion de 1re année : moyenne générale d’au moins 10/20 et aucune composante de module inférieure à 10/20. Pour les années 2 à 4, la décision appartient au Dr Dris et au Pr Benhocine.

### Comptes et audit
- Pr Benhocine et Dr Dris sont Super Administrateurs ; Dr Dris doit disposer du contrôle élargi convenu sur les comptes, paramètres, affectations, archives et dérogations.
- Prévoir journal d’audit des actions sensibles, gestion des comptes et rôles, et le flux de vérification par e-mail/code demandé.
- Les droits doivent être vérifiés côté serveur, pas seulement en masquant des boutons dans l’interface.

### Interface et langues
- Nom de l’application : **ResiManage**.
- Interface élégante, moderne et pratique, avec identité visuelle médicale/anesthésie-réanimation et une palette pas excessivement bleue.
- Utiliser la dernière image 3D fournie par l’utilisateur pour l’identité visuelle et l’icône selon les spécifications convenues ; médecin avec stéthoscope, sans croix.
- Choix Français, arabe et anglais sur l’écran d’accueil et après connexion ; mémoriser correctement la langue choisie.
- Prévoir l’affichage/masquage du mot de passe.
- Organiser les fonctions liées aux résidents sous un accès clair ; regrouper dans Paramètres la déconnexion, les comptes administrateurs, le journal d’audit, les sauvegardes et l’export CSV.
- Le pied de page doit utiliser le nom actuel ResiManage, pas l’ancien nom ResiTrack.

## 5. Stratégie de synchronisation locale — points à vérifier lors de l’implémentation

- Le PC Windows est la source centrale des données partagées.
- Le service de synchronisation doit être joignable uniquement depuis le réseau local autorisé, avec configuration claire du pare-feu Windows.
- Les appareils doivent être authentifiés et autorisés ; aucune ouverture non protégée sur tous les réseaux.
- Définir quelles données sont téléchargeables sur Android et quels rôles peuvent les modifier.
- Définir les règles en cas de modification du même dossier sur deux appareils, de suppression, de doublon, d’échec partiel ou de reconnexion.
- Montrer l’état de synchronisation et la date de dernière synchronisation ; conserver les erreurs pour diagnostic.
- Prévoir sauvegarde automatique et restauration testée de la base centrale.
- Ne pas déclarer la synchronisation prête tant que des tests sur deux appareils réels et des tests de coupure/reconnexion n’ont pas réussi.

## 6. Évolution future vers le serveur web

- Pas d’hébergement public maintenant.
- Après stabilisation locale, étudier une API sécurisée et une base centrale adaptée à l’hébergement, en préservant les données existantes.
- Le choix d’un hébergeur gratuit évoqué précédemment est une piste de test seulement, pas une décision de mise en production.
- Ne pas utiliser des données médicales réelles dans un hébergement de test avant analyse des obligations de confidentialité, de sécurité, de contrôle d’accès, de sauvegarde et de conformité applicables.

## 7. État honnête au moment de l’archivage

- La décision « local maintenant + synchronisation sur le réseau local ; serveur web plus tard » est validée et consignée.
- Ce registre est une archive de décisions et d’exigences, pas un rapport de tests.
- La présence effective d’un service de synchronisation LAN, de l’authentification réseau, de la résolution des conflits et du mode hors connexion reste à vérifier dans le code avant de les annoncer comme opérationnels.

## 8. Mise à jour du 18 octobre 2026 — première correction visuelle sur la référence confirmée

- **Version de référence confirmée par l’utilisateur :** branche `resimanage-2-work`, commit de départ `b3f6d3fc34532a1067f32a05f0560221874d2903`.
- Commit de correction visuelle : `876dcc5ee14e36855be3433814a3581748bca891`.
- Changements intégrés dans `app.py` :
  - Le symbole cœur animé de l’écran de connexion a été remplacé par l’image 3D déjà présente dans le dépôt, `static/resimanage-3d-icon.jpg`, avec un texte alternatif.
  - Le cadre photo du profil résident a été agrandi : largeur/hauteur adaptatives jusqu’à 240 px sur grand écran et 180 px sur petit écran.
- **Vérification :** les quatre remplacements ont chacun correspondu exactement à un emplacement dans le code. Les tests automatisés et l’affichage sur téléphone restent à vérifier après ce commit.
- **Aucune compilation APK/EXE n’a été lancée.** ResiManage 1 reste inchangée.
- Prochaine priorité : exécuter les tests automatiques déclenchés par le commit, puis auditer les fonctions et l’interface avant de traiter la synchronisation réseau. Le service Android actuel écoute sur `127.0.0.1` ; il ne constitue donc pas encore une synchronisation PC ↔ téléphone sur le réseau local.


## 9. Mise à jour du 19 octobre 2026 — compilation Android et smoke-test automatisés

- L’utilisateur a explicitement autorisé la compilation automatique des APK de test à chaque correction, afin d’accélérer le cycle de développement ; il peut compléter les essais sur son téléphone.
- Workflow modifié sur `resimanage-2-work` dans le commit `e66a9c7cf110a79f5b8107d47821181f1e77a14c` : tests Python, assemblage APK debug, lancement dans un émulateur Android API 35, vérification de l’activité au premier plan et détection d’exceptions fatales ; artefacts APK et preuves de test conservés 14 jours.
- À la rédaction de cette note, le commit workflow n’affichait pas encore de statut CI ; ne pas prétendre que le premier passage Android a réussi tant que le run et ses artefacts ne sont pas inspectés.
- Étape suivante de la feuille de route : audit des fonctions et de l’interface en corrigeant les anomalies confirmées, puis stabilisation Windows locale avant de concevoir la synchronisation LAN PC ↔ Android.


## 10. Mise à jour du 19 octobre 2026 — stabilisation Windows et pause des vérifications Android

À la demande de l’utilisateur, la vérification Android via GitHub Actions (émulateur, logs et inspection des artefacts APK) est **en pause jusqu’à l’intégration de l’ensemble des directives**. Ne pas relancer ni présenter ces contrôles comme accomplis pendant cette phase. La compilation et la vérification globales seront reprises à la fin.

Corrections appliquées sur `resimanage-2-work` :
- `c709b8c4f905bb3835b58a052c00cf4853004066` : le lanceur Windows place désormais la base SQLite et le secret dans `%LOCALAPPDATA%\\ResiManage\\data`, hors du dossier d’installation ; il sélectionne un port local libre et n’écoute que sur `127.0.0.1`.
- `e5a1bcedaf817a2e6c15be2c70c9646e81c06516` : le workflow Windows inclut les fichiers `static/` dans l’exécutable PyInstaller et réagit aux changements de ces ressources.
- `7e124468d133d70a99b11faea84a4af4d216dde2` : tests de régression ajoutés pour la persistance du secret et l’inclusion des ressources Windows.
- `d7f17f72c6d7c483a2626477d99657cb1ffdb69a` : README documentant l’emplacement des données et la sauvegarde avant essais.
- `94af435ae3c10d1526d11ba4ed1bd97042e5b595` : pied de page de connexion harmonisé avec le nom actuel « ResiManage » dans les trois langues.
- `02291d3df04852824a92c64929d9c74ad429b533` : assertion de non-régression pour le nom actuel dans le pied de page.

**État de vérification :** ces modifications ont été enregistrées sur GitHub ; les tests Windows et Python ne sont pas déclarés réussis car ils n’ont pas été exécutés dans le cadre de cette étape. La vérification Android reste volontairement suspendue. Étape suivante : poursuivre l’audit fonctionnel et la préparation du plan de synchronisation locale, sans lancer de contrôle Android.


Complément opérationnel à la pause Android :
- `915157322af55ee4556f0237466433597d762254` : les déclencheurs automatiques push/PR du workflow Android principal sont désactivés ; le workflow complet (y compris diagnostics et captures en cas d’échec) est conservé pour un lancement manuel en fin de programme.
- `0ac9b1792d25faa12155f41ce0c4f8508a295066` : le workflow de compilation APK séparé est lui aussi manuel uniquement.
- Les contrôles Python généraux peuvent encore se déclencher séparément via `ci.yml`; cela ne relance pas la compilation ni le smoke-test Android.


### Corrections complémentaires de cohérence visuelle
- `fd17860c01e3aebc9302f02180bcb28a26a26350` : correction du type MIME de l’icône navigateur : le fichier JPG est maintenant déclaré `image/jpeg` au lieu de `image/svg+xml`.
- `60035d69d877dc050126d89c87e12f740c4f8564` : test de régression pour empêcher le retour de ce mauvais type MIME.
- `b0961f2ae52643f242c5c9b2cc01d81c8949517c` : README mis à jour pour désigner l’image actuelle du médecin/stéthoscope 3D plutôt que l’ancien fichier SVG.
- Ces changements ont été enregistrés ; les tests ne sont pas déclarés exécutés/réussis. La vérification Android reste en pause.


## 11. Conception de la synchronisation hors ligne

- Document ajouté : `docs/SYNC_ARCHITECTURE_RESIMANAGE2.md` (commit `58797156c28bc5e793365a1635c10aba505d3e74`).
- Il fixe le PC Windows central, le mode hors connexion Android/PC secondaire, le VPN privé entre réseaux distincts, HTTPS, l’enrôlement/révocation des appareils, la synchronisation incrémentale idempotente, la résolution explicite des conflits, les tombstones, l’audit et les critères d’acceptation.
- **Ce document est une conception, pas une implémentation.** Aucun endpoint de synchronisation n’a été ajouté et le serveur reste local. L’exposition réseau reste désactivée par défaut.
- Ordre de travail : terminer la stabilisation Windows, puis implémenter l’API et le modèle de versions par étapes, avec données fictives et tests de coupure/conflit avant toute donnée réelle.

## 12. Éléments encore à fermer pendant l’audit fonctionnel

- Vérifier et compléter la gestion des comptes : l’interface actuelle permet la création/activation/désactivation et les paramètres permettent de changer le mot de passe courant ; l’édition du rôle et la réinitialisation du mot de passe d’un autre compte ne sont pas encore confirmées comme disponibles.
- Poursuivre la revue fonctionnelle des profils résidents, examens, congés, stages externes, règles d’affectation, archives DEMS, export/sauvegarde et traductions.
- Les tests Python et Windows restent à exécuter ; la validation Android demeure suspendue jusqu’à la fin des directives.


## 13. Audit — prérequis e-mail et gestion des comptes

- Document ajouté : `docs/EMAIL_VERIFICATION_SETUP.md` (commit `519e1d9725c4a16e79ef2f0085528654582c8c67`).
- Le code de vérification par e-mail existe, mais il dépend des cinq variables SMTP et aucun fournisseur/secret SMTP n’a été fourni. La livraison réelle n’est donc pas confirmée.
- L’inscription exige un e-mail, mais l’écran de connexion actuel accepte le nom d’utilisateur et non l’adresse e-mail : la connexion par e-mail reste à implémenter si elle est requise comme indiqué dans les directives.
- Le paquet Android ne propose pas encore de configuration SMTP sécurisée ; ne pas embarquer de secrets SMTP dans l’APK.
- La gestion des comptes permet actuellement de créer/activer/désactiver des comptes. L’édition du rôle et la réinitialisation du mot de passe d’un autre compte restent à finaliser dans l’interface.
- Ces points sont consignés comme **travaux restants**, pas comme fonctionnalités achevées. La vérification Android reste en pause.


### Amélioration UX — affichage des mots de passe à l’inscription
- `7e1701f0e80abfc070893dc20effd10eb2a443f0` : ajout de boutons d’affichage/masquage sur le mot de passe et sa confirmation dans le formulaire d’inscription, en cohérence avec l’écran de connexion.
- `2f18c013fed8515f95b9031530051dc7daacd953` : test de régression du formulaire d’inscription.
- Tests non exécutés ici ; validation Android toujours en pause.


### Cohérence de l’affichage des mots de passe
- `955390a15729639db2e1bf142178b6bca740d8d5` : ajout des commandes d’affichage/masquage sur les formulaires de première configuration, paramètres et création de compte administrateur.
- `1c7d327c76d2baa3c17d7754dcd97987ea2540e4` : tests de présence de ces commandes sur les formulaires administrateur.
- Ces changements restent non vérifiés par exécution à cette étape.


### Connexion par adresse e-mail
- `8ebe025e8de05edea9036d4248f1046bc7458184` : la recherche du compte à la connexion accepte désormais le nom d’utilisateur ou l’adresse e-mail enregistrée, sans tenir compte de la casse de l’e-mail.
- `22795868fb8f09ae5089d706528159384356dbab` : libellé de connexion clarifié en français, anglais et arabe.
- `cb6459ff2f0d0ec450f602260bdc1cd6e5e16162` : test de régression pour la connexion avec l’adresse e-mail.
- Le test n’a pas été exécuté à cette étape. L’envoi SMTP réel et la configuration sécurisée sur Android restent des points ouverts.


### Objectifs de stage — suivi d’avancement
- `f80b20d551a612891b1ac8a2247ff1085b7a60c9` : ajout d’un état `completed` avec migration additive de la base existante ; chaque objectif peut être marqué terminé ou à faire. L’affichage utilise rouge pour terminé et vert pour à faire, par service et année d’étude ; chaque changement est audité.
- `1de47aed5fb78422eee5c47343a34bfb87e2d1b2` : test de régression du changement d’état, des couleurs et du journal d’audit.
- Test non exécuté ici ; validation Android toujours en pause.


- `d5269a1017a3714e5167be5d073c09b56b6cfdfc` : le profil résident affiche lui aussi les objectifs en rouge lorsqu’ils sont terminés et en vert lorsqu’ils restent à faire.
- `1d4202d8a1d5922a0c33e52170ae37f82221217e` : test de régression de l’affichage des objectifs dans le profil.


### Exactitude de l’avancement des terrains
- `2a654556841b02fc91f26822f38588b4598ce55c` : le profil ne considère plus une affectation confirmée future comme un stage déjà terminé. Les historiques et affectations ne passent à « terminé » qu’après leur date de fin effective.
- `49ddf8c91055613f165c98e27edae1f4f9bd3cb4` : test de régression pour une affectation future.
- Tests non exécutés ici ; validation Android toujours en pause.


### Cohérence du nom de l’application
- `a20649cf807a5dd708916ed127bf79508018a9ce` : le message d’erreur de restauration n’utilise plus l’ancien nom générique « Rotation App » et mentionne maintenant ResiManage.
