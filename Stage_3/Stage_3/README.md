# StellarStudio - Astronomical Image Processing Platform

## Table of Contents
- [Overview](#overview)
- [MVP Focus](#mvp-focus)
- [Project Goals](#project-goals)
- [Technical Stack](#technical-stack)
  - [Backend](#backend)
  - [Frontend](#frontend)
  - [Image Processing](#image-processing)
- [Key Features](#key-features)
- [Development Status](#development-status)
- [Technical Documentation](#technical-documentation) (<= Kevin you missed the plane, again : Where is Keeeeeeeeeeeeeeeeeeeevin !?????? )
- [Roadmap](#roadmap)
- [License & Intellectual Property](#license--intellectual-property)

## Overview
StellarStudio is an innovative web platform dedicated to astronomical image processing, designed to meet the needs of astrophotographers of all levels. Our solution provides an intuitive interface and powerful tools to transform raw data into stunning cosmic images.

## MVP Focus (March 2025)
Our initial release focuses on beginners in astrophotography by providing:
- Direct integration with NASA/MAST catalog
- Automated pre-processing workflows
- Simple and intuitive interface
- Predefined processing templates

## Project Goals
- Democratize astronomical image processing
- Provide automated workflows for beginners
- Deliver advanced tools for experts
- Build an astrophotographer community

## Technical Stack
### Backend
- FastAPI for RESTful API
- Celery + Redis for async tasks
- MariaDB as database
- MinIO for image storage

### Frontend
- Vue.js 3 with Vuetify
- Planned migration to Vite
- Three.js for 3D visualization

### Image Processing
- AstroPy for FITS files
- OpenCV and NumPy for processing

## Key Features
- Predefined catalog of astronomical targets (HST (Hubble Space Telescope) and JWST (James Webb Space Telescope))
- Automated preprocessing (dark, flat, bias)
- Image alignment and stacking
- Advanced processing techniques 
    - ABE (Automatic Background Extraction)
    - HOO (Hydrogen/OIII oxygen palette)
    - SHO (Hubble Space Telescope palette - S-II, H-alpha, O-III)
- 3D visualization of astronomical objects (MVP feature if time permits)

## Development Status
Currently in active development with:
- Core architecture implementation
- Basic authentication system
- NASA/MAST API integration
- Automated pre-processing pipeline

## Technical Documentation
### Architecture and Specifications
- [User Stories](./docs/user_stories.md)
- [System Architecture](./docs/architecture.md)
- [API Specifications](./docs/api_specs.md)
- [QA Strategy](./docs/qa_strategy.md)

Note: All technical diagrams and schemas are proprietary and part of StellarStudio's intellectual property.

## Roadmap
- [x] Base architecture
- [x] Authentication system
- [ ] Preset library
- [ ] Community sharing features
- [ ] Performance optimization

## License & Intellectual Property
© 2024-2025 StellarStudio. All rights reserved.

This software, including but not limited to:
- Source code
- Algorithms
- Processing pipelines
- Documentation
- User interface design

is proprietary and confidential. Any unauthorized copying, modification, distribution, or use of this software and its components is strictly prohibited.

Future licensing terms may be revised based on market conditions and project evolution.
