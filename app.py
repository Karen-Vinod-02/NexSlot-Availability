import streamlit as st
from datetime import datetime, date, timedelta
import pandas as pd
import json
import os
import hashlib
<<<<<<< HEAD
=======
from sqlalchemy import text

@st.cache_resource
def get_db():
    return st.connection("mysql", type="sql").engine

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()
>>>>>>> d54d050 (Iteration 1)

# Page configuration
st.set_page_config(
    page_title="Classroom Availability System",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------
# Constants
# -----------------------
CLASS_SLOTS = ["8:00 - 9:30", "9:40 - 11:10", "11:20 - 12:50", "1:30 - 3:00", "3:10 - 4:40"]
ACADEMIC_YEARS = ["1st Year", "2nd Year", "3rd Year", "4th Year"]
ACADEMIC_SEMESTERS = ["Semester I", "Semester II"]
DEPARTMENTS = ["Computer Engineering", "Electronics & Telecom (EXTC)", "Mechanical Engineering", "Civil Engineering"]

DIVISIONS_BY_DEPT = {
    "Computer Engineering": ["A", "B", "C"],
    "Electronics & Telecom (EXTC)": ["A", "B"],
    "Mechanical Engineering": [],
    "Civil Engineering": []
}

SUBJECTS_BY_DEPT = {
    "Computer Engineering": {
        "1st Year": ["Introduction to Programming", "Engineering Physics"],
        "2nd Year": ["Data Structures", "Discrete Mathematics"],
        "3rd Year": ["Operating Systems", "Database Management", "AI/ML"],
        "4th Year": ["Web Technology", "Cloud Computing", "Project Management"]
    },
    "Electronics & Telecom (EXTC)": {
        "1st Year": ["Basic Electronics", "Engineering Chemistry"],
        "2nd Year": ["Analog Circuits", "Control Systems"],
        "3rd Year": ["Digital Signal Processing", "Communication Systems", "VLSI Design"],
        "4th Year": ["Microwave Engineering", "Embedded Systems", "Wireless Networks"]
    },
    "Mechanical Engineering": {
        "1st Year": ["Engineering Graphics", "Workshop Practice"],
        "2nd Year": ["Thermodynamics", "Fluid Mechanics"],
        "3rd Year": ["Machine Design", "Manufacturing"],
        "4th Year": ["Automobile Engineering", "Robotics"]
    },
    "Civil Engineering": {
        "1st Year": ["Engineering Mechanics", "Material Science"],
        "2nd Year": ["Structural Analysis", "Geotechnical Engineering"],
        "3rd Year": ["Transportation Engineering", "Hydrology"],
        "4th Year": ["Environmental Engineering", "Construction Management"]
    }
}

# -----------------------
# Data persistence functions
# -----------------------
<<<<<<< HEAD
DATA_DIR = "data"
CLASSROOMS_FILE = os.path.join(DATA_DIR, "classrooms.json")
BOOKINGS_FILE = os.path.join(DATA_DIR, "bookings.json")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
USERS_FILE = os.path.join(DATA_DIR, "users.json")

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def save_users():
    """Save users to file"""
    ensure_data_dir()
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(st.session_state.users, f, indent=2)
    except Exception as e:
        st.error(f"Error saving users: {e}")

def load_users():
    """Load users from file"""
    ensure_data_dir()
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r') as f:
                st.session_state.users = json.load(f)
        else:
            # Initialize with default admin account
            st.session_state.users = {
                "admin": {
                    "password": hash_password("admin123"),
                    "role": "Admin"
                }
            }
            save_users()
    except Exception as e:
        st.error(f"Error loading users: {e}")
        st.session_state.users = {}

def save_data():
    ensure_data_dir()
    try:
        with open(CLASSROOMS_FILE, 'w') as f:
            json.dump(st.session_state.classrooms, f, indent=2)
        with open(BOOKINGS_FILE, 'w') as f:
            json.dump(st.session_state.bookings, f, indent=2)
        config_data = {
            'class_slots': st.session_state.class_slots,
            'classroom_limit': st.session_state.classroom_limit
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_data, f, indent=2)
    except Exception as e:
        st.error(f"Error saving data: {e}")

def load_data():
    ensure_data_dir()
    try:
        if os.path.exists(CLASSROOMS_FILE):
            with open(CLASSROOMS_FILE, 'r') as f:
                st.session_state.classrooms = json.load(f)
        else:
            st.session_state.classrooms = [
                {'id': 'c1', 'roomNumber': '101', 'capacity': 30, 'hasSmartboard': True},
                {'id': 'c2', 'roomNumber': '102', 'capacity': 25, 'hasSmartboard': False},
                {'id': 'c3', 'roomNumber': '205', 'capacity': 50, 'hasSmartboard': True}
            ]

        if os.path.exists(BOOKINGS_FILE):
            with open(BOOKINGS_FILE, 'r') as f:
                st.session_state.bookings = json.load(f)
        else:
            yesterday = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
            st.session_state.bookings = {}

        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config_data = json.load(f)
                st.session_state.class_slots = config_data.get('class_slots', CLASS_SLOTS.copy())
                st.session_state.classroom_limit = config_data.get('classroom_limit', 100)
        else:
            st.session_state.class_slots = CLASS_SLOTS.copy()
            st.session_state.classroom_limit = 100

    except Exception as e:
        st.error(f"Error loading data: {e}")
=======
def init_database():
    """Create all necessary tables if they don't exist"""
    engine = get_db()
    
    with engine.begin() as conn:
        # Users table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL,
                name VARCHAR(255),
                department VARCHAR(255),
                year VARCHAR(50),
                division VARCHAR(10),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Classrooms table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS classrooms (
                id INT AUTO_INCREMENT PRIMARY KEY,
                room_number VARCHAR(50) UNIQUE NOT NULL,
                capacity INT NOT NULL,
                has_smartboard BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Bookings table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                classroom_id INT NOT NULL,
                faculty_id VARCHAR(255) NOT NULL,
                booking_date DATE NOT NULL,
                slot VARCHAR(50) NOT NULL,
                subject VARCHAR(255) NOT NULL,
                faculty_name VARCHAR(255) NOT NULL,
                status VARCHAR(50) DEFAULT 'Confirmed',
                is_guest_lecture BOOLEAN DEFAULT FALSE,
                lecture_title VARCHAR(255),
                department VARCHAR(255),
                year VARCHAR(50),
                division VARCHAR(10),
                semester VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_booking (classroom_id, booking_date, slot),
                FOREIGN KEY (classroom_id) REFERENCES classrooms(id) ON DELETE CASCADE
            )
        """))
        
        # Feedback table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INT AUTO_INCREMENT PRIMARY KEY,
                booking_id INT NOT NULL,
                student_id VARCHAR(255) NOT NULL,
                rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
                comments TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_feedback (booking_id, student_id),
                FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE
            )
        """))
        
        # System settings table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS system_settings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                setting_key VARCHAR(100) UNIQUE NOT NULL,
                setting_value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """))
        
        # Initialize default settings if not exists
        conn.execute(text("""
            INSERT IGNORE INTO system_settings (setting_key, setting_value)
            VALUES ('classroom_limit', '100')
        """))
        
        # Create default admin if not exists
        conn.execute(text("""
            INSERT IGNORE INTO users (username, password_hash, role, name)
            VALUES ('admin', :pwd, 'Admin', 'System Administrator')
        """), {"pwd": hash_password("admin123")})
>>>>>>> d54d050 (Iteration 1)

# -----------------------
# Session initialization
# -----------------------
def init_session_state():
    if 'initialized' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.user_role = None
        st.session_state.user_data = {}
        
        load_users()
        load_data()
        st.session_state.initialized = True

# -----------------------
# Authentication functions
# -----------------------
def register_user(username, password, role, **user_details):
    """Register a new user"""
    if username in st.session_state.users:
        return False, "Username already exists"
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    
    user_data = {
        "password": hash_password(password),
        "role": role
    }
    user_data.update(user_details)
    
    st.session_state.users[username] = user_data
    save_users()
    return True, "Registration successful"

def login(username, password):
    """Authenticate user and set session state"""
    if username not in st.session_state.users:
        return False
    
    user = st.session_state.users[username]
    if user["password"] == hash_password(password):
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.user_role = user["role"]
        st.session_state.user_data = user
        return True
    return False

def logout():
    """Clear session state"""
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.user_role = None
    st.session_state.user_data = {}

def require_auth(allowed_roles):
    """Decorator to require authentication"""
    if not st.session_state.logged_in:
        st.warning("Please login to access this page")
        return False
    if st.session_state.user_role not in allowed_roles:
        st.error("You don't have permission to access this page")
        return False
    return True

# -----------------------
<<<<<<< HEAD
=======
# Database helper functions
# -----------------------
def get_all_classrooms():
    """Get all classrooms from database"""
    engine = get_db()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM classrooms ORDER BY room_number"))
        return [dict(row._mapping) for row in result]

def get_classroom_by_id(classroom_id):
    """Get classroom by ID"""
    engine = get_db()
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM classrooms WHERE id = :id"),
            {"id": classroom_id}
        ).fetchone()
        return dict(result._mapping) if result else None

def get_all_bookings():
    """Get all bookings with feedback"""
    engine = get_db()
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT b.*, 
                   GROUP_CONCAT(
                       CONCAT_WS('|', f.student_id, f.rating, f.comments, f.created_at)
                       SEPARATOR '||'
                   ) as feedback_data
            FROM bookings b
            LEFT JOIN feedback f ON b.id = f.booking_id
            GROUP BY b.id
        """))
        
        bookings = {}
        for row in result:
            row_dict = dict(row._mapping)
            booking_key = f"{row_dict['classroom_id']}_{row_dict['slot']}_{row_dict['booking_date']}"
            
            # Parse feedback
            feedback_list = []
            if row_dict['feedback_data']:
                for feedback_str in row_dict['feedback_data'].split('||'):
                    parts = feedback_str.split('|')
                    if len(parts) >= 4:
                        feedback_list.append({
                            'studentId': parts[0],
                            'rating': int(parts[1]),
                            'comments': parts[2] if parts[2] != 'None' else '',
                            'timestamp': parts[3]
                        })
            
            row_dict['feedback'] = feedback_list
            row_dict['bookingKey'] = booking_key
            bookings[booking_key] = row_dict
        
        return bookings

def get_system_setting(key, default=None):
    """Get system setting"""
    engine = get_db()
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT setting_value FROM system_settings WHERE setting_key = :key"),
            {"key": key}
        ).fetchone()
        return result.setting_value if result else default

def set_system_setting(key, value):
    """Set system setting"""
    engine = get_db()
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO system_settings (setting_key, setting_value)
            VALUES (:key, :value)
            ON DUPLICATE KEY UPDATE setting_value = :value
        """), {"key": key, "value": value})

# -----------------------
>>>>>>> d54d050 (Iteration 1)
# Helper functions
# -----------------------
def generate_id():
    from random import randint
    return f"id_{randint(10000, 99999)}"

def get_classroom_by_id(classroom_id):
    for room in st.session_state.classrooms:
        if room['id'] == classroom_id:
            return room
    return None

def is_lecture_completed(booking_date, slot):
    """Check if a lecture has been completed"""
    booking_datetime = datetime.strptime(booking_date, '%Y-%m-%d').date()
    today = date.today()
    
    if booking_datetime < today:
        return True
    elif booking_datetime == today:
        current_time = datetime.now().time()
        slot_end_time = datetime.strptime(slot.split(' - ')[1], '%H:%M').time()
        return current_time > slot_end_time
    return False

def can_student_give_feedback(booking, student_data):
    """Check if student is eligible to give feedback for a booking"""
    if booking.get('isGuestLecture', False):
        if booking.get('department'):
            return booking['department'] == student_data.get('department')
        return True
    
    if booking.get('department') != student_data.get('department'):
        return False
    if booking.get('year') != student_data.get('year'):
        return False
    if booking.get('division') and booking['division'] != student_data.get('division'):
        return False
    
    return True

def has_student_feedback(booking_key, student_id):
    """Check if student has already given feedback"""
<<<<<<< HEAD
    if booking_key not in st.session_state.bookings:
=======
    engine = get_db()
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT COUNT(*) as count FROM feedback 
                WHERE booking_id = :bid AND student_id = :sid
            """),
            {"bid": booking_id, "sid": student_id}
        ).fetchone()
        return result.count > 0

def submit_feedback(booking_id, student_id, rating, comments):
    """Submit student feedback for a lecture"""
    engine = get_db()
    
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO feedback (booking_id, student_id, rating, comments)
                VALUES (:bid, :sid, :rating, :comments)
            """), {
                "bid": booking_id,
                "sid": student_id,
                "rating": rating,
                "comments": comments
            })
        st.success("Thank you for your feedback!")
        return True
    except Exception as e:
        if 'Duplicate entry' in str(e):
            st.warning("You have already submitted feedback for this lecture!")
        else:
            st.error(f"Error submitting feedback: {str(e)}")
>>>>>>> d54d050 (Iteration 1)
        return False
    
    booking = st.session_state.bookings[booking_key]
    if 'feedback' not in booking:
        return False
    
    return any(f['studentId'] == student_id for f in booking['feedback'])

def submit_feedback(booking_key, student_id, rating, comments):
    """Submit student feedback for a lecture"""
    if booking_key not in st.session_state.bookings:
        st.error("Booking not found.")
        return False
    
    booking = st.session_state.bookings[booking_key]
    
    student_data = st.session_state.user_data
    if not can_student_give_feedback(booking, student_data):
        st.error("You are not eligible to provide feedback for this lecture.")
        return False
    
    if has_student_feedback(booking_key, student_id):
        st.warning("You have already submitted feedback for this lecture!")
        return False
    
    feedback_entry = {
        'studentId': student_id,
        'rating': rating,
        'comments': comments,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    if 'feedback' not in booking:
        booking['feedback'] = []
    
    booking['feedback'].append(feedback_entry)
    save_data()
    st.success("Thank you for your feedback!")
    return True

def get_average_rating(booking):
    """Calculate average rating for a booking"""
    if 'feedback' not in booking or not booking['feedback']:
        return None
    
    ratings = [f['rating'] for f in booking['feedback']]
    return sum(ratings) / len(ratings)

def create_booking(classroom_id, slot, subject, faculty_name, booking_date,
                   is_guest_lecture=False, lecture_title=None, 
                   department=None, year=None, division=None,
                   semester=None, guest_dept_restriction=None):
    """Create a new booking"""
    if not all([classroom_id, slot, faculty_name, booking_date]):
        st.error("Please fill all required fields.")
        return False
    
    if is_guest_lecture and lecture_title:
        subject = lecture_title
    
    if not subject:
        st.error("Please provide a subject or lecture title.")
        return False
    
    booking_key = f"{classroom_id}_{slot}_{booking_date}"
    
<<<<<<< HEAD
    if booking_key in st.session_state.bookings:
        st.error(f"Booking conflict! This slot is already reserved on {booking_date}.")
=======
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO bookings 
                (classroom_id, faculty_id, booking_date, slot, subject, faculty_name,
                 is_guest_lecture, lecture_title, department, year, division, semester)
                VALUES (:cid, :fid, :date, :slot, :subj, :fname, :guest, :title, :dept, :yr, :div, :sem)
            """), {
                "cid": classroom_id,
                "fid": st.session_state.username,
                "date": booking_date,
                "slot": slot,
                "subj": subject,
                "fname": faculty_name,
                "guest": is_guest_lecture,
                "title": lecture_title if is_guest_lecture else None,
                "dept": guest_dept_restriction if is_guest_lecture else department,
                "yr": year if not is_guest_lecture else None,
                "div": division if not is_guest_lecture else None,
                "sem": semester if not is_guest_lecture else None
            })
        
        if is_guest_lecture:
            st.success(f"Guest Lecture '{lecture_title}' successfully booked!")
        else:
            st.success("Classroom successfully booked!")
        return True
    except Exception as e:
        if 'Duplicate entry' in str(e):
            st.error(f"Booking conflict! This slot is already reserved on {booking_date}.")
        else:
            st.error(f"Error creating booking: {str(e)}")
>>>>>>> d54d050 (Iteration 1)
        return False
    
    new_booking = {
        'id': generate_id(),
        'bookingKey': booking_key,
        'classroomId': classroom_id,
        'facultyId': st.session_state.username,
        'date': booking_date,
        'slot': slot,
        'subject': subject,
        'facultyName': faculty_name,
        'status': 'Confirmed',
        'isGuestLecture': is_guest_lecture,
        'lectureTitle': lecture_title if is_guest_lecture else None,
        'department': guest_dept_restriction if is_guest_lecture else department,
        'year': year if not is_guest_lecture else None,
        'division': division if not is_guest_lecture else None,
        'semester': semester if not is_guest_lecture else None,
        'feedback': []
    }
    
    st.session_state.bookings[booking_key] = new_booking
    save_data()
    
    if is_guest_lecture:
        st.success(f"Guest Lecture '{lecture_title}' successfully booked!")
    else:
        st.success("Classroom successfully booked!")
    return True

def cancel_booking(booking_key):
    """Cancel a booking"""
<<<<<<< HEAD
    if booking_key in st.session_state.bookings:
        del st.session_state.bookings[booking_key]
        save_data()
        st.success("Booking successfully cancelled.")
        return True
    st.error("Booking not found.")
    return False

def add_classroom(room_number, capacity, has_smartboard):
    """Add a new classroom"""
    new_room = {
        'id': generate_id(),
        'roomNumber': room_number,
        'capacity': int(capacity),
        'hasSmartboard': has_smartboard
    }
    st.session_state.classrooms.append(new_room)
    save_data()
    st.success(f"Classroom {room_number} added successfully!")

def delete_classroom(room_id):
    """Delete a classroom"""
    st.session_state.classrooms = [r for r in st.session_state.classrooms if r['id'] != room_id]
    keys_to_delete = [key for key, booking in st.session_state.bookings.items() 
                      if booking['classroomId'] == room_id]
    for key in keys_to_delete:
        del st.session_state.bookings[key]
    save_data()
    st.success("Classroom deleted successfully!")
=======
    engine = get_db()
    
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("DELETE FROM bookings WHERE id = :id"),
                {"id": booking_id}
            )
            if result.rowcount > 0:
                st.success("Booking successfully cancelled.")
                return True
            else:
                st.error("Booking not found.")
                return False
    except Exception as e:
        st.error(f"Error cancelling booking: {str(e)}")
        return False

def add_classroom(room_number, capacity, has_smartboard):
    """Add a new classroom"""
    engine = get_db()
    
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO classrooms (room_number, capacity, has_smartboard)
                VALUES (:rnum, :cap, :sb)
            """), {
                "rnum": room_number,
                "cap": int(capacity),
                "sb": has_smartboard
            })
        st.success(f"Classroom {room_number} added successfully!")
        return True
    except Exception as e:
        if 'Duplicate entry' in str(e):
            st.error(f"Classroom {room_number} already exists!")
        else:
            st.error(f"Error adding classroom: {str(e)}")
        return False

def delete_classroom(room_id):
    """Delete a classroom"""
    engine = get_db()
    
    try:
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM classrooms WHERE id = :id"), {"id": room_id})
        st.success("Classroom deleted successfully!")
        return True
    except Exception as e:
        st.error(f"Error deleting classroom: {str(e)}")
        return False
>>>>>>> d54d050 (Iteration 1)

def create_availability_dataframe(selected_date, filter_subject=None, smartboard_only=False):
    """Create a DataFrame for availability display"""
    rooms = st.session_state.classrooms
    
    if smartboard_only:
        rooms = [r for r in rooms if r['hasSmartboard']]
    
    if filter_subject:
        filtered_rooms = []
        for room in rooms:
            include_room = False
            for slot in st.session_state.class_slots:
                booking_key = f"{room['id']}_{slot}_{selected_date}"
                booking = st.session_state.bookings.get(booking_key)
                if (booking and booking['subject'] == filter_subject) or not booking:
                    include_room = True
                    break
            if include_room:
                filtered_rooms.append(room)
        rooms = filtered_rooms
    
    data = []
    for room in rooms:
        row = {
            'Room': f"R{room['roomNumber']}" + (" [SB]" if room['hasSmartboard'] else ""),
            'Capacity': room['capacity']
        }
        
        for slot in st.session_state.class_slots:
            booking_key = f"{room['id']}_{slot}_{selected_date}"
            booking = st.session_state.bookings.get(booking_key)
            
            if booking:
                if filter_subject and booking['subject'] != filter_subject:
                    row[slot] = "Filtered"
                else:
                    guest_icon = "[GL] " if booking.get('isGuestLecture', False) else ""
                    avg_rating = get_average_rating(booking)
                    rating_display = f" [{avg_rating:.1f}]" if avg_rating else ""
                    
                    division_info = ""
                    if not booking.get('isGuestLecture') and booking.get('division'):
                        division_info = f" | Div {booking['division']}"
                    
                    row[slot] = f"{guest_icon}{booking['subject']}\n({booking['facultyName']}){rating_display}{division_info}"
            else:
                row[slot] = "Available"
        
        data.append(row)
    
    if not data:
        return None
    
    return pd.DataFrame(data)

def style_availability_dataframe(df, filter_subject=None):
    """Apply styling to the availability DataFrame"""
    def color_cells(val):
        val = str(val)
        if val == "Available":
            return 'background-color: #dcfce7; color: #166534; font-weight: bold'
        elif val == "Filtered":
            return 'background-color: #e5e7eb; color: #6b7280; font-style: italic'
        elif val in ['Room', 'Capacity'] or pd.isna(val):
            return ''
        else:
            if filter_subject:
                return 'background-color: #fee2e2; color: #991b1b; font-weight: bold; border: 3px solid #fbbf24'
            if val.startswith('[GL]'):
                return 'background-color: #ddd6fe; color: #5b21b6; font-weight: bold'
            return 'background-color: #fee2e2; color: #991b1b; font-weight: bold'
    
    return df.style.map(color_cells)

# -----------------------
# UI: Login/Registration Page
# -----------------------
def render_login_page():
    st.title("Classroom Availability System")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            st.subheader("Login")
            
            with st.form("login_form"):
                role_select = st.selectbox(
                    "Select Role",
                    options=["Student", "Faculty", "Admin"],
                )
                
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                
                submit = st.form_submit_button("Login", type="primary", use_container_width=True)
                
                if submit:
                    if login(username, password):
                        if st.session_state.user_data["role"] != role_select:
                            logout()
                            st.error(f"Invalid credentials for {role_select} role")
                        else:
                            st.success(f"Welcome, {username}!")
                            st.rerun()
                    else:
                        st.error("Invalid username or password")
        
        with tab2:
            st.subheader("Register New Account")
            
            reg_role = st.selectbox(
                "Role",
                options=["Student", "Faculty"],
                key="reg_role_select"
            )
            
            with st.form("register_form"):
                reg_username = st.text_input("Username", placeholder="Choose a username (min 3 chars)")
                reg_password = st.text_input("Password", type="password", placeholder="Choose a password (min 6 chars)")
                reg_password_confirm = st.text_input("Confirm Password", type="password", placeholder="Re-enter password")
                
                if reg_role == "Student":
                    st.markdown("**Student Details**")
                    reg_dept = st.selectbox("Department", DEPARTMENTS)
                    reg_year = st.selectbox("Year", ACADEMIC_YEARS)
                    
                    divisions = DIVISIONS_BY_DEPT.get(reg_dept, [])
                    if divisions:
                        reg_division = st.selectbox("Division", divisions)
                    else:
                        reg_division = ""
                        st.info("No divisions for this department")
                    
                    user_details = {
                        "department": reg_dept,
                        "year": reg_year,
                        "division": reg_division
                    }
                else:  # Faculty
                    st.markdown("**Faculty Details**")
                    reg_name = st.text_input("Full Name", placeholder="Enter your full name")
                    user_details = {
                        "name": reg_name
                    }
                
                submit_reg = st.form_submit_button("Register", type="primary", use_container_width=True)
                
                if submit_reg:
                    if reg_password != reg_password_confirm:
                        st.error("Passwords do not match")
                    elif reg_role == "Faculty" and not reg_name:
                        st.error("Please enter your full name")
                    else:
                        success, message = register_user(reg_username, reg_password, reg_role, **user_details)
                        if success:
                            st.success(message + " You can now login.")
                        else:
                            st.error(message)
        

        st.markdown("---")

# -----------------------
# UI: Student View
# -----------------------
def render_student_view():
    if not require_auth(['Student']):
        return
    
    st.title("Student Interface")
    
    user_data = st.session_state.user_data
    st.info(f"User: {st.session_state.username} | {user_data['department']} | {user_data['year']}" + 
            (f" | Division {user_data['division']}" if user_data.get('division') else ""))
    
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["View Availability", "Give Feedback"])
    
    with tab1:
        st.subheader("Search Filters")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filter_date = st.date_input("Date", value=date.today(), key="student_date")
            filter_year = st.selectbox("Year", [""] + ACADEMIC_YEARS, key="student_year")
        
        with col2:
            filter_semester = st.selectbox("Semester", [""] + ACADEMIC_SEMESTERS, key="student_semester")
            filter_dept = st.selectbox("Department", [""] + DEPARTMENTS, key="student_dept")
        
        with col3:
            subjects = []
            if filter_year and filter_dept:
                subjects = SUBJECTS_BY_DEPT.get(filter_dept, {}).get(filter_year, [])
            filter_subject = st.selectbox("Subject", [""] + subjects, 
                                         key="student_subject",
                                         disabled=not (filter_year and filter_dept))
            
            search_clicked = st.button("Search Availability", type="primary", use_container_width=True)
        
        st.info("Select filters to search. [GL] = Guest Lecture, [Rating] = Average Rating, [SB] = Smartboard")
        
        st.markdown("---")
        
        st.subheader("Classroom Availability")
        
        search_date = filter_date.strftime('%Y-%m-%d')
        search_subject = filter_subject if search_clicked and filter_subject else None
        
        df = create_availability_dataframe(search_date, search_subject)
        
        if df is None:
            st.warning(f"No classrooms found for the selected criteria")
        else:
            st.dataframe(
                style_availability_dataframe(df, search_subject),
                use_container_width=True,
                height=400
            )
            
            if search_subject:
                st.success(f"Showing results for: {search_subject} on {search_date}")
    
    with tab2:
        st.subheader("Give Feedback for Completed Lectures")
        
        completed_lectures = []
        for booking in st.session_state.bookings.values():
            if is_lecture_completed(booking['date'], booking['slot']):
                if can_student_give_feedback(booking, user_data):
                    completed_lectures.append(booking)
        
        completed_lectures.sort(key=lambda x: x['date'], reverse=True)
        
        if not completed_lectures:
            st.info("No completed lectures available for feedback.")
        else:
            st.success(f"Found {len(completed_lectures)} completed lecture(s) eligible for feedback")
            
            for idx, booking in enumerate(completed_lectures):
                room = get_classroom_by_id(booking['classroomId'])
                room_display = f"R{room['roomNumber']}" if room else "Unknown"
                
                is_guest = booking.get('isGuestLecture', False)
                
                with st.expander(
                    f"{'[GL]' if is_guest else ''} {booking['subject']} - {booking['date']} {booking['slot']}", 
                    expanded=(idx == 0)
                ):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"**Subject:** {booking['subject']}")
                        st.markdown(f"**Faculty:** {booking['facultyName']}")
                        
                        if not is_guest:
                            st.markdown(f"**Department:** {booking.get('department', 'N/A')}")
                            st.markdown(f"**Year:** {booking.get('year', 'N/A')}")
                            if booking.get('division'):
                                st.markdown(f"**Division:** {booking['division']}")
                        
                        st.markdown(f"**Room:** {room_display} | **Date:** {booking['date']} | **Time:** {booking['slot']}")
                    
                    with col2:
                        avg_rating = get_average_rating(booking)
                        feedback_count = len(booking.get('feedback', []))
                        
                        if avg_rating:
                            st.metric("Average Rating", f"{avg_rating:.1f}/5")
                            st.caption(f"{feedback_count} feedback(s)")
                        else:
                            st.info("No ratings yet")
                    
                    st.markdown("---")
                    
                    if has_student_feedback(booking['bookingKey'], st.session_state.username):
                        st.success("You have already submitted feedback for this lecture!")
                        
                        student_feedback = next(f for f in booking['feedback'] 
                                              if f['studentId'] == st.session_state.username)
                        st.markdown(f"**Your Rating:** {student_feedback['rating']}/5")
                        if student_feedback.get('comments'):
                            st.markdown(f"**Your Comments:** {student_feedback['comments']}")
                    else:
                        st.markdown("**Rate this lecture:**")
                        
                        rating = st.slider(
                            "Rating (1-5 stars)",
                            min_value=1,
                            max_value=5,
                            value=3,
                            key=f"rating_{booking['id']}"
                        )
                        
                        comments = st.text_area(
                            "Additional Comments (Optional):",
                            placeholder="Share your experience, what went well, what could be improved...",
                            key=f"comments_{booking['id']}",
                            height=100
                        )
                        
                        if st.button("Submit Feedback", 
                                   key=f"submit_{booking['id']}", 
                                   type="primary",
                                   use_container_width=True):
                            if submit_feedback(booking['bookingKey'], st.session_state.username, rating, comments):
                                st.rerun()

# -----------------------
# UI: Faculty View
# -----------------------
def render_faculty_view():
    if not require_auth(['Faculty']):
        return

    st.title("Faculty Interface")
    user_data = st.session_state.user_data
    st.info(f"User: {user_data.get('name', st.session_state.username)} | Faculty")

    st.markdown("---")

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.subheader("1. Book a Classroom Slot")

        faculty_name = st.text_input(
            "Faculty Name",
            value=user_data.get("name", st.session_state.username),
            key="faculty_name_field"
        )

        booking_type = st.radio(
            "Booking Type",
            ["Regular Class", "Guest Lecture"],
            horizontal=True,
            key="faculty_booking_type"
        )
        is_guest = booking_type == "Guest Lecture"

        booking_date = st.date_input(
            "Date",
            value=date.today(),
            key="faculty_booking_date"
        )

        classroom_options = [
            (r["id"], f"R{r['roomNumber']} ({'Smartboard' if r['hasSmartboard'] else 'Standard'})")
            for r in st.session_state.classrooms
        ]

        classroom = st.selectbox(
            "Classroom",
            options=[opt[0] for opt in classroom_options],
            format_func=lambda x: next(opt[1] for opt in classroom_options if opt[0] == x),
            key="faculty_classroom_select"
        )

        slot = st.selectbox(
            "Time Slot",
            st.session_state.class_slots,
            key="faculty_slot_select"
        )

        if is_guest:
            lecture_title = st.text_input("Lecture Title", key="guest_lecture_title")

            guest_dept = st.selectbox(
                "Department Restriction (optional)",
                ["All Departments"] + DEPARTMENTS,
                key="guest_lecture_dept"
            )

            subject = lecture_title
            dept = None if guest_dept == "All Departments" else guest_dept
            year = None
            division = None

        else:
            colA, colB = st.columns(2)

            with colA:
                dept = st.selectbox(
                    "Department",
                    DEPARTMENTS,
                    key="faculty_dept_select"
                )

            with colB:
                year = st.selectbox(
                    "Year",
                    ACADEMIC_YEARS,
                    key="faculty_year_select"
                )

            divisions = DIVISIONS_BY_DEPT.get(dept, [])
            if divisions:
                division = st.selectbox(
                    "Division",
                    divisions,
                    key="faculty_division_select"
                )
            else:
                st.text_input("Division", "N/A", disabled=True)
                division = None

            subject_list = SUBJECTS_BY_DEPT.get(dept, {}).get(year, [])

            if subject_list:
                subject = st.selectbox(
                    "Subject",
                    subject_list,
                    key="faculty_subject_select"
                )
            else:
                subject = st.text_input(
                    "Subject/Course Name",
                    key="faculty_subject_custom"
                )

            lecture_title = None
            guest_dept = None

        with st.form("faculty_booking_form"):
            submit = st.form_submit_button(
                "Book Guest Lecture" if is_guest else "Book Classroom",
                type="primary"
            )

            if submit:
                success = create_booking(
                    classroom_id=classroom,
                    slot=slot,
                    subject=subject,
                    faculty_name=faculty_name,
                    booking_date=booking_date.strftime("%Y-%m-%d"),
                    is_guest_lecture=is_guest,
                    lecture_title=lecture_title,
                    department=dept,
                    year=year,
                    division=division,
                    guest_dept_restriction=guest_dept,
                )

                if success:
                    st.rerun()

    with col_right:
        st.subheader("3. View Real-time Availability")

        view_date = st.date_input(
            "Select Date",
            value=date.today(),
            key="faculty_view_date"
        )

        smartboard_only = st.checkbox("Smartboard Only", key="faculty_smartboard_toggle")

        df = create_availability_dataframe(
            view_date.strftime("%Y-%m-%d"),
            smartboard_only=smartboard_only
        )

        if df is None:
            st.warning("No classrooms match your criteria.")
        else:
            st.dataframe(
                style_availability_dataframe(df),
                use_container_width=True,
                height=500
            )

    st.markdown("---")
    st.subheader("2. My Bookings & Feedback")

    my_bookings = [
        b for b in st.session_state.bookings.values()
        if b["facultyId"] == st.session_state.username
    ]

    if not my_bookings:
        st.info("You have no active bookings.")
    else:
        for booking in my_bookings:
            room = get_classroom_by_id(booking["classroomId"])
            room_display = f"R{room['roomNumber']}" if room else "N/A"

            avg_rating = get_average_rating(booking)
            rating_display = f"{avg_rating:.1f}" if avg_rating else "No rating"

            st.markdown(
                f"{booking['subject']} | {room_display}<br>"
                f"Date: {booking['date']} Time: {booking['slot']}",
                unsafe_allow_html=True
            )

            st.caption(f"Feedback: {len(booking.get('feedback', []))} | Rating: {rating_display}")

            if st.button("Remove", key=f"remove_{booking['id']}"):
                cancel_booking(booking["bookingKey"])
                st.rerun()

            st.divider()

# -----------------------
# UI: Admin View
# -----------------------
def render_admin_view():
    if not require_auth(['Admin']):
        return
    
    st.title("Admin Interface")
    
    st.info(f"User: {st.session_state.username} | Administrator")
    
    st.markdown("---")
    
    col_left, col_right = st.columns(2, gap="large")
    
    with col_left:
        st.subheader("System Configuration")
        
        st.markdown("**Manage Class Time Slots**")
        
        slots_text = st.text_area(
            "Time Slots (one per line)",
            value="\n".join(st.session_state.class_slots),
            height=150,
            help="Enter time slots in format: HH:MM - HH:MM"
        )
        
        classroom_limit = st.number_input(
            "Classroom Count Limit",
            min_value=1,
            max_value=500,
            value=st.session_state.classroom_limit,
            help="Maximum number of classrooms allowed in the system"
        )
        
        if st.button("Update System Settings", type="primary", use_container_width=True):
            new_slots = [s.strip() for s in slots_text.split('\n') if s.strip()]
            if new_slots:
                st.session_state.class_slots = new_slots
                st.session_state.classroom_limit = classroom_limit
                save_data()
                st.success("System settings updated successfully!")
                st.rerun()
            else:
                st.error("Slot list cannot be empty")
        
        st.markdown("---")
        
        st.subheader("Feedback Analytics")
        
        all_ratings = []
        guest_ratings = []
        regular_ratings = []
        
        for booking in st.session_state.bookings.values():
            if 'feedback' in booking and booking['feedback']:
                ratings = [f['rating'] for f in booking['feedback']]
                all_ratings.extend(ratings)
                
                if booking.get('isGuestLecture'):
                    guest_ratings.extend(ratings)
                else:
                    regular_ratings.extend(ratings)
        
        if all_ratings:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                avg_overall = sum(all_ratings) / len(all_ratings)
                st.metric("Overall Avg Rating", f"{avg_overall:.2f}/5")
                st.caption(f"{len(all_ratings)} total feedbacks")
            
            with col2:
                if guest_ratings:
                    avg_guest = sum(guest_ratings) / len(guest_ratings)
                    st.metric("Guest Lectures", f"{avg_guest:.2f}/5")
                    st.caption(f"{len(guest_ratings)} feedbacks")
                else:
                    st.metric("Guest Lectures", "No data")
            
            with col3:
                if regular_ratings:
                    avg_regular = sum(regular_ratings) / len(regular_ratings)
                    st.metric("Regular Classes", f"{avg_regular:.2f}/5")
                    st.caption(f"{len(regular_ratings)} feedbacks")
                else:
                    st.metric("Regular Classes", "No data")
            
            st.markdown("---")
            st.markdown("**Top Rated Lectures**")
            
            bookings_with_ratings = []
            for booking in st.session_state.bookings.values():
                avg = get_average_rating(booking)
                if avg:
                    bookings_with_ratings.append((booking, avg))
            
            bookings_with_ratings.sort(key=lambda x: x[1], reverse=True)
            
            if bookings_with_ratings:
                for i, (booking, avg) in enumerate(bookings_with_ratings[:5]):
                    badge = "[GL]" if booking.get('isGuestLecture') else "[RC]"
                    st.markdown(f"{i+1}. {badge} **{booking['subject']}** - {avg:.2f}/5 ({len(booking['feedback'])} reviews)")
            else:
                st.info("No rated lectures yet")
        else:
            st.info("No feedback data available yet")
    
    with col_right:
        st.subheader("Classroom Management")
        
        with st.expander("Add New Classroom", expanded=False):
            with st.form("add_classroom_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_room = st.text_input("Room Number", placeholder="e.g., 101")
                    new_capacity = st.number_input("Capacity", min_value=1, max_value=200, value=30)
                
                with col2:
                    new_smartboard = st.checkbox("Has Smartboard")
                    st.write("")
                
                submit = st.form_submit_button("Add Classroom", type="primary", use_container_width=True)
                
                if submit:
                    if new_room:
                        add_classroom(new_room, new_capacity, new_smartboard)
                        st.rerun()
                    else:
                        st.error("Please enter a room number")
        
        st.markdown("---")
        
        st.markdown(f"**Existing Classrooms ({len(st.session_state.classrooms)})**")
        
        if not st.session_state.classrooms:
            st.info("No classrooms registered in the system")
        else:
            for idx, room in enumerate(st.session_state.classrooms):
                with st.container():
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.markdown(f"**Room {room['roomNumber']}**")
                    
                    with col2:
                        smartboard_icon = "[SB] " if room['hasSmartboard'] else ""
                        st.caption(f"Capacity: {room['capacity']} | {smartboard_icon}{'Smartboard' if room['hasSmartboard'] else 'Standard'}")
                    
                    with col3:
                        if st.button("Delete", key=f"delete_{room['id']}", help="Delete classroom"):
                            delete_classroom(room['id'])
                            st.rerun()
                    
                    if idx < len(st.session_state.classrooms) - 1:
                        st.divider()
    
    st.markdown("---")
    st.subheader("All Bookings Overview")
    
    if st.session_state.bookings:
        bookings_list = []
        for booking in st.session_state.bookings.values():
            room = get_classroom_by_id(booking['classroomId'])
            avg_rating = get_average_rating(booking)
            
            bookings_list.append({
                'Date': booking['date'],
                'Slot': booking['slot'],
                'Subject': booking['subject'],
                'Faculty': booking['facultyName'],
                'Room': f"R{room['roomNumber']}" if room else "N/A",
                'Type': 'Guest' if booking.get('isGuestLecture') else 'Regular',
                'Department': booking.get('department', 'N/A'),
                'Year': booking.get('year', 'N/A'),
                'Division': booking.get('division', 'N/A'),
                'Avg Rating': f"{avg_rating:.1f}" if avg_rating else "No ratings",
                'Feedback Count': len(booking.get('feedback', []))
            })
        
        df = pd.DataFrame(bookings_list)
        df = df.sort_values('Date', ascending=False)
        
        st.dataframe(df, use_container_width=True, height=400)
    else:
        st.info("No bookings in the system")

# -----------------------
# Sidebar
# -----------------------
def render_sidebar():
    with st.sidebar:
        st.markdown("### Classroom Availability System")
        
        if st.session_state.logged_in:
            st.success(f"Logged in as **{st.session_state.username}**")
            st.caption(f"Role: {st.session_state.user_role}")
            
            if st.button("Logout", use_container_width=True):
                logout()
                st.rerun()
        else:
            st.warning("Not logged in")
        
        st.markdown("---")
        
        st.subheader("System Statistics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Classrooms", len(st.session_state.classrooms))
            st.metric("Total Bookings", len(st.session_state.bookings))
        
        with col2:
            if st.session_state.logged_in and st.session_state.user_role == 'Faculty':
                my_bookings_count = len([b for b in st.session_state.bookings.values() 
                                         if b['facultyId'] == st.session_state.username])
                st.metric("My Bookings", my_bookings_count)
            else:
                guest_lectures = len([b for b in st.session_state.bookings.values() 
                                     if b.get('isGuestLecture', False)])
                st.metric("Guest Lectures", guest_lectures)
            
            total_feedback = sum(len(b.get('feedback', [])) for b in st.session_state.bookings.values())
            st.metric("Total Feedback", total_feedback)
        
        st.markdown("---")

# -----------------------
# Main app
# -----------------------
def main():
    init_session_state()
    
    render_sidebar()
    
    if not st.session_state.logged_in:
        render_login_page()
    elif st.session_state.user_role == 'Student':
        render_student_view()
    elif st.session_state.user_role == 'Faculty':
        render_faculty_view()
    elif st.session_state.user_role == 'Admin':
        render_admin_view()
    
    st.markdown("---")
    st.caption("Classroom Management System | Built with Streamlit")

if __name__ == "__main__":
    main()
