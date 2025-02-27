## 1. Structure de Base
- [x] Architecture DDD mise en place
- [x] Services WebSocket configurés
- [x] Modèles de données définis
- [ ] Schemas Pydantic à créer
- [ ] Endpoints api
- [ ] Tests unitaires à écrire

## 2. Infrastructure Docker
- [ ] Optimisation réseau Docker
  - Définir un subnet fixe dans docker-compose
  - Configurer les networks proprement
- [ ] Configuration Traefik
  - Routing MinIO correct
  - Labels Docker optimisés
  - Certificats SSL
- [ ] Monitoring
  - Prometheus/Grafana
  - Métriques WebSocket
  - Métriques Celery

## 3. Data Management
- [ ] Script de seed initial
  - Télescopes (HST/JWST)
  - Filtres et Presets
  - Targets et fichiers MAST
- [ ] Migrations Alembic
- [ ] Tests d'intégration DB

## 4. Processing Pipeline
- [x] Tâches Celery
  - Download MAST
  - Processing images
  - Génération previews
- [/] Workflows de traitement
  - [x] HOO
  - SHO
  - HaRGB
- [ ] Tests des workflows

## 5. Frontend
- [/] Interface utilisateur
  - Sélection Target/Preset
  - Visualisation progression
  - Contrôles de traitement
- [ ] Intégration WebSocket
- [ ] Three.js pour visualisation

## 6. Documentation
- [ ] API Documentation
- [ ] Guide d'installation
- [ ] Documentation utilisateur

## Priorités pour DemoDay (13/03)
1. Schemas + Tests (2-3 jours)
2. Infrastructure Docker (2 jours)
3. Data Seeding (1-2 jours)
4. Pipeline Processing (3-4 jours)
5. Frontend (3-4 jours)
6. Documentation (1-2 jours)