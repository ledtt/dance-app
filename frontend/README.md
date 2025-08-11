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
│   │   ├── auth/              # Authentication components
│   │   ├── booking/           # Booking components
│   │   ├── common/            # Common components
│   │   ├── layout/            # Layout components
│   │   └── schedule/          # Schedule components
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
└── tsconfig.json
```

## 🛠️ Installation and Setup

### Prerequisites

- Node.js 18+
- npm or yarn

### Install Dependencies

```bash
cd frontend
npm install
```

### Development Mode

```bash
npm run dev
```

Application will be available at: http://localhost:3000

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

Configured in `vite.config.ts`:

- `/api/auth` → `http://localhost:8001`
- `/api/schedule` → `http://localhost:8002`
- `/api/booking` → `http://localhost:8003`

### Environment Variables

Create `.env` file in frontend root:

```env
VITE_API_BASE_URL=http://localhost:3000/api
```

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

