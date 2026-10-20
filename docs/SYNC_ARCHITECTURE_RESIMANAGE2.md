# ResiManage 2 — architecture de synchronisation PC ↔ Android

Statut : **conception préparatoire, pas encore implémentée**. Ce document fixe une architecture de travail avant d’ouvrir le réseau à des données de résidents. Il ne constitue pas une promesse que la synchronisation fonctionne déjà.

## Décisions de départ

- Le PC Windows désigné comme serveur central conserve la base de référence.
- L’application Android conserve une copie locale dans le stockage privé de l’application et doit rester utilisable hors connexion. La base SQLite n’est pas encore chiffrée au niveau du fichier ; le chiffrement au repos doit être évalué avant tout déploiement avec données réelles.
- Les deux PC et le téléphone peuvent être sur des réseaux Internet différents. La connexion entre eux passe par un VPN privé (par exemple WireGuard ou Tailscale) ; aucun port de l’application ne doit être exposé publiquement directement à Internet.
- L’API de synchronisation doit utiliser HTTPS même à travers le VPN, avec authentification distincte par appareil et contrôle de rôle côté serveur.
- Ne jamais synchroniser le fichier SQLite brut en le copiant ou en fusionnant des fichiers DB : les modifications passent par une API transactionnelle.
- Les données personnelles, photos, notes, identifiants et secrets ne doivent jamais apparaître dans les journaux techniques ou les dépôts Git.

## Architecture proposée

1. **Serveur central Windows** : service local démarré avec ResiManage, base SQLite centrale et dossier de données séparé du dossier du programme. Écoute uniquement sur l’interface VPN ou une interface explicitement autorisée, jamais sur toutes les interfaces par défaut.
2. **Clients** : ResiManage Windows secondaire et Android utilisent une file d’opérations locales lorsque le réseau est absent. Chaque opération reçoit un identifiant unique, un appareil d’origine, une date, un type d’objet et la version de base connue.
3. **API versionnée** : endpoints conceptuels `/api/sync/v1/bootstrap`, `/push`, `/pull` et `/status`. Ces routes ne sont pas encore présentes et ne doivent pas être considérées comme actives.
4. **Authentification des appareils** : enrôlement explicite par un administrateur, jeton révocable propre à chaque appareil, stockage du hash du jeton côté serveur, expiration/rotation, limitation des tentatives et révocation immédiate.
5. **Transport** : TLS obligatoire ; validation stricte de la taille, du type, des champs et des identifiants ; contrôle de rôle sur chaque opération ; protection contre rejeu par identifiant idempotent.
6. **Audit et diagnostic** : journaliser le type d’action, l’appareil, l’heure, le résultat et l’identifiant de corrélation. Ne pas journaliser les mots de passe, codes de vérification, jetons, notes médicales ou contenu des dossiers.

## Règles de synchronisation

- **Affectations, capacités, décisions de promotion, résultats DEMS et rôles** : opérations sensibles. Elles doivent être validées par le serveur central avec les règles métier courantes. Une décision nécessitant deux responsables ne peut jamais être approuvée par une simple synchronisation.
- **Dossiers résidents, examens, congés, stages externes et historique** : chaque modification doit être versionnée et auditée ; aucune fusion silencieuse en cas de conflit.
- **Conflits** : si la version reçue ne correspond pas à la version de base, le serveur renvoie un conflit structuré. Les champs simples peuvent proposer une comparaison ; les affectations, examens, décisions, congés et suppressions exigent une résolution explicite par un responsable autorisé.
- **Suppressions** : utiliser des marqueurs de suppression versionnés (tombstones) plutôt que d’effacer immédiatement les enregistrements nécessaires à la propagation.
- **Idempotence** : renvoyer plusieurs fois la même opération ne doit pas créer de doublons ni répéter une décision.
- **Photos** : transférer les fichiers séparément avec limite de taille, validation du format, empreinte, reprise après interruption et suppression contrôlée ; la base ne contient que la référence et les métadonnées.
- **Sauvegardes** : sauvegarde automatique avant migration de schéma et avant restauration ; vérification d’intégrité ; test de restauration périodique.

## Phases obligatoires

1. Terminer la stabilisation de l’application Windows locale et vérifier les chemins de données/sauvegarde.
2. Définir le modèle de versions et la journalisation des changements, avec migration rétrocompatible de la base existante.
3. Implémenter l’enrôlement des appareils et l’API sur le PC central, d’abord avec données fictives.
4. Implémenter la file hors connexion et la synchronisation incrémentale sur un seul client de test.
5. Tester les conflits, la révocation d’appareil, les pertes réseau, les doublons, la reprise, les sauvegardes et la restauration.
6. Ajouter Android et le second PC, puis tester sur deux réseaux distincts via VPN.
7. N’autoriser des données réelles qu’après revue de sécurité, sauvegarde vérifiée et tests de bout en bout réussis.

## Critères d’acceptation

- Aucun accès depuis Internet public sans VPN et authentification.
- Un appareil révoqué ne peut plus pousser ni tirer de données.
- Une interruption réseau ne perd pas les opérations en attente ; la reprise ne duplique pas les changements.
- Un conflit sensible est visible et audité ; aucune règle métier n’est contournée.
- Les données locales et centrales restent récupérables après échec de synchronisation.
- L’état de synchronisation affiche au minimum : connecté/hors connexion, dernière réussite, opérations en attente, conflits à résoudre et dernière erreur sans données personnelles.
- Des tests de bout en bout sur Windows central + Windows secondaire + Android passent avant toute déclaration de mise en service.

## Limites connues à ce stade

- Le serveur Android actuel écoute sur `127.0.0.1:5000` et n’est pas un serveur de synchronisation réseau.
- Le lanceur Windows local est prévu pour ouvrir une interface sur boucle locale ; l’exposition à une interface VPN doit être conçue séparément et rester désactivée par défaut.
- Il n’existe pas encore d’API de synchronisation, de file d’attente distribuée, de gestion de conflits ni d’enrôlement d’appareils. Aucun de ces éléments ne doit être présenté comme opérationnel.


## État actualisé avant implémentation de la synchronisation

La base locale évolue encore : les notes d’examen distinguent maintenant `exam_type` et `attempt` (virtuel, réel, rattrapage et sessions DEMS), et les contrôles de compte permettent des changements de rôle/mot de passe audités. Ces champs et ces règles doivent être inclus dans le modèle de versions avant de créer l’API ; il ne faut pas démarrer une réplication qui ne comprendrait que les anciens champs.

**État d’exécution :** la synchronisation réseau reste non implémentée. Le travail doit commencer après la stabilisation Windows et la validation de la base locale. La vérification Android via GitHub Actions est suspendue à la demande de l’utilisateur jusqu’à la fin de toutes les directives ; aucun endpoint de synchronisation ne doit être exposé en attendant la conception complète de l’enrôlement, de TLS/VPN, des opérations idempotentes et des conflits.


## Journal local de changements — première brique ajoutée (20 octobre 2026)

Le code local crée maintenant une table `sync_change_log` et des déclencheurs SQLite pour les entités métier (résidents, terrains, périodes, capacités, affectations, historique, décisions, examens, objectifs, votes/archives DEMS, congés, stages externes et audit). Les insertions/modifications journalisent un instantané JSON de la ligne; les suppressions créent un tombstone avec l’identifiant. Les tables `users`, mots de passe et sessions ne sont pas incluses.

Cette brique fournit une séquence locale pour préparer le pull incrémental, mais **ne réalise pas la synchronisation** : aucun endpoint API authentifié, enrôlement d’appareils, transfert photo, file d’opérations Android, résolution de conflits, TLS/VPN ou bootstrap initial n’est encore disponible. Les tests de régression du journal doivent réussir avant de poursuivre l’API.


## API de lecture et enrôlement — phase serveur partielle

Une première API authentifiée est maintenant présente :

- Écran Super Admin `/sync-devices` pour générer un jeton aléatoire par appareil, stocker uniquement son SHA-256, afficher le jeton une seule fois dans la réponse d’enrôlement et révoquer un appareil.
- `GET /api/sync/v1/status`, `/bootstrap?entity=...&after_id=...&limit=...` et `/pull?after_seq=...&limit=...` permettent une lecture initiale et incrémentale avec bearer token.
- Les appareils enrôlés en mode `read_write` peuvent envoyer des lots limités via `POST /api/sync/v1/push`: idempotency key, contrôle de conflit par curseur, validation de forme/domaine et réponses `applied/conflict/rejected`. Les comptes read-only ne peuvent pas pousser. Les affectations poussées sont ramenées à `pending` pour décision centrale.
- Le push ne couvre pas encore les votes de promotion/DEMS, l’archive diplômés, ni l’ensemble des règles de workflow. L’API refuse le HTTP depuis une adresse distante (426); HTTP loopback reste autorisé pour les tests locaux.
- Le lanceur Windows peut écouter sur une IP VPN privée précise, avec certificat/clé TLS configurés via `RESIMANAGE_BIND`, `RESIMANAGE_PORT`, `RESIMANAGE_TLS_CERT` et `RESIMANAGE_TLS_KEY`. Les wildcard binds et adresses IP publiques sont refusés. Par défaut, il reste sur `127.0.0.1`.

**La synchronisation complète n’est toujours pas réalisée.** L’APK Android a maintenant un écran manuel `/sync`, un bridge natif qui chiffre URL/jeton avec Android Keystore, et un client Python qui peut bootstrap/pull et pousser les entités autorisées. Mais le client Android n’a pas encore été compilé/testé sur téléphone; il refuse le premier appairage si des données résidents/stages existent déjà, n’a pas d’interface de résolution de conflits, n’effectue pas de synchronisation planifiée et ne pousse pas encore les votes officiels/archives DEMS. Ne déployer l’API que sur VPN privé et ne pas l’exposer sur Internet.


### Synchronisation des photos (première implémentation)

- Le serveur expose `GET /api/sync/v1/photo/<resident_id>` et `PUT /api/sync/v1/photo/<resident_id>?base_seq=...` avec le même jeton appareil. L’upload vérifie le type image, limite à 4 MB, normalise en WEBP et refuse un upload si la version de la fiche a changé depuis le dernier pull.
- Le client Android source télécharge les photos lors du bootstrap/pull, les range dans son dossier privé `resident_photos`, et les envoie après l’upsert de la fiche résidente. Les fichiers locaux et le curseur de ligne sont suivis séparément.
- Ce code source doit encore être compilé et testé sur un téléphone; aucun run Android n’a été lancé. La résolution interactive de conflit de photo et le nettoyage des anciennes versions de fichiers restent à faire.
