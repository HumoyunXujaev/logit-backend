# Logit Platform - Logistics Management System

![Logit Platform](logit\app\blue.png)

## Overview

Logit Platform is a comprehensive logistics management system designed to streamline cargo transportation and logistics operations. The platform connects cargo owners, carriers, logistics companies, and logistics students in a unified ecosystem.

## 🌟 Key Features

### Authentication & User Management

- Telegram WebApp authentication integration
- Multi-role user system (Carriers, Cargo Owners, Logistics Companies, Students)
- Profile management with document verification
- Role-based access control
- Language selection (Russian/Uzbek)

### Cargo Management

- Create and manage cargo listings
- Advanced cargo search with filtering
- Real-time cargo status tracking
- Multi-point route support
- Automatic cargo matching with carriers
- Price negotiation system
- Document management for cargo

### Vehicle Management

- Detailed vehicle registration and management
- Vehicle document verification
- Technical specifications tracking
- Vehicle availability management
- ADR/TIR/DOZVOL certification support
- Vehicle inspection history

### Carrier Features

- Vehicle fleet management
- Cargo acceptance/rejection system
- Real-time cargo notifications
- Document upload and verification
- Route planning and tracking
- Availability management

### Student Features

- Access to logistics training
- Supervised cargo management
- Learning progression tracking
- Practice with real cargo listings
- Mentor assignment system

### Platform Features

- Real-time notifications
- Favorites system
- Rating and review system
- Distance calculation
- Advanced search filters
- Document verification system
- Multi-language support
- Telegram group integration

## 🔧 Technology Stack

### Frontend

- Next.js 14 (App Router)
- TypeScript
- TailwindCSS
- Shadcn/ui Components
- Telegram WebApp SDK
- React Query
- Axios
- Framer Motion

### Backend

- Django
- Django REST Framework
- PostgreSQL
- Redis
- Celery
- JWT Authentication
- Swagger/OpenAPI

## 📦 Installation

### Prerequisites

- Node.js 18+
- Python 3.10+
- PostgreSQL
- Redis
- Telegram Bot Token

### Frontend Setup

1. Clone the repository:

```bash
git clone https://github.com/HumoyunXujaev/logit-fronttt
cd logit
```

2. Install dependencies:

```bash
npm install
```

3. Create .env.local:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

4. Run development server:

```bash
npm run dev
```

5. setup ngrok (telegram web app doesn't work with localhost):
```bash
ngrok http 3000
```

### Backend Setup

1. Clone the repository:

```bash
git clone https://github.com/HumoyunXujaev/logit-backend/
cd logit_backend
```

2. Create virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create .env:

```env
DJANGO_SECRET_KEY=your_secret_key
DJANGO_DEBUG=True
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
POSTGRES_DB=logit_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

5. Run migrations:
   
```bash
python manage.py makemigrations
```

```bash
python manage.py migrate
```

6. Start development server:

```bash
python manage.py runserver
```

## 🏗 Project Structure

### Backend Structure

```
├── cargo/             # Cargo management
├── vehicles/          # Vehicle management
├── users/            # User management
├── core/             # Core functionality
└── logit_backend/    # Project settings
```

## 🚀 Features In Detail

### User Registration Flow

1. User opens Telegram bot
2. Selects language preference
3. Chooses user type (Individual/Legal Entity)
4. Selects role (Carrier/Cargo Owner/etc.)
5. Fills profile information
6. Uploads required documents
7. Awaits verification (if required)

### Cargo Management Flow

1. Cargo owner creates cargo listing
2. System processes and validates cargo information
3. Students can view and manage cargo listings
4. Students can match cargo with carriers
5. Carriers receive notification and can accept/reject
6. System tracks cargo status throughout delivery

### Vehicle Management Flow

1. Carrier registers vehicles
2. Uploads required documentation
3. System verifies vehicle information
4. Carrier can update vehicle availability
5. System matches vehicles with compatible cargo
6. Tracks vehicle status and documents expiry

### Student Learning Flow

1. Student registers with group information
2. Gets assigned to mentor
3. Can view and practice with real cargo listings
4. Manages cargo-carrier matching
5. Receives feedback from mentors
6. Tracks learning progress

## 🔐 Security

- JWT-based authentication
- Role-based access control
- Document verification system
- Secure file uploads
- HTTPS encryption
- Input validation
- Rate limiting
- Session management

## 📱 Mobile Responsiveness

The platform is fully responsive and optimized for:

- Desktop browsers
- Mobile devices
- Telegram WebApp
- Tablets

## 🌐 API Documentation

API documentation is available at:

- Swagger UI: `/api/docs/`
- ReDoc: `/api/redoc/`

## 🤝 Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## 👥 Team

- Product Owner: [Name]
- Lead Developer: [Name]
- Backend Developer: [Name]
- Frontend Developer: [Name]
- UI/UX Designer: [Name]

## 📞 Support

For support, please contact:

- Email: support@logit.com
- Telegram: @logit_support
- Website: https://logit.com/support

## 🌟 Acknowledgments

- Telegram for WebApp SDK
- Shadcn for UI components
- All contributors and testers

## 🗺 Roadmap

### Phase 1 (Current)

- Core platform functionality
- Basic cargo management
- Vehicle registration
- User authentication

### Phase 2 (Planned)

- Advanced analytics
- Mobile applications
- Real-time tracking
- Payment integration
- AI-powered matching

### Phase 3 (Future)

- International expansion
- Blockchain integration
- IoT device support
- Advanced automation

## ⚙ Configuration

### Environment Variables

#### Frontend

```env
NEXT_PUBLIC_API_URL=
NEXT_PUBLIC_TELEGRAM_BOT_TOKEN=
```

#### Backend

```env
DJANGO_SECRET_KEY=
DJANGO_DEBUG=
TELEGRAM_BOT_TOKEN=
POSTGRES_DB=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_HOST=
POSTGRES_PORT=
```

---

**Note**: This project is actively maintained and regularly updated. For the latest features and changes, please check the CHANGELOG.md file.
