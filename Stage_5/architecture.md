# StellarStudio System Architecture

## System Overview
![System Architecture](../assets/diagrams/system-overview.png)

## Component Interactions
![Component Flow](../assets/diagrams/component-flow.png)

## Key Workflows

### Authentication Flow
![Authentication Sequence](../assets/diagrams/auth-sequence.png)

Key authentication features:
- JWT-based authentication
- Session management with Redis
- Secure password handling
- Role-based access control

### Data Processing Flow
![Data Processing Sequence](../assets/diagrams/data-flow-sequence.png)

MVP processing features:
- NASA/MAST catalog integration
- Automated pre-processing pipeline
- HST/JWST data handling
- Optimized storage management

## Infrastructure Components

### Storage Layer
- **MinIO**: Object storage for processed images
- **MariaDB**: 
  - User profiles and authentication
  - Processing workflow configurations
  - Image metadata and catalog data
  - Target information

### Processing Layer
- **Celery**: Asynchronous task processing
- **Redis**: 
  - Session management
  - Task queue broker
  - Result backend
- **AstroPy**: Core astronomical data handling

### API Layer
- **FastAPI**: RESTful API implementation
- **JWT**: Token-based authentication
- **OpenAPI**: API documentation and testing
