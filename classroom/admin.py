from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Classroom, Booking, Feedback, SystemConfig

# Custom User admin
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Display these columns in the user list
    list_display = ['username', 'email', 'role', 'department', 'year', 'division', 'is_staff', 'is_active']
    list_filter = ['role', 'department', 'year', 'is_staff', 'is_active']
    
    # Add extra fields to the fieldsets
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'department', 'year', 'division')
        }),
    )
    
    # Add extra fields to the add_fieldsets for user creation
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'department', 'year', 'division')
        }),
    )
    
    search_fields = ['username', 'email']
    ordering = ['username']

# Classroom admin
@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ['room_number', 'capacity', 'has_smartboard', 'created_at']
    list_filter = ['has_smartboard']
    search_fields = ['room_number']

# Booking admin
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['subject', 'classroom', 'faculty', 'booking_date', 'slot', 'status', 'is_guest_lecture', 'department']
    list_filter = ['status', 'is_guest_lecture', 'booking_date', 'department']
    search_fields = ['subject', 'faculty__username', 'faculty_name']
    date_hierarchy = 'booking_date'

# Feedback admin
@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['booking', 'student', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['booking__subject', 'student__username']

# SystemConfig admin
@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    list_display = ['classroom_limit', 'updated_at']
