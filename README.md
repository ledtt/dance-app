# Dance App - Full Stack Application

A dance class booking system built with FastAPI microservices backend and React frontend.

## 🏗️ Architecture Overview

The application follows a microservices architecture with:

### Backend Services (Microservices)

1. **Auth Service** (`services/auth/`) - User authentication and authorization
2. **Schedule Service** (`services/schedule/`) - Class schedule management
3. **Booking Service** (`services/booking/`) - Class booking and management

### Frontend Application

- **React Frontend** (`frontend/`) - Modern React + TypeScript application with beautiful UI

### Shared Components

- **Shared Library** (`shared/`) - Common utilities, exceptions, and constants
- **Security Features** - Rate limiting, CORS, JWT authentication
- **Structured Logging** - JSON-formatted logs for monitoring

## 📁 Project Structure

```
dance-app/
├── frontend/                # React frontend application
│   ├── src/
│   │   ├── api/            # API client
│   │   ├── components/     # React components
│   │   │   ├── admin/      # Admin components
│   │   │   ├── auth/       # Authentication components
│   │   │   ├── booking/    # Booking components
│   │   │   ├── common/     # Common components
│   │   │   ├── layout/     # Layout components
│   │   │   └── schedule/   # Schedule components
│   │   ├── contexts/       # React contexts
│   │   ├── pages/          # Application pages
│   │   ├── types/          # TypeScript types
│   │   ├── App.tsx         # Main app component
│   │   ├── main.tsx        # Entry point
│   │   └── index.css       # Styles
│   ├── package.json        # Dependencies
│   ├── vite.config.ts      # Vite configuration
│   ├── tailwind.config.js  # Tailwind CSS config
│   ├── Dockerfile          # Frontend container
│   └── nginx.conf          # Nginx configuration
├── services/
│   ├── auth/               # Authentication service
│   │   ├── src/
│   │   │   ├── main.py    # FastAPI application
│   │   │   ├── auth.py    # JWT authentication
│   │   │   ├── crud.py    # Database operations
│   │   │   ├── models.py  # SQLAlchemy models
│   │   │   ├── schemas.py # Pydantic schemas
│   │   │   ├── config.py  # Configuration
│   │   │   └── db.py      # Database setup
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── booking/            # Booking service
│   │   ├── src/
│   │   │   ├── main.py    # FastAPI application
│   │   │   ├── crud.py    # Database operations
│   │   │   ├── models.py  # SQLAlchemy models
│   │   │   ├── schemas.py # Pydantic schemas
│   │   │   ├── auth.py    # JWT validation
│   │   │   ├── config.py  # Configuration
│   │   │   ├── db.py      # Database setup
│   │   │   ├── external_schedule.py  # External service calls
│   │   │   └── service_auth.py       # Inter-service authentication
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── schedule/           # Schedule service
│       ├── src/
│       │   ├── main.py    # FastAPI application
│       │   ├── crud.py    # Database operations
│       │   ├── models.py  # SQLAlchemy models
│       │   ├── schemas.py # Pydantic schemas
│       │   ├── config.py  # Configuration
│       │   ├── db.py      # Database setup
│       │   └── auth.py    # JWT validation
│       ├── requirements.txt
│       └── Dockerfile
├── shared/                 # Shared components
│   ├── __init__.py
│   ├── auth.py            # Authentication utilities
│   ├── constants.py       # Constants and enums
│   ├── exceptions.py      # Custom exceptions
│   ├── schemas.py         # Shared Pydantic schemas
│   └── utils.py           # Utility functions
├── tests/                 # Test suite
│   └── unit/              # Unit tests
│       ├── __init__.py
│       ├── conftest.py    # Test configuration and fixtures
│       ├── requirements.txt
│       ├── auth/
│       │   └── test_auth_service.py
│       ├── booking/
│       │   └── test_booking_service.py
│       └── schedule/
│           └── test_schedule_service.py
├── postgres-config/       # PostgreSQL configuration
│   └── postgresql.conf
├── docker-compose.yml     # Local development Docker configuration
├── requirements-admin.txt  # Admin dependencies
├── create_admin.py        # Admin user creation script
├── entrypoint.sh          # Docker entrypoint script
├── .env.example           
└── README.md              # Documentation
```

## 🚀 Local Development Setup

This project uses Docker Compose for local development and testing. All services are containerized and configured to work together.

### Prerequisites

- Docker and Docker Compose
- Environment variables configured (see `.env.example`)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd dance-app
   ```

2. **Set up environment variables**
   ```bash
   # Create .env file with your configuration
   # See docker-compose.yml for required environment variables
   ```

3. **Start all services with Docker Compose**
   ```bash
   docker-compose up --build
   ```

4. **Access the application locally**
   - Frontend: http://localhost (port 80)
   - Auth Service: http://localhost:8001
   - Schedule Service: http://localhost:8002
   - Booking Service: http://localhost:8003
   - PostgreSQL: localhost:5432

### Development Commands

```bash
# Start services in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Rebuild and restart
docker-compose up --build

# Run tests
docker-compose exec auth-service python -m pytest tests/unit
```

## 📚 API Documentation

### Authentication Service

#### Endpoints
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user info
- `PUT /api/auth/me` - Update current user profile
- `POST /api/auth/me/change-password` - Change current user password
- `GET /api/auth/admin/users` - Get all users (admin only)
- `PUT /api/auth/admin/users/{user_id}/role` - Update user role (admin only)
- `GET /api/auth/admin/users/{user_id}` - Get user by ID (admin only)
- `POST /api/auth/internal/service-token` - Get service JWT token
- `GET /api/auth/internal/users/{user_id}` - Get user (internal use)
- `GET /health` - Health check

### Schedule Service

#### Endpoints
- `GET /api/schedule/schedule` - Get all classes (with advanced filtering)
- `POST /api/schedule/schedule` - Create new class (admin only)
- `PUT /api/schedule/schedule/{class_id}` - Update class (admin only)
- `DELETE /api/schedule/schedule/{class_id}` - Delete class (admin only)
- `GET /api/schedule/schedule/{class_id}` - Get specific class
- `GET /api/schedule/schedule/statistics` - Get schedule statistics
- `GET /api/schedule/schedule/ids` - Get class IDs (internal use)
- `GET /health` - Health check

#### Advanced Filtering
The main `/api/schedule/schedule` endpoint supports advanced filtering:
```bash
# Filter by weekday
GET /api/schedule/schedule?weekday=1

# Filter by teacher
GET /api/schedule/schedule?teacher=Anna

# Filter by active status
GET /api/schedule/schedule?active=true

# Combine filters
GET /api/schedule/schedule?weekday=1&teacher=Anna&active=true

# Pagination
GET /api/schedule/schedule?page=1&size=20
```
### Booking Service

#### Endpoints
- `POST /api/booking/book` - Book a class (authenticated users)
- `GET /api/booking/my-bookings` - Get user's bookings
- `DELETE /api/booking/bookings/{booking_id}` - Cancel booking
- `GET /api/booking/bookings/{booking_id}` - Get specific booking
- `GET /api/booking/admin/bookings` - Get all bookings (admin)
- `POST /api/booking/admin/bookings` - Create booking for any user (admin)
- `GET /api/booking/admin/statistics` - Get booking statistics (admin)
- `GET /health` - Health check
