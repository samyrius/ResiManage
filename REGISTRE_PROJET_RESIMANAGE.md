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


### Protection des données existantes lors de la migration Windows
- `178885ca3cc02b46760d40e63b2f40edb5723f77` : migration de première exécution depuis l’ancien dossier de l’exécutable vers le dossier utilisateur : copie SQLite via l’API backup SQLite, photos copiées sans suppression des sources, et reprise de l’ancienne clé secrète si elle existe. La migration n’écrase pas une base cible déjà présente.
- `3bfce1aeea2238ef0d8f8e5e217bf8ccb934beea` : test de migration de la base et des photos.
- `29a6d95adaa2b47d4af88825519900f058c4aace` : documentation de la migration.
- Tests non exécutés ici ; la sauvegarde de l’application reste obligatoire avant des essais avec données réelles.


- `e787cff6a42b71b5256b8174972a3c1ac75c64f1` : durcissement de la migration des photos : les fichiers déjà présents dans le nouveau dossier ne sont jamais écrasés ; seuls les fichiers manquants sont copiés.
- `39752a13979f77a4eb277e4a318f23785e260748` : test couvrant la conservation des fichiers plus récents et la copie des photos manquantes.


- `f142bcd03a913664b72a473a29ebe8b9ede5ae73` : ajout d’un test de migration depuis une ancienne base dont la table `objectives` ne possède pas encore la colonne `completed`.


### Correction de la persistance de langue
- `43b5d218fc25db008ade2118da3b8d57aba57323` : la langue sélectionnée est conservée dans la session lors de la connexion réussie au lieu d’être effacée avec le reste de la session. Cela corrige la cause probable du retour à l’arabe après sélection du français ou de l’anglais.
- `5e45f4dc123eafbf8a8f8b96b6348afcbeb7640b` : test de régression de la persistance de la langue après connexion.
- Test non exécuté ici ; validation Android toujours en pause.


### Sélecteurs de langue avec drapeaux
- `7284ceb8a11fa29ec4c2508acaa68ddfb275d65f` : ajout du drapeau algérien pour l’arabe sur l’écran de connexion et dans la navigation après connexion ; les drapeaux français et britannique restent visibles.
- `6cfe34441c0ce09d3ab864beb8bc945f675f649a` : test des trois drapeaux sur les deux écrans.


### Ressources visuelles manquantes dans le paquet Android
- `66fca1d6e6c48cbe89cc19e2aa88205a7e5ce70d` : correction du script Gradle : les ressources du dossier `static/`, dont l’image 3D utilisée dans l’en-tête et le favicon, sont maintenant copiées vers le répertoire Python embarqué d’Android.
- `873fc85a295fcf86f85c8c5ef192b300330bc2b1` : test de régression de la présence de la tâche de copie.
- Le paquet Android n’a pas été reconstruit conformément à la pause demandée ; cette correction reste à confirmer lors de la vérification finale.


### Versionnement du paquet Android
- `234ec5a475b411e01c7571ddb08cb42f9455d07f` : version Android passée à `versionCode 2` / `versionName 2.0.0` afin d’identifier clairement cette ligne de travail et de permettre une mise à jour par-dessus la version de test précédente.
- `edd592a9c0e1dcd9845543b008f87636605e0029` : test de cohérence du numéro de version.
- Aucune compilation n’a été lancée ; vérification Android en pause.


- `1b63bfc430408768dcdf922c5a4451208428b174` : nom du projet Gradle Android harmonisé avec `ResiManage` au lieu de `RotationApp`.
- `6e487bd1fe796705c60aaebc6af45b55ab7a58f9` : test de cohérence du nom du projet Android.


### Précision sur les examens — travail restant
- La saisie actuelle enregistre une matière avec deux notes (théorie/pratique) par année, et le premier passage en année 1 utilise ces notes pour le calcul de promotion.
- Le formulaire ne distingue pas encore explicitement les catégories « virtuel », « réel », « rattrapage » et les sessions DEMS ; les différentes tentatives d’une même matière ne sont pas conservées comme tentatives distinctes.
- Avant d’ajouter ces catégories, il faut préserver l’historique des notes et définir sans ambiguïté quelle tentative sert au calcul de progression (notamment quand un rattrapage remplace une note insuffisante). Ne pas écraser les notes existantes ni modifier silencieusement les règles de promotion.


- `61596ccbac909e1b6f780d0d6c3a9babf81eabd8` : connexion par e-mail limitée aux adresses marquées comme vérifiées ; le nom d’utilisateur reste utilisable.
- `8acf0873c8e9ebaeffb1632f6add8a9acc8de6c0` et `6f0e6148650a1507f15d9245c189abf05b3fb42d` : tests pour accepter un e-mail vérifié et rejeter un e-mail non vérifié.


- `50fb078514b5be850b5c33add9affa5ecb66f016` : documentation e-mail mise à jour pour préciser que la connexion par e-mail est prise en charge uniquement après vérification ; l’envoi SMTP réel reste à configurer.


### Dossier résident — congés annuels
- `711f63e4e80f7fbac88832161702671ee1b0569a` : ajout dans le profil résident du tableau des congés (dates de début/fin, jours, notes) et du bilan acquis/utilisé/restant, en complément de la page globale de gestion des congés.
- `0e0175964c722abc39079595f5ad33eee02021fd` : test de régression du détail et du solde des congés dans le profil.
- Test non exécuté ici ; vérification Android toujours en pause.


### Dossier résident — stages à l’étranger
- `b30c2ca283efead33ad49c70f5218493b9de40eb` : le profil résident affiche désormais les stages à l’étranger avec destination, hôpital, pays, type, dates, responsable, notes et statut.
- `93140be81fbac2df1ffe757c90e2302f8ac2ca80` : test de régression du détail des stages externes dans le profil.

- `1076e08c3521cf99641495e002bf8886d84c35a1` : clarification du statut de chiffrement : la base SQLite Android est dans le stockage privé de l’application, mais le fichier DB n’est pas encore chiffré au repos ; ce point doit être évalué avant l’usage avec des données réelles.


### Mise à jour de la documentation Android et e-mail
- `b803e356c41d78f7e98335c4f66a03363e5202c5` : le guide Android indique que les workflows sont manuels jusqu’à la revue finale.
- `69abd473bcd06bacfec8012298b8ae85829c1dd0` : correction du nom d’artefact dans les instructions d’installation.
- `900b370cf4222e31803e4223d949e0cfdcf75e9a` : suppression de l’affirmation non vérifiée selon laquelle le dernier APK serait déjà construit ; le guide indique honnêtement que les dernières modifications attendent une compilation et un test finaux.
- `50fb078514b5be850b5c33add9affa5ecb66f016` : documentation SMTP mise à jour pour mentionner la connexion par e-mail vérifiée.

- `a99b94237d7deb3378093d092730c3a1cc389cf4` : README clarifié sur la branche de référence active `resimanage-2-work`, le caractère historique des tests anciens et la pause des workflows Android.

- `06f1223f12eaeeff3cc7597fd081c73d076e2015` : la colonne d’état des objectifs est maintenant définie dès la création d’une base neuve ; la migration additive reste en place pour les bases existantes.

- `91d3fe3a004b9c5215cab5758377f917a1b7f326` : le workflow Windows exécute maintenant la suite de régression Python sur Windows avant la création de l’exécutable et de l’installateur. Cette vérification Windows est distincte des workflows Android, toujours manuels uniquement.


## 14. Tableau de clôture — à reprendre dans cet ordre

### Corrections déjà intégrées au code
- Langue conservée après connexion ; drapeaux 🇩🇿 🇫🇷 🇬🇧 sur les deux écrans.
- Connexion possible avec identifiant ou e-mail vérifié ; boutons d’affichage du mot de passe sur les formulaires principaux.
- Objectifs par service/année avec état terminé/à faire, couleurs demandées et audit.
- Profil résident enrichi avec solde et historique des congés, stages à l’étranger, notes, affectations et objectifs.
- Les affectations futures ne sont plus affichées comme des stages terminés dans le profil.
- Ressources 3D copiées dans le paquet Android ; version du paquet portée à 2.0.0.
- Lanceur Windows : données persistantes dans le profil utilisateur, migration non destructive des anciennes bases/photos et tests Python prévus avant packaging.
- Icône navigateur, pied de page et documentation harmonisés avec le nom ResiManage.
- Vérification Android désactivée automatiquement et conservée en mode manuel uniquement.

### Travaux restant à finaliser avant la vérification Android
1. Terminer la gestion des comptes (modification de rôle et réinitialisation du mot de passe d’un autre compte).
2. Définir une configuration SMTP sécurisée et vérifier l’envoi réel des codes, notamment pour Android sans intégrer de secrets à l’APK.
3. Revoir et valider les règles métier des sessions d’examens (virtuel, réel, rattrapage, sessions DEMS) et les critères de progression. Le modèle de données et les champs de saisie sont intégrés, mais la suite de tests doit être exécutée avant validation.
4. Terminer la stabilisation Windows, examiner le résultat du workflow Windows et confirmer les tests Python.
5. Implémenter la synchronisation réelle PC central ↔ PC secondaire ↔ Android, avec VPN, authentification par appareil, mode hors connexion et résolution des conflits. Le document de conception existe ; le service n’est pas implémenté.
6. Lancer manuellement les workflows Android, vérifier l’APK, les logs et les captures de l’émulateur ; ensuite tester sur le téléphone réel.
7. Faire la revue finale des exigences, des sauvegardes/restaurations et de la sécurité avant d’utiliser des données réelles.

**État honnête :** des corrections importantes sont enregistrées sur `resimanage-2-work`, mais le programme n’est pas encore terminé. Aucun test Python/Windows n’est déclaré réussi sans résultat effectif ; aucun nouveau test Android n’a été lancé pendant la pause.

- `51b76964a5067445518626fb2946331cc0f69560` : correction du solde de congés quand un résident possède déjà des droits enregistrés pour une année future : l’année courante conserve son droit de 30 jours dans le profil et la page Congés initialise aussi l’année courante. Un test dédié reste à ajouter/exécuter.


## 15. Gestion des comptes et configuration SMTP — 19 octobre 2026

- `aa44790c0a303d8340cb72f62a6cc3251bf29df9` : configuration SMTP renommée avec priorité à `RESIMANAGE_SMTP_*`, tout en gardant temporairement la compatibilité avec `RESITRACK_SMTP_*`. Le port SMTP invalide produit maintenant une erreur claire. Aucun secret n’est intégré dans le code ou dans l’APK.
- `58fb511e16dd20089fd14125b2db09d0c99a20e3` : tests de régression ajoutés pour la configuration SMTP actuelle, le chiffrement TLS, l’absence de secret dans le message et le rejet d’un port invalide.
- `6f23e85be2dd8fa363786087c30e1550cfcda3df` : README complété avec les variables d’environnement SMTP et la consigne de ne pas placer les identifiants dans le dépôt ou l’APK.
- `5eb165434abaf70476e1894ff45169ac21c7c878` : page de gestion des comptes complétée avec modification de rôle et réinitialisation du mot de passe d’un autre compte. Les changements sont journalisés ; les comptes Benhocine et Dr Dris ne peuvent pas être rétrogradés, et le dernier Super Admin actif est protégé.
- `cba3d07c436d6d11c1f68eb2ac9b2c6756ebe5e2` : tests de régression ajoutés pour les changements de rôle, la réinitialisation du mot de passe, le journal d’audit et les protections de rôle.
- Les tests n’ont pas été exécutés ici ; leur présence ne signifie pas qu’ils passent. Les workflows Android restent manuels uniquement et ne doivent pas être lancés avant la fin du programme.


### Migration Windows non destructive
- `5bd699c3842bd46bbb35119b38fab584dfdc88b4` : ajout d’un test qui vérifie que la première ouverture de ResiManage 2 copie l’ancienne base SQLite, les photos des résidents et le secret de session vers le dossier utilisateur, tout en conservant les fichiers d’origine. Ce test n’a pas encore été exécuté.


## 16. Historique des examens et DEMS — 19 octobre 2026

- `049ca2eb2cd0c95f9bc58eab4e25b8c9025073f5` : migration additive des champs `exam_type` et `attempt`; les anciennes notes sont conservées comme session réelle, tentative 1.
- `bbcba1b831e5081fa21b5cb909421262f35026f4` : l’enregistrement permet de distinguer virtuel, réel, rattrapage et sessions DEMS ; les notes sont séparées par type de session et numéro de tentative. Les sessions DEMS sont réservées à l’année 4.
- `3fb2c1b36a4fdc4f3a231f3e90b48b9fff5ca04f` : formulaire et tableau d’examens affichent les sessions, tentatives et deux composantes des notes. Pour l’insertion DEMS, les deux champs représentent les deux parties de la note.
- `b7fe279c6bf714a4dbe475cd870983f3f291ecb2` : correction de placement des migrations SQLite, exécutées en Python après la création de la table et non à l’intérieur du script SQL.
- `6112043d39b636ef4abb247175bc067a11d4d998` : tests ajoutés pour la conservation de plusieurs sessions, l’utilisation du rattrapage dans l’évaluation de première année et les deux notes d’insertion DEMS.
- Règle de progression conservée : moyenne d’au moins 10/20 et chaque composante au moins 10/20 ; les notes virtuelles ne déterminent pas l’avancement. Le rattrapage remplace le résultat réel du module lorsqu’il existe. Ce choix doit être validé lors de la revue finale.
- Aucun test n’est déclaré passé. La vérification Android reste en pause jusqu’à la fin de toutes les directives.


### Protection supplémentaire des décisions de promotion
- `e08f0f1be41f28aaae90d6ae736ac44dcc54d662` : l’évaluation de première année exige désormais des notes réelles ou de rattrapage pour chaque module déjà enregistré ; les notes virtuelles seules ne suffisent pas pour un module.
- `cdc602b02660b061f85ad96ee052264f0ba3fdcd` : test de non-régression pour empêcher le passage en deuxième année si un module n’a que des notes virtuelles.
- Cette vérification supplémentaire est enregistrée, mais elle n’a pas été exécutée. La suite Android demeure suspendue.


- `52a2f36a75065848671e77f1b0b5778d506d05c9` : guide de configuration SMTP aligné avec les noms `RESIMANAGE_SMTP_*` ; la compatibilité avec les anciens noms reste explicitement temporaire. L’envoi réel n’est toujours pas testé, car aucun compte SMTP n’a été fourni.


## 17. Revue de la suite Python/Windows — 19 octobre 2026

Les résultats des workflows Python et Windows (pas Android) ont mis en évidence des tests obsolètes et un cas de verrouillage SQLite sous Windows. Corrections enregistrées :
- `4bd83af62bbfc233870dadd03d239e4f21d9a29d` : les sélecteurs de langue après connexion affichent les drapeaux français et anglais, et le message de notes invalides conserve un texte explicite.
- `d3b2fe0043df2745f56ab0c9046738eaa098427a` : assertions de tests alignées avec le favicon JPG, le lanceur qui écoute sur la boucle locale via `make_server`, et fermeture explicite d’une connexion SQLite dans le test de restauration Windows.
- `483e33a5878f68522c475f8941ade39134d99011` : le workflow Windows se déclenche aussi quand les tests changent ; le texte d’installation précise le vrai dossier de données `%LOCALAPPDATA%\\ResiManage\\data`.
- Les workflows Python et Windows ont été relancés automatiquement après ces corrections et leur résultat est en attente. La vérification Android reste manuelle uniquement et n’a pas été relancée.


- `c4e0dda3cdd98ed7bc0d609e60a89b42d5811fbc` : correction d’une assertion UTF-8 du pied de page ; l’échec venait de la chaîne de test, pas du rendu de l’application.
- `2d020cf192eb8ee268f348d67126440f02311e52` : document de synchronisation actualisé pour inclure les nouveaux champs d’examens et les contrôles de comptes comme prérequis de versionnement. La synchronisation reste non implémentée et aucune API réseau n’est activée.


- `9c79393c026840471418c5a6ea54198b159b564c` : le profil résident utilise maintenant une photo de 240 px sur téléphone et place les informations sous la photo au lieu de les comprimer à côté.
- `7ab0a8ddbd1dbdf1b7a342c2332432806f7b7931` : test de non-régression mis à jour pour cette disposition mobile plus lisible. La validation est en attente du workflow Python/Windows ; Android reste suspendu.
