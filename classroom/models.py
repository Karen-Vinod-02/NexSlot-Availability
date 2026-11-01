from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import datetime

class User(AbstractUser):
    ROLE_CHOICES = [
        ('Admin', 'Administrator'),
        ('Faculty', 'Faculty'),
        ('Student', 'Student'),
        ('Employee', 'Employee'),
    ]
    
    # Override email to be unique for login
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    department = models.CharField(max_length=255, blank=True, null=True)
    year = models.CharField(max_length=50, blank=True, null=True) # Stores 'Year' (Academic) or 'Level' (Corporate)
    division = models.CharField(max_length=50, blank=True, null=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'

class AuthorizedEmail(models.Model):
    """
    Verification table: Users can only register if their email exists here.
    """
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=User.ROLE_CHOICES)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    
    # Student/Employee specific fields
    department = models.CharField(max_length=255, blank=True, null=True)
    year = models.CharField(max_length=50, blank=True, null=True)
    division = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = 'authorized_emails'

    def __str__(self):
        return f"{self.email} ({self.role})"

class Classroom(models.Model):
    room_number = models.CharField(max_length=50, unique=True)
    capacity = models.IntegerField(validators=[MinValueValidator(1)])
    has_smartboard = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'classrooms'
        ordering = ['room_number']
    
    def __str__(self):
        return f"Room {self.room_number}"

class Subject(models.Model):
    """
    Used primarily for College mode to populate dropdowns.
    Corporate mode uses free-text subjects in Booking.
    """
    name = models.CharField(max_length=255)
    department = models.CharField(max_length=255)
    year = models.CharField(max_length=50)     
    semester = models.CharField(max_length=50) 
    
    class Meta:
        db_table = 'subjects'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.department})"

class Booking(models.Model):
    STATUS_CHOICES = [
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled'),
        ('Completed', 'Completed'),
    ]
    
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='bookings')
    faculty = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    booking_date = models.DateField()
    slot = models.CharField(max_length=50)
    
    # Details: Supports both Academic Subject (Dropdown) and Corporate Topic (Free Text)
    subject = models.CharField(max_length=255, blank=True, null=True)
    faculty_name = models.CharField(max_length=255)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Confirmed')
    
    # Type of Lecture/Meeting
    is_guest_lecture = models.BooleanField(default=False)
    lecture_title = models.CharField(max_length=255, blank=True, null=True)
    guest_speaker = models.CharField(max_length=100, blank=True, null=True)
    
    # Target Audience
    department = models.CharField(max_length=255, blank=True, null=True)
    year = models.CharField(max_length=50, blank=True, null=True)
    division = models.CharField(max_length=50, blank=True, null=True)
    semester = models.CharField(max_length=50, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'bookings'
        unique_together = ['classroom', 'booking_date', 'slot']
        ordering = ['-booking_date', 'slot']
    
    def __str__(self):
        return f"{self.subject or self.lecture_title} - {self.booking_date}"
    
    def is_past_or_ongoing(self):
        now = timezone.localtime()
        lecture_date = self.booking_date
        
        if lecture_date < now.date():
            return True
        elif lecture_date == now.date():
            try:
                start_str = self.slot.split(' - ')[0]
                start_time = datetime.strptime(start_str, "%H:%M").time()
                # 12-hour adjustment for typical working hours (1-6 PM treated as 13:00-18:00)
                if 1 <= start_time.hour <= 6:
                     start_time = start_time.replace(hour=start_time.hour + 12)
                return now.time() >= start_time
            except:
                return False
        return False

    def get_average_rating(self):
        feedbacks = self.feedbacks.all()
        if not feedbacks: return None
        return sum(f.rating for f in feedbacks) / len(feedbacks)

class Feedback(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='feedbacks')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comments = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'feedback'
        unique_together = ['booking', 'student']
        ordering = ['-created_at']

class Document(models.Model):
    """
    Stores uploaded files for RAG processing (Chatbot knowledge base).
    """
    title = models.CharField(max_length=255, blank=True)
    file = models.FileField(upload_to='data/')  # Saves to project_root/data/
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='documents')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    
    # Metadata for Intelligent Indexing
    department = models.CharField(max_length=255, blank=True, null=True)
    year = models.CharField(max_length=50, blank=True, null=True)
    semester = models.CharField(max_length=50, blank=True, null=True)
    
    class Meta:
        db_table = 'documents'
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.title or self.file.name

class SystemConfig(models.Model):
    # Functional Config
    class_slots = models.JSONField(default=list)
    classroom_limit = models.IntegerField(default=100)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Branding
    site_name = models.CharField(max_length=50, default="Classroom")
    site_logo = models.FileField(upload_to='branding/', null=True, blank=True)
    org_type = models.CharField(max_length=20, default='College', choices=[('College', 'College'), ('Corporate', 'Corporate')])

    # Colors
    primary_color = models.CharField(max_length=7, default="#2563EB")
    accent_color = models.CharField(max_length=7, default="#F59E0B", blank=True, null=True)
    secondary_color = models.CharField(max_length=7, default="#F3F4F6")
    navbar_color = models.CharField(max_length=7, default="#FFFFFF")
    sidebar_color = models.CharField(max_length=7, default="#FFFFFF")

    # AI Assistant Configuration
    chatbot_enabled = models.BooleanField(default=True)
    chatbot_source_url = models.URLField(blank=True, null=True, help_text="External source URL for knowledge base")
    chatbot_greeting = models.CharField(max_length=255, default="Hello! How can I assist you today?")

    class Meta:
        db_table = 'config'
    
    @classmethod
    def get_config(cls):
        config, created = cls.objects.get_or_create(pk=1)
        if created or not config.class_slots:
            # Default slots if created or empty
            config.class_slots = ["8:00 - 9:30", "9:40 - 11:10", "11:20 - 12:50", "13:30 - 15:00"]
            config.save()
        return config

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)