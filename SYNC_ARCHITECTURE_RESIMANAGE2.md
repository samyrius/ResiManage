# ResiManage 2 — plan de synchronisation PC ↔ Android

## Objectif demandé

Permettre à deux PC Windows situés sur des réseaux différents et à un téléphone Android de travailler sur les mêmes dossiers, tout en continuant à fonctionner hors connexion. La synchronisation doit être bidirectionnelle, sécurisée, traçable et ne jamais écraser silencieusement une modification concurrente.

## Architecture cible

- **Base locale par appareil :** chaque installation conserve sa base SQLite et les photos localement ; les écrans métier restent utilisables hors connexion.
- **Point de synchronisation central :** un service HTTPS authentifié, hébergé sur un serveur contrôlé par l’établissement ou un serveur privé. Les appareils se connectent sortants, donc pas besoin d’ouvrir un port entrant sur les PC.
- **Réseau sécurisé :** privilégier un VPN privé (par exemple WireGuard/Tailscale géré par l’établissement) et TLS même à travers le VPN. Ne pas exposer directement SQLite, SMB ou le serveur Flask de développement sur Internet.
- **Journal de changements :** chaque modification métier crée un événement durable avec un identifiant unique, appareil, utilisateur, horodatage UTC, type d’objet, version précédente et version résultante. Les événements sont idempotents afin qu’une répétition réseau ne duplique pas les données.
- **Conflits explicites :** si deux appareils modifient le même dossier depuis la même version, le serveur conserve les deux propositions dans une file de conflits ; aucun écrasement silencieux. Les comptes autorisés choisissent la version à retenir et cette décision est auditée.
- **Fichiers photo :** transfert séparé, contrôlé par empreinte SHA-256 et taille maximale ; la base ne reçoit qu’une référence stable.
- **Sauvegardes :** sauvegarde automatique côté serveur, rétention définie et restauration testée ; sauvegarde locale avant migration et avant toute restauration.
- **Sécurité :** comptes individuels, rôles existants, sessions/jetons révocables, TLS, limites de débit, journaux sans mots de passe ni codes de vérification. Les secrets restent dans les variables d’environnement ou un gestionnaire de secrets, jamais dans Git ni dans l’APK.

## Règles de synchronisation

1. Les données de référence partagées (terrains, périodes, capacités et paramètres) sont versionnées ; une modification de capacité déclenche un contrôle de conflits avant publication.
2. Les dossiers résidents, notes, congés, stages externes, affectations, votes et décisions portent des versions distinctes. Une décision d’affectation ou de promotion est toujours auditée.
3. Les enregistrements historiques et les entrées d’audit sont append-only autant que possible ; les corrections ajoutent un événement plutôt que d’effacer l’historique.
4. Les suppressions sont représentées par des tombstones versionnés afin qu’un appareil resté hors ligne ne ressuscite pas un enregistrement supprimé.
5. Chaque appareil affiche l’état « Hors connexion », « À synchroniser », « Synchronisation en cours », « Conflit à résoudre » ou « Synchronisé », avec la date de dernière synchronisation réussie.
6. Le serveur refuse les données provenant d’un client qui n’a pas le droit d’effectuer l’action correspondante ; masquer un bouton dans l’interface n’est pas une protection suffisante.

## Étapes d’implémentation

1. Inventorier et versionner le schéma SQLite, identifier les tables métier et ajouter des identifiants stables / métadonnées de version sans perdre les bases existantes.
2. Créer le journal local des changements et les tests de migration / idempotence.
3. Créer l’API centrale d’authentification et de synchronisation, avec autorisation côté serveur et audit.
4. Implémenter la synchronisation incrémentale et les tombstones ; tester les répétitions réseau, les déconnexions et la reprise.
5. Ajouter l’interface de conflits et les règles de résolution pour affectations, capacités, notes et décisions.
6. Synchroniser les photos, puis ajouter les sauvegardes automatiques et la restauration vérifiée.
7. Tester les scénarios multi-appareils sur un réseau de test, y compris une longue période hors ligne, avant de l’utiliser avec les données réelles du CHU.

## Conditions de mise en production

- Aucun secret ni donnée réelle de résident dans les logs ou le dépôt.
- Migration testée sur une copie d’une base existante et retour arrière documenté.
- Scénarios de conflit testés automatiquement.
- Sauvegarde restaurée avec succès sur une installation vierge.
- Vérification Android et compilation APK uniquement après la fin de l’intégration des autres directives, conformément à la demande de l’utilisateur.

## État

Ce document définit la cible technique, pas une fonctionnalité de synchronisation déjà active. Tant que les étapes ci-dessus ne sont pas implémentées et testées, les installations locales ne doivent pas être présentées comme synchronisées entre elles.
