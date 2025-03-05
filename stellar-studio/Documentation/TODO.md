# TODO List - Stellar Studio

## 🔥 Priorité Haute (Bloquant pour la démo)
- [x] **Endpoint de Download**
  - Créer un endpoint `/tasks/download` dédié
  - Intégrer avec le service de téléchargement
  - Assurer la cohérence avec le frontend

- [x] **Gestion des tâches Celery**
  - Résoudre la double déclaration des tâches (tasks/ et core/tasks.py)
  - Standardiser les noms des tâches
  - Assurer la cohérence des chaînes de tâches pour le traitement d'images

- [ ] **Gestion des erreurs critiques**
  - Implémenter une gestion basique des erreurs dans les services principaux
  - Ajouter des logs pour les erreurs critiques
  - Gérer les cas d'erreur dans les tâches de traitement d'images

- [ ] **WebSocket et notifications**
  - Assurer la stabilité des connexions WebSocket
  - Gérer proprement les déconnexions
  - Implémenter un mécanisme de retry basique

## ⚠️ Priorité Moyenne (Important mais non bloquant)
- [ ] **Sécurité basique**
  - Sécuriser le stockage des secrets
  - Implémenter une validation CORS basique
  - Ajouter une authentification simple

- [ ] **Performance de base**
  - Ajouter une pagination simple sur les endpoints critiques
  - Optimiser les requêtes les plus lourdes
  - Gérer la mémoire dans le traitement d'images

- [ ] **Documentation minimale**
  - Documenter l'installation et le déploiement
  - Ajouter des commentaires sur les parties complexes
  - Créer un README clair

## 📝 Priorité Basse (Pour l'après-démo)
- [ ] **Optimisation du téléchargement MAST**
  - Débugger l'erreur "'telescope_id' is an invalid keyword argument for TargetFile"
  - Corriger le statut FAILED malgré le téléchargement réussi dans MinIO
  - Ajouter une vérification préalable des fichiers existants dans MinIO pour éviter les téléchargements redondants
  - Optimiser la sélection des fichiers pertinents (ex: M104 prend ~2h pour télécharger tous les fichiers)
  - Implémenter une stratégie intelligente pour récupérer prioritairement les fichiers nécessaires à la mosaïque
  - Ajouter une option pour limiter le nombre de fichiers téléchargés par cible

- [ ] **Tests**
  - Mettre en place une structure de tests
  - Écrire des tests unitaires basiques
  - Ajouter des tests d'intégration

- [ ] **Refactoring**
  - Nettoyer le code dupliqué
  - Améliorer la structure des repositories
  - Standardiser les patterns utilisés

- [ ] **Configuration**
  - Centraliser la configuration
  - Ajouter la validation des variables d'environnement
  - Séparer les configurations dev/prod

- [ ] **Monitoring et Maintenance**
  - Mettre en place un système de logging complet
  - Ajouter des métriques
  - Implémenter un health check complet

## 💡 Améliorations Futures
- [ ] Implémenter un système de cache
- [ ] Ajouter un rate limiting
- [ ] Améliorer la gestion des sessions DB
- [ ] Optimiser les performances globales
- [ ] Ajouter des fonctionnalités de monitoring avancées
- [ ] Mettre en place un système de CI/CD
- [ ] Améliorer la documentation technique
- [ ] Implémenter des tests de charge
- [ ] Ajouter des mécanismes de backup automatiques 