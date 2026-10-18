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
- Ne pas lancer de compilation APK ou EXE sans demande explicite de l’utilisateur. Une demande de compilation doit viser une version dont les corrections ont été intégrées et vérifiées.
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
7. Effectuer des tests complets avec des données fictives ; préparer une compilation de test uniquement après demande explicite.
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
