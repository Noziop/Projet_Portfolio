# StellarStudio - Astronomical Image Processing Platform

## Overview
StellarStudio is an innovative web platform dedicated to astronomical image processing, designed to meet the needs of astrophotographers of all levels. Our solution provides an intuitive interface and powerful tools to transform raw data into stunning cosmic images.

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

## Detailed Documentation
- [User Stories](./docs/user_stories.md)
- [System Architecture](./docs/architecture.md)
- [API Specifications](./docs/api_specs.md)
- [QA Strategy](./docs/qa_strategy.md)

## Key Features
- Predefined catalog of astronomical targets (HST and JWST)
- Automated preprocessing (dark, flat, bias)
- Image alignment and stacking
- Advanced processing techniques (ABE, HOO, SHO)
- 3D visualization of astronomical objects

## Roadmap
- [x] Base architecture
- [x] Authentication system
- [ ] Preset library
- [ ] Community sharing features
- [ ] Performance optimization
