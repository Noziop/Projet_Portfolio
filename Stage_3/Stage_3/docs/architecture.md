# StellarStudio System Architecture

## System Overview

```
graph TB
    Client[Web Client Vue.js/Vuetify]
    API[FastAPI Backend]
    Queue[Celery Queue]
    Cache[Redis Cache]
    DB[(MariaDB)]
    Storage[MinIO Storage]
    
    Client --> API
    API --> Queue
    API --> Cache
    API --> DB
    Queue --> Storage
    Queue --> Cache
```

## Component Details

### Backend Services
```
graph LR
    Auth[Authentication Service]
    Image[Image Processing Service]
    Telescope[Telescope Integration]
    Storage[Storage Service]
    
    Auth --> Image
    Image --> Storage
    Image --> Telescope
```

### Data Flow
```
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant Celery
    participant Storage
    
    User->>Frontend: Upload image
    Frontend->>API: POST /images
    API->>Storage: Store raw image
    API->>Celery: Create processing task
    Celery->>Storage: Process image
    Storage->>API: Return processed URL
    API->>Frontend: Return result
    Frontend->>User: Display processed image
```

## Infrastructure Components

### Storage Layer
- **MinIO**: Object storage for astronomical images
- **MariaDB**: Relational database for:
  - User data
  - Telescope configurations
  - Processing workflows
  - Image metadata

### Processing Layer
- **Celery**: Asynchronous task processing
- **Redis**: Cache and message broker
- **AstroPy**: Core astronomical processing

### API Layer
- **FastAPI**: RESTful API endpoints
- **JWT**: Authentication
- **OpenAPI**: API documentation
