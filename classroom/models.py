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
    ]
    
    # Override email to be unique for login
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    department = models.CharField(max_length=255, blank=True, null=True)
    year = models.CharField(max_length=50, blank=True, null=True)
    division = models.CharField(max_length=50, blank=True, null=True)
    
    # Set Email as the login field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username'] # Username is still required by Django internals

    class Meta:
        db_table = 'users'

# --- NEW: VERIFICATION DATABASE ---
class AuthorizedEmail(models.Model):
    """
    This table maps emails to their pre-defined details.
    Users can only register/login if their email is in this table.
    """
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=User.ROLE_CHOICES)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    
    # Student specific fields (nullable for Faculty)
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
    name = models.CharField(max_length=255)
    department = models.CharField(max_length=255)
    year = models.CharField(max_length=50)     # e.g., SE, TE, BE
    semester = models.CharField(max_length=50) # e.g., Sem 3, Sem 4
    
    class Meta:
        db_table = 'subjects'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.department} - {self.year})"

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
    
    # Lecture Details
    subject = models.CharField(max_length=255, blank=True, null=True)
    faculty_name = models.CharField(max_length=255)
    
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Confirmed')
    
    # Type of Lecture
    is_guest_lecture = models.BooleanField(default=False)
    lecture_title = models.CharField(max_length=255, blank=True, null=True)
    guest_speaker = models.CharField(max_length=100, blank=True, null=True)  # <-- Added Field
    
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
        """Check if lecture is active or finished to enable feedback"""
        now = timezone.localtime()
        lecture_date = self.booking_date
        
        if lecture_date < now.date():
            return True # Past date
        elif lecture_date == now.date():
            # Parse slot time "8:00 - 9:30" -> get start time
            try:
                start_str = self.slot.split(' - ')[0]
                start_time = datetime.strptime(start_str, "%H:%M").time()
                return now.time() >= start_time # Active if start time passed
            except:
                return False
        return False

    def get_average_rating(self):
        feedbacks = self.feedbacks.all()
        if not feedbacks:
            return None
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

class SystemConfig(models.Model):
    # Functional Config
    class_slots = models.JSONField(default=list)
    classroom_limit = models.IntegerField(default=100)
    updated_at = models.DateTimeField(auto_now=True)
    
    # --- BRANDING / CUSTOMIZATION ---
    site_name = models.CharField(max_length=50, default="Classroom", help_text="The name displayed in the navbar")
    
    # --- FIX: Changed to FileField to bypass PIL/Numpy crash ---
    site_logo = models.FileField(upload_to='branding/', null=True, blank=True, help_text="Transparent PNG recommended")
    
    primary_color = models.CharField(max_length=7, default="#2563EB", help_text="Hex code (e.g. #2563EB)")
    accent_color = models.CharField(max_length=7, default="#F59E0B", blank=True, null=True, help_text="Optional Accent Color")
    secondary_color = models.CharField(max_length=7, default="#F3F4F6", help_text="Hex code (e.g. #F3F4F6)")

    class Meta:
        db_table = 'config'
    
    @classmethod
    def get_config(cls):
        # Ensure only one config row exists (ID=1)
        config, created = cls.objects.get_or_create(pk=1)
        if created:
            config.class_slots = [
                "8:00 - 9:30", "9:40 - 11:10", "11:20 - 12:50", "13:30 - 15:00", "15:10 - 16:40"
            ]
            config.save()
        return config

    def save(self, *args, **kwargs):
        # Force ID to 1 to maintain Singleton pattern
        self.pk = 1
        super().save(*args, **kwargs)