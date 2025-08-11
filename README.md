# Dance App - Full Stack Application

A modern dance class booking system built with FastAPI microservices backend and React frontend.

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
│       ├── requirements.txt
│       ├── test_auth_service.py
│       ├── test_booking_service.py
│       └── test_schedule_service.py

├── docker-compose.yml     # Main Docker configuration
├── requirements-admin.txt  # Admin dependencies
├── create_admin.py        # Admin user creation script
└── README.md              # Documentation
```

## 📚 API Documentation

### Authentication Service (Port 8001)

#### Endpoints
- `POST /register` - Register new user
- `POST /login` - User login
- `GET /me` - Get current user info
- `PUT /me` - Update current user profile
- `POST /me/change-password` - Change current user password
- `GET /admin/users` - Get all users (admin only)
- `PUT /admin/users/{user_id}` - Update user by admin
- `GET /users/{user_id}` - Get user by ID (admin only)
- `POST /auth/internal/service-token` - Get service JWT token
- `GET /internal/users/{user_id}` - Get user (internal use)

### Schedule Service (Port 8002)

#### Endpoints
- `GET /schedule` - Get all classes (with advanced filtering)
- `POST /schedule` - Create new class (admin only)
- `PUT /schedule/{class_id}` - Update class (admin only)
- `DELETE /schedule/{class_id}` - Delete class (admin only)
- `GET /schedule/{class_id}` - Get specific class
- `GET /schedule/statistics` - Get schedule statistics

#### Advanced Filtering
The main `/schedule` endpoint supports advanced filtering:
```bash
# Filter by weekday
GET /schedule?weekday=1

# Filter by teacher
GET /schedule?teacher=Anna

# Filter by active status
GET /schedule?active=true

# Combine filters
GET /schedule?weekday=1&teacher=Anna&active=true

# Pagination
GET /schedule?limit=20&offset=0
```
### Booking Service (Port 8003)

#### Endpoints
- `POST /book` - Book a class (authenticated users)
- `GET /my-bookings` - Get user's bookings
- `DELETE /bookings/{booking_id}` - Cancel booking
- `GET /bookings/{booking_id}` - Get specific booking
- `GET /admin/bookings` - Get all bookings (admin)
- `POST /admin/bookings` - Create booking for any user (admin)
- `GET /admin/statistics` - Get booking statistics (admin)
