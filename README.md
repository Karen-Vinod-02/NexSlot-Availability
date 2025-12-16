# Classroom Availability Management System

A comprehensive web-based classroom booking and management system built with Streamlit and MySQL. This system allows students to view classroom availability, faculty to book classrooms for lectures and guest presentations, and administrators to manage the system.

## 🎯 Features

### For Students:
- **View Classroom Availability**: Real-time checking of classroom schedules
- **Advanced Filtering**: Filter by department, year, subject, and date
- **Smartboard Filtering**: Find classrooms with smartboard equipment
- **Lecture Feedback**: Rate and review completed lectures
- **Guest Lecture Access**: Access guest lectures based on department restrictions

### For Faculty:
- **Classroom Booking**: Book classrooms for regular classes and guest lectures
- **Conflict Detection**: Automatic prevention of double-booking
- **Real-time Availability**: Check classroom availability instantly
- **Booking Management**: View and manage existing bookings
- **Feedback Analytics**: View ratings and feedback for your lectures

### For Administrators:
- **System Configuration**: Manage system settings and limits
- **Classroom Management**: Add, edit, and delete classroom information
- **Analytics Dashboard**: View comprehensive feedback analytics
- **User Management**: Monitor user activity and bookings
- **Database Administration**: Full database control through admin interface

## 🏗️ System Architecture

- **Frontend**: Streamlit (Python web framework)
- **Database**: MySQL 8.4.7
- **Authentication**: Custom role-based authentication system
- **Data Storage**: Pure MySQL + SQLAlchemy (no file dependencies)
- **Containerization**: Docker for database services

## 📋 Prerequisites

- Python 3.8 or higher
- Docker and Docker Compose
- pip (Python package manager)

## 🚀 Quick Start

### 1. Clone and Navigate
```bash
git clone <repository-url>
cd Classroom-Availability-Management-System-main
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Start MySQL Database
```bash
docker-compose up -d
```

### 4. Launch the Application
```bash
streamlit run app.py
```

### 5. Access the System
Open your browser and navigate to: **http://localhost:8501**

## 🔧 Configuration

### Database Configuration

The MySQL database connection is configured in `secrets.toml`:

```toml
# MySQL Database Configuration
[connections.mysql]
url = "mysql://root:example@localhost:3306/classroom_system"
```

### Database Access (Optional)

For database administration, you can access the web-based admin panel at:
- **URL**: http://localhost:8080
- **System**: MySQL
- **Server**: classroom-db
- **Username**: root
- **Password**: example
- **Database**: classroom_system

## 👥 Default Login Credentials

### Administrator Account
- **Username**: `admin`
- **Password**: `admin123`
- **Role**: Full system access

### Creating New Accounts

Users can self-register through the application interface:
1. Navigate to the login page
2. Click the "Register" tab
3. Choose role (Student or Faculty)
4. Fill in required information
5. Submit registration

## 📚 Usage Guide

### Student Interface

1. **Login** with student credentials
2. **View Availability**:
   - Select date and filters
   - Search by subject or department
   - View smartboard-equipped rooms
3. **Give Feedback**:
   - Access completed lectures
   - Rate lectures (1-5 stars)
   - Add comments

### Faculty Interface

1. **Login** with faculty credentials
2. **Book Classroom**:
   - Select booking type (Regular/Guest)
   - Choose classroom and time slot
   - Add subject/lecture details
3. **Manage Bookings**:
   - View existing bookings
   - Check feedback and ratings
   - Cancel bookings if needed

### Admin Interface

1. **Login** with admin credentials
2. **System Management**:
   - Configure system settings
   - Manage classroom inventory
   - View analytics and reports
3. **Database Operations**:
   - Add/delete classrooms
   - Monitor user activity
   - Analyze feedback trends

## 🗃️ Database Schema

### Tables Created Automatically:
- **users**: User accounts and profiles
- **classrooms**: Room information and capacity
- **bookings**: Lecture and booking records
- **feedback**: Student feedback and ratings
- **system_settings**: Configuration parameters

### Sample Data:
- Default admin account
- System configuration settings
- Classroom count limits

## 🔍 Troubleshooting

### Common Issues

#### 1. MySQL Connection Error
```
Error: Database connection failed
```
**Solution**: Ensure MySQL container is running
```bash
docker-compose up -d
```

#### 2. Port Already in Use
```
Error: Port 8501 is already in use
```
**Solution**: Kill existing process or use different port
```bash
streamlit run app.py --server.port 8502
```

#### 3. Permission Denied
```
Error: Permission denied when accessing database
```
**Solution**: Check database credentials in secrets.toml

#### 4. Dependencies Missing
```
ModuleNotFoundError: No module named 'streamlit'
```
**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

### Container Management

#### Start Services
```bash
docker-compose up -d
```

#### Stop Services
```bash
docker-compose down
```

#### View Logs
```bash
docker-compose logs -f
```

#### Reset Database
```bash
docker-compose down -v
docker-compose up -d
```

## 🛠️ Development

### Project Structure
```
Classroom-Availability-Management-System-main/
├── app.py                 # Main application
├── requirements.txt       # Python dependencies
├── docker-compose.yml     # Docker configuration
├── secrets.toml          # Database configuration
├── schema.sql            # Database schema
├── Dockerfile            # Container definition
└── README.md            # This file
```

### Key Components

#### Authentication System
- Role-based access control
- Password hashing with SHA256
- Session management

#### Database Layer
- SQLAlchemy ORM integration
- Raw SQL execution for complex queries
- Connection pooling and caching

#### User Interface
- Responsive Streamlit components
- Real-time data updates
- Interactive data visualization

## 📊 System Statistics

The sidebar displays real-time statistics:
- Total classrooms registered
- Active bookings count
- User-specific metrics
- Feedback statistics

## 🔐 Security Features

- Password hashing (SHA256)
- Session-based authentication
- Role-based access control
- SQL injection protection
- Input validation and sanitization

## 📈 Performance Optimizations

- Database connection caching
- Streamlit caching for expensive operations
- Efficient SQL queries with proper indexing
- Lazy loading of data

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and support:
1. Check the troubleshooting section
2. Review application logs
3. Verify database connectivity
4. Check Docker container status

## 🔄 Updates

The system automatically initializes the database on first run, creating all necessary tables and default data.

---

**Built with ❤️ using Streamlit & MySQL**

For more information, visit the application at http://localhost:8501
