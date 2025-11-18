# NetHub - Network Sharing Hub

A comprehensive network management and sharing platform with captive portal functionality, user management, and payment integration.

## 🌟 Features

### Core Functionality
- **Captive Portal** - User authentication and network access control
- **Payment System** - Flexible pricing plans with M-Pesa and card payments
- **User Management** - Role-based access control and user profiles
- **Device Management** - Connected device monitoring and access control
- **Service Discovery** - Local services and advertisements platform
- **Admin Dashboard** - Comprehensive network administration

### Technical Features
- **Responsive Design** - Mobile-first approach with dark/light theme support
- **Real-time Updates** - Live connection status and payment processing
- **Queue Management** - M-Pesa payment queue system
- **API-driven** - RESTful backend with JSON responses
- **Modern UI** - Tailwind CSS with elegant glass morphism effects

## 🏗️ Project Structure

```
nethub/
├── frontend/                 # React Frontend
│   ├── src/
│   │   ├── components/       # Reusable components
│   │   ├── pages/           # Main application pages
│   │   ├── services/        # API integration
│   │   └── styles/          # CSS and Tailwind config
│   └── package.json
│
├── backend/                  # Django Backend
│   ├── nethub/
│   │   ├── models.py        # Database models
│   │   ├── views.py         # API views and business logic
│   │   ├── admin.py         # Django admin configurations
│   │   ├── urls.py          # URL routing
│   │   └── settings.py      # Django settings
│   └── requirements.txt
│
└── README.md
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.8+
- PostgreSQL/MySQL database
- M-Pesa API credentials (for payment processing)

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## 📱 Application Pages

### 1. **Portal Page** (`/`)
- User authentication and terms acceptance
- Device information display
- Network connection initiation

### 2. **Dashboard** (`/dashboard`)
- User connection statistics
- Network quality indicators
- Quick action buttons
- Real-time connection monitoring

### 3. **Payment** (`/payment`)
- Multiple pricing plans (30min to 1 month)
- M-Pesa and card payment options
- Payment queue management
- Transaction status tracking

### 4. **Discover** (`/discover`)
- Local services directory
- Service provider listings
- Advertisement management
- Search and filtering

### 5. **Admin** (`/admin`)
- Network configuration
- User management
- Device monitoring
- Access code generation
- System reports

### 6. **Settings** (`/settings`)
- System configuration
- Payment gateway setup
- Security settings
- Notification preferences

## 💳 Payment Integration

### Supported Payment Methods
- **M-Pesa** - Mobile money payments with STK push
- **Credit/Debit Cards** - Visa, MasterCard, American Express

### Pricing Plans
- 30 Minutes - KES 50
- 1 Hour - KES 80
- 4 Hours - KES 250
- 24 Hours - KES 400
- 1 Week - KES 2,000
- 1 Month - KES 6,000

## 🔧 API Endpoints

### Authentication & Portal
- `GET /api/status` - System status and device info
- `POST /api/connect` - Initiate network connection

### Payment System
- `GET /api/payment/plans` - Get pricing plans
- `POST /api/payment/initiate` - Start payment process
- `GET /api/payment/status/{id}` - Check payment status
- `POST /api/payment/mpesa-callback` - M-Pesa webhook

### User Management
- `GET /api/users` - List users (admin)
- `POST /api/users` - Create user (admin)
- `PUT /api/users/{id}` - Update user

### Device Management
- `GET /api/devices` - List connected devices
- `POST /api/admin/grant_access/{mac}` - Grant device access
- `DELETE /api/admin/revoke_access/{mac}` - Revoke device access

### Service Discovery
- `GET /api/discover/services` - Browse services
- `GET /api/discover/services/featured` - Featured services
- `POST /api/discover/services/{id}/favorite` - Favorite services

## 🗄️ Database Models

### Core Models
- **User** - Extended user profiles with roles
- **Network** - WiFi network configurations
- **Device** - Connected device tracking
- **PaymentTransaction** - Payment records
- **InternetAccess** - Active access sessions

### Service Models
- **ServiceCategory** - Service classifications
- **ServiceProvider** - Business listings
- **Service** - Individual service offerings
- **Advertisement** - Promotional content

### Payment Models
- **PricingPlan** - Subscription plans
- **PaymentQueue** - Transaction queue
- **MpesaCallback** - Payment webhook logs

## 🎨 UI/UX Features

### Design System
- **Tailwind CSS** - Utility-first CSS framework
- **Heroicons** - Consistent iconography
- **Glass Morphism** - Modern translucent effects
- **Gradient Backgrounds** - Elegant color schemes

### Responsive Design
- Mobile-first approach
- Tablet and desktop optimizations
- Touch-friendly interfaces
- Adaptive layouts

### Theme Support
- Light and dark mode
- Consistent color palettes
- Accessibility considerations
- Smooth transitions

## 🔒 Security Features

- Role-based access control
- Device authentication
- Payment validation
- Secure API endpoints
- Input sanitization
- CSRF protection

## 📊 Admin Features

### Network Administration
- Real-time device monitoring
- Bandwidth management
- Access control
- Network configuration

### User Management
- User role assignment
- Access permissions
- Activity monitoring
- Profile management

### Reporting
- Usage statistics
- Payment analytics
- Device connectivity reports
- System performance metrics

## 🔄 Workflow

### User Connection Flow
1. User connects to WiFi network
2. Redirected to captive portal
3. Accepts terms and conditions
4. Selects payment plan
5. Completes payment (M-Pesa/card)
6. Granted internet access
7. Redirected to dashboard

### Payment Processing Flow
1. User selects pricing plan
2. Payment method selection
3. Payment initiation (STK push for M-Pesa)
4. Queue position assignment (if M-Pesa)
5. Payment confirmation via callback
6. Internet access activation
7. Status update to user

## 🛠️ Development

### Frontend Stack
- React 18
- React Router
- Axios for API calls
- Tailwind CSS
- Heroicons

### Backend Stack
- Django 4.2
- Django REST Framework
- PostgreSQL/MySQL
- M-Pesa Daraja API

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/nethub

# M-Pesa
MPESA_CONSUMER_KEY=your_consumer_key
MPESA_CONSUMER_SECRET=your_consumer_secret
MPESA_SHORTCODE=your_shortcode
MPESA_PASSKEY=your_passkey

# Security
SECRET_KEY=your_django_secret
DEBUG=False
```

## 📈 Deployment

### Production Checklist
- [ ] Set DEBUG=False
- [ ] Configure database
- [ ] Set up M-Pesa credentials
- [ ] Configure static files
- [ ] Set up SSL certificate
- [ ] Configure domain and DNS
- [ ] Set up backup system
- [ ] Configure logging
- [ ] Set up monitoring

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the documentation
- Open an issue on GitHub
- Contact the development team

---

**NetHub** - Empowering network sharing and management with modern web technologies.
