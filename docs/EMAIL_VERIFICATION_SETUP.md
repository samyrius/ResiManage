# Configuration de la vérification par e-mail

Statut : le flux de code de vérification existe dans l’application, mais il dépend d’un serveur SMTP externe. Il ne faut pas le considérer comme prêt pour une installation neuve tant que l’envoi réel n’a pas été configuré et vérifié.

## Variables requises

Le code lit les variables d’environnement suivantes :

- `RESITRACK_SMTP_HOST` : serveur SMTP du fournisseur de messagerie.
- `RESITRACK_SMTP_PORT` : port SMTP STARTTLS, généralement 587 selon le fournisseur.
- `RESITRACK_SMTP_FROM` : adresse d’expédition vérifiée.
- `RESITRACK_SMTP_USER` : identifiant SMTP.
- `RESITRACK_SMTP_PASSWORD` : mot de passe d’application ou secret SMTP fourni par le service.

Ne jamais mettre ces valeurs dans Git, dans une capture d’écran, dans le code source, ni dans un fichier de configuration partagé. Utiliser un mot de passe d’application lorsque le fournisseur le propose. Le serveur doit accepter STARTTLS ; les paramètres exacts dépendent du fournisseur choisi.

## Vérification avant utilisation

1. Configurer les variables dans l’environnement du processus qui lance ResiManage.
2. Redémarrer complètement l’application pour que les variables soient prises en compte.
3. Faire un test avec une adresse de test contrôlée.
4. Confirmer la réception, le délai d’expiration de 10 minutes et le blocage après 5 tentatives.
5. Vérifier qu’un échec SMTP ne crée pas un compte actif et ne conserve pas une inscription en attente inutilisable.

## Limite pour les paquets Android/Windows

- Le lanceur Windows hérite des variables d’environnement du processus qui le démarre ; une configuration doit donc être faite sur le poste avant lancement.
- Le paquet Android actuel ne présente pas d’écran sécurisé de configuration SMTP et ne doit pas être supposé capable d’envoyer des codes de vérification dans une installation vierge. Il faut définir une méthode d’envoi adaptée avant de déclarer cette fonction prête sur téléphone.
- Les identifiants SMTP ne doivent pas être intégrés à l’APK ni à un dépôt public. Pour un déploiement multi-appareils, préférer un service de vérification côté serveur, accessible uniquement par le VPN privé et protégé par TLS et authentification.

## État

La configuration SMTP n’a pas été fournie et l’envoi réel n’a pas été testé dans le cadre de cette étape. Cette note décrit les prérequis ; elle ne prétend pas que la livraison des e-mails fonctionne déjà.
