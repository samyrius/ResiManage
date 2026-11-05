# Refonte de la navigation intérieure — 5 novembre 2026

## Problème constaté

La navigation principale possède cinq accès directs, mais le dernier ouvre un catalogue long. Les outils y sont présentés en plusieurs grands blocs, avec une recherche qui ne réduit que les liens après chargement. Sur mobile, cette organisation impose de parcourir verticalement une page longue pour trouver une fonction. Les écrans métier contiennent aussi des explications parfois longues, mais cette première intervention cible l'architecture d'accès sans réécrire la logique métier.

## Principes retenus

- Conserver les cinq accès principaux et les cinq commandes fixes mobiles : Accueil, Résidents, Stages, Gardes, Outils.
- Remplacer le libellé ambigu « Plus » par « Outils » dans les sept thèmes.
- Dans Outils, afficher une barre de recherche globale et quatre catégories compactes : Résidents, Stages, Formation, Administration.
- Afficher une seule catégorie à la fois. La recherche, elle, explore toutes les fonctions, sans obliger à changer de catégorie.
- Garder les accès directs et les URL existantes : aucune route métier n'est supprimée ni renommée.
- Conserver les règles d'autorisation existantes : les outils d'administration et de validation restent réservés au Super Admin.
- Conserver les sept présentations visuelles, mais leur donner exactement la même organisation fonctionnelle.
- Réduire les textes d'introduction au strict nécessaire : titre, recherche, catégories, actions.

## Organisation cible

| Accès | Contenu direct |
|---|---|
| Accueil | Indicateurs et raccourcis vers les tâches fréquentes |
| Résidents | Liste et fiches résidents |
| Stages | Tableau de répartition et organisation des stages |
| Gardes | Calendrier mensuel des gardes |
| Outils → Résidents | Import des listes, formulaires vierges |
| Outils → Stages | Services/terrains, capacités, affectations, historique, congés, stages externes |
| Outils → Formation | Examens et promotions, objectifs, DEMS, synthèse, décisions autorisées |
| Outils → Administration | Paramètres, utilisateurs, synchronisation, appareils, audit, sauvegarde, export, restauration, corbeille (Super Admin) |

## Comportement de recherche

- La recherche ignore les accents et la casse.
- Elle interroge le nom de l'outil et les mots-clés métier associés.
- Pendant une recherche, les résultats de toutes les catégories sont affichés et les groupes sans résultat sont masqués.
- Sans recherche, un seul groupe est visible ; changer de catégorie ne recharge pas la page.
- Un message concis apparaît si aucun outil ne correspond.

## Hors périmètre de cette première tranche

- Aucun changement des routes Flask, des tables SQLite, des données résidents, des affectations ou des gardes.
- Aucune modification des permissions métier.
- Pas de réécriture globale de tous les écrans métier ni de suppression arbitraire de leurs explications réglementaires.
- Les optimisations de densité et de défilement à l'intérieur de chaque écran seront traitées après validation de ce socle de navigation.

## Critères de validation

1. Les cinq accès principaux sont présents dans chacun des sept thèmes.
2. Les catégories Outils affichent un seul groupe à la fois.
3. La recherche trouve des outils dans plusieurs catégories et ignore les accents.
4. Un compte non Super Admin ne voit pas les fonctions réservées à l'administration.
5. Les URL et les routes métier existantes continuent de répondre.
6. Les tests de non-régression Python et le workflow Android sont exécutés avant de présenter un APK.
