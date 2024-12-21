#!/bin/bash

# Création de l'arborescence
mkdir -p stellar-studio/{backend/{app/{api,core,services,models},tests,docker},frontend/{src,docker}}

# Création des README uniquement dans les dossiers principaux
echo "# Stellar Studio" > stellar-studio/README.md
echo "# Backend" > stellar-studio/backend/README.md
echo "# Frontend" > stellar-studio/frontend/README.md

# Création du docker-compose.yml
touch stellar-studio/docker-compose.yml
echo "# Docker Compose file for StellarStudio" > stellar-studio/docker-compose.yml
