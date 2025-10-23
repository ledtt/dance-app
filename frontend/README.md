# Dance Studio Frontend

Modern React frontend for dance studio booking system.

## 🚀 Technologies

- **React 18** - Core framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **React Router** - Client-side routing
- **React Hook Form** - Form handling
- **Lucide React** - Icon library
- **Date-fns** - Date manipulation

## 📁 Project Structure

```
frontend/
├── src/
│   ├── api/
│   │   └── client.ts          # API client
│   ├── components/
│   │   ├── admin/             # Admin components
│   │   │   ├── BookingFilters.tsx
│   │   │   ├── ClassesByDay.tsx
│   │   │   └── UserDetails.tsx
│   │   ├── auth/              # Authentication components
│   │   │   ├── LoginForm.tsx
│   │   │   └── RegisterForm.tsx
│   │   ├── booking/           # Booking components
│   │   │   └── BookingModal.tsx
│   │   ├── common/            # Common components
│   │   │   └── LoadingSpinner.tsx
│   │   ├── layout/            # Layout components
│   │   │   └── Navigation.tsx
│   │   └── schedule/          # Schedule components
│   │       ├── ScheduleCard.tsx
│   │       └── ScheduleFilters.tsx
│   ├── contexts/
│   │   └── AuthContext.tsx    # Authentication context
│   ├── pages/                 # Application pages
│   ├── types/                 # TypeScript type definitions
│   ├── App.tsx               # Main application component
│   ├── main.tsx              # Application entry point
│   └── index.css             # Global styles
├── public/                   # Static assets
├── package.json
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
├── Dockerfile               # Frontend container
└── nginx.conf               # Nginx configuration
```

## 🛠️ Installation and Setup

### Prerequisites

- Node.js 18+
- npm or yarn
- Docker and Docker Compose (for full application)

### Local Development (Standalone)

```bash
cd frontend
npm install
npm run dev
```

Application will be available at: http://localhost:3000

### Docker Development (Recommended)

The frontend is designed to work with the full Docker Compose setup:

```bash
# From project root
docker-compose up --build
```

This will start all services including the frontend at http://localhost (port 80)

### Production Build

```bash
npm run build
```

### Preview Build

```bash
npm run preview
```

## 🔧 Configuration

### API Proxy

Configured in `vite.config.ts` for development:

- `/api/auth` → `http://localhost:8001` (Auth Service)
- `/api/schedule` → `http://localhost:8002` (Schedule Service)  
- `/api/booking` → `http://localhost:8003` (Booking Service)

### Environment Variables

The frontend uses proxy configuration for API calls during development. In production, the API endpoints would be configured differently.

### Docker Configuration

The frontend is containerized with:
- **Base Image**: Node.js Alpine
- **Build Tool**: Vite
- **Web Server**: Nginx (for production)
- **Port**: 80 (in Docker), 3000 (standalone development)

## 📱 Features

### 🔐 Authentication

- User registration
- User login
- JWT token management
- Protected routes

### 📅 Schedule

- View all dance classes
- Filter by instructor, day of week, class name
- Search functionality
- Class activity status

### 📚 Booking

- Book classes for specific dates
- View personal bookings
- Cancel bookings
- Booking history

### 👨‍💼 Admin Panel

- Class and booking statistics
- Class management (create, edit, delete)
- View all bookings
- Analytics by day of week

