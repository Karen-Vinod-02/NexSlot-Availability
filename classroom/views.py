from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg, Count
from django.http import JsonResponse
from datetime import date
from .models import User, Classroom, Booking, Feedback, SystemConfig, Subject, AuthorizedEmail
from .forms import UserRegistrationForm, UserLoginForm, ForgotPasswordForm, ClassroomForm, BookingForm, FeedbackForm, get_allowed_divisions, get_allowed_semesters

# -------------------------
# AUTHENTICATION VIEWS
# -------------------------

def user_login(request):
    if request.user.is_authenticated:
        return redirect('classroom:dashboard')
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            # The form field is named 'username' but contains the email string
            email_credential = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            # --- FIX: DIRECT AUTHENTICATION ---
            # Instead of looking up the user object first, we pass the email 
            # directly to authenticate().
            user = authenticate(request, username=email_credential, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome, {user.first_name}!')
                return redirect('classroom:dashboard')
            else:
                # If auth fails, check if it's a first-time user for a better error message
                if AuthorizedEmail.objects.filter(email=email_credential).exists():
                     # If they are authorized but auth failed, they likely haven't set a password yet
                     messages.error(request, "Invalid credentials. If this is your first time, please activate your account.")
                else:
                     messages.error(request, 'Invalid email or password.')
        else:
            messages.error(request, 'Invalid email format or password')
    else:
        form = UserLoginForm()
    
    return render(request, 'classroom/login.html', {'form': form})

def forgot_password(request):
    """
    DEV MODE: Instant Password Set (Bypasses Email)
    If email is in AuthorizedEmail, allow setting password immediately.
    """
    if request.method == 'POST':
        # reusing the Registration Form because it already has password fields
        form = UserRegistrationForm(request.POST) 
        
        # We manually validate because UserRegistrationForm expects a unique email check
        # which might fail if the User object already exists.
        email = request.POST.get('email')
        password = request.POST.get('password1')
        confirm = request.POST.get('password2')

        if not email or not password:
            messages.error(request, "All fields are required.")
            return render(request, 'classroom/forgot_password.html', {'form': UserRegistrationForm()})

        if password != confirm:
            messages.error(request, "Passwords do not match.")
            return render(request, 'classroom/forgot_password.html', {'form': UserRegistrationForm(initial={'email': email})})

        try:
            # 1. Check Authority
            auth_entry = AuthorizedEmail.objects.get(email=email)

            # 2. Get or Create User
            user, created = User.objects.get_or_create(username=email, email=email)

            # 3. Update Attributes
            user.first_name = auth_entry.first_name
            user.last_name = auth_entry.last_name
            user.role = auth_entry.role

            # 4. Decouple Faculty Logic
            if user.role == 'Student':
                user.department = auth_entry.department
                user.year = auth_entry.year
                user.division = auth_entry.division
            else:
                user.department = None
                user.year = None
                user.division = None
            
            # 5. SET PASSWORD DIRECTLY
            user.set_password(password)
            user.save()

            status_msg = "Account created!" if created else "Password updated!"
            messages.success(request, f"{status_msg} You can now log in.")
            return redirect('classroom:login')

        except AuthorizedEmail.DoesNotExist:
            messages.error(request, "This email is not authorized.")
            return render(request, 'classroom/forgot_password.html', {'form': UserRegistrationForm(initial={'email': email})})

    else:
        # We use the Registration form here because it has the Password boxes we need
        form = UserRegistrationForm()  
    return render(request, 'classroom/forgot_password.html', {'form': form})

@login_required
def user_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('classroom:login')

@login_required
def dashboard(request):
    if request.user.is_superuser:
        return redirect('classroom:admin_dashboard')
    if request.user.role == 'Student':
        return redirect('classroom:student_dashboard')
    elif request.user.role == 'Faculty':
        return redirect('classroom:faculty_dashboard')
    elif request.user.role == 'Admin':
        return redirect('classroom:admin_dashboard')
    
    return redirect('classroom:login')

# -------------------------
# DASHBOARD VIEWS
# -------------------------

@login_required
def student_dashboard(request):
    if request.user.role != 'Student':
        messages.error(request, 'Access denied')
        return redirect('classroom:dashboard')
    
    today = date.today().isoformat()
    completed_bookings = Booking.objects.filter(
        Q(booking_date__lt=today) | 
        Q(booking_date=today, status='Completed')
    )
    
    eligible_bookings = []
    for booking in completed_bookings:
        # Check if booking is relevant to this student
        if booking.is_guest_lecture:
            # Guest lectures: Open to all OR specific department
            if not booking.department or booking.department == request.user.department:
                eligible_bookings.append(booking)
        else:
            # Regular lectures: Must match Dept, Year, and Division
            if (booking.department == request.user.department and 
                booking.year == request.user.year and
                (not booking.division or booking.division == request.user.division)):
                eligible_bookings.append(booking)
    
    # Check if feedback is already submitted
    for booking in eligible_bookings:
        booking.has_feedback = Feedback.objects.filter(
            booking=booking, 
            student=request.user
        ).exists()
    
    context = {
        'today': today,
        'completed_bookings': eligible_bookings,
        'classrooms': Classroom.objects.all(),
        'config': SystemConfig.get_config(),
    }
    return render(request, 'classroom/student_dashboard.html', context)

@login_required
def faculty_dashboard(request):
    if request.user.role != 'Faculty':
        messages.error(request, 'Access denied')
        return redirect('classroom:dashboard')
    
    my_bookings = Booking.objects.filter(faculty=request.user)
    
    for booking in my_bookings:
        booking.avg_rating = booking.get_average_rating()
        booking.feedback_count = booking.feedbacks.count()
    
    context = {
        'my_bookings': my_bookings,
        'classrooms': Classroom.objects.all(),
        'config': SystemConfig.get_config(),
    }
    return render(request, 'classroom/faculty_dashboard.html', context)

@login_required
def admin_dashboard(request):
    if request.user.role != 'Admin' and not request.user.is_superuser:
        messages.error(request, 'Access denied')
        return redirect('classroom:dashboard')
    
    all_bookings = Booking.objects.all()
    avg_rating = Feedback.objects.aggregate(Avg('rating'))['rating__avg']
    
    guest_feedback = Feedback.objects.filter(booking__is_guest_lecture=True)
    regular_feedback = Feedback.objects.filter(booking__is_guest_lecture=False)
    
    guest_avg = guest_feedback.aggregate(Avg('rating'))['rating__avg']
    regular_avg = regular_feedback.aggregate(Avg('rating'))['rating__avg']
    
    top_lectures = Booking.objects.annotate(
        avg_rating=Avg('feedbacks__rating'),
        feedback_count=Count('feedbacks')
    ).filter(feedback_count__gt=0).order_by('-avg_rating')[:5]
    
    context = {
        'classrooms': Classroom.objects.all(),
        'all_bookings': all_bookings,
        'total_feedback': Feedback.objects.count(),
        'avg_rating': avg_rating,
        'guest_avg': guest_avg,
        'regular_avg': regular_avg,
        'guest_feedback_count': guest_feedback.count(),
        'regular_feedback_count': regular_feedback.count(),
        'top_lectures': top_lectures,
        'config': SystemConfig.get_config(),
    }
    return render(request, 'classroom/admin_dashboard.html', context)

# -------------------------
# ACTION VIEWS
# -------------------------

@login_required
def create_booking(request):
    if request.user.role != 'Faculty':
        messages.error(request, 'Only faculty can create bookings')
        return redirect('classroom:dashboard')
    
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.faculty = request.user
            
            # Use faculty name if not manually entered
            if not booking.faculty_name:
                booking.faculty_name = f"{request.user.first_name} {request.user.last_name}"

            if booking.is_guest_lecture:
                if not booking.lecture_title:
                    messages.error(request, "Lecture Title is required for Guest Lectures.")
                    return render(request, 'classroom/create_booking.html', {'form': form})
            else:
                subject_id = form.cleaned_data.get('subject')
                if not subject_id:
                    messages.error(request, "Subject is required for Regular Lectures.")
                    return render(request, 'classroom/create_booking.html', {'form': form})
                
                # Handle Subject Logic (ID vs Name)
                try:
                    if str(subject_id).isdigit():
                          subject_obj = Subject.objects.get(id=int(subject_id))
                          booking.subject = subject_obj.name
                    else:
                          booking.subject = subject_id
                except (Subject.DoesNotExist, ValueError):
                    booking.subject = subject_id

            conflict = Booking.objects.filter(
                classroom=booking.classroom,
                booking_date=booking.booking_date,
                slot=booking.slot
            ).exists()
            
            if conflict:
                messages.error(request, 'This classroom is already booked for this slot!')
            else:
                booking.save()
                messages.success(request, 'Booking created successfully!')
                return redirect('classroom:faculty_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BookingForm()
    
    return render(request, 'classroom/create_booking.html', {'form': form})

@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.user.role != 'Faculty' or booking.faculty != request.user:
        messages.error(request, 'You cannot cancel this booking')
        return redirect('classroom:dashboard')
    
    booking.delete()
    messages.success(request, 'Booking cancelled successfully')
    return redirect('classroom:faculty_dashboard')

@login_required
def submit_feedback(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.user.role != 'Student':
        messages.error(request, 'Only students can submit feedback')
        return redirect('classroom:dashboard')
    
    if Feedback.objects.filter(booking=booking, student=request.user).exists():
        messages.warning(request, 'You have already submitted feedback for this lecture')
        return redirect('classroom:student_dashboard')
    
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.booking = booking
            feedback.student = request.user
            feedback.save()
            messages.success(request, 'Thank you for your feedback!')
            return redirect('classroom:student_dashboard')
    else:
        form = FeedbackForm()
    
    return render(request, 'classroom/submit_feedback.html', {'form': form, 'booking': booking})

@login_required
def add_classroom(request):
    if request.user.role != 'Admin' and not request.user.is_superuser:
        messages.error(request, 'Access denied')
        return redirect('classroom:dashboard')
    
    if request.method == 'POST':
        form = ClassroomForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Classroom added successfully!')
            return redirect('classroom:admin_dashboard')
    else:
        form = ClassroomForm()
    
    return render(request, 'classroom/add_classroom.html', {'form': form})

@login_required
def delete_classroom(request, classroom_id):
    if request.user.role != 'Admin' and not request.user.is_superuser:
        messages.error(request, 'Access denied')
        return redirect('classroom:dashboard')
    
    classroom = get_object_or_404(Classroom, id=classroom_id)
    classroom.delete()
    messages.success(request, 'Classroom deleted successfully!')
    return redirect('classroom:admin_dashboard')

@login_required
def view_availability(request):
    selected_date = request.GET.get('date', date.today().isoformat())
    classrooms = Classroom.objects.all()
    config = SystemConfig.get_config()
    
    availability_data = []
    for classroom in classrooms:
        classroom_data = {'classroom': classroom, 'slots': {}}
        for slot in config.class_slots:
            booking = Booking.objects.filter(
                classroom=classroom,
                booking_date=selected_date,
                slot=slot
            ).first()
            classroom_data['slots'][slot] = booking
        availability_data.append(classroom_data)
    
    context = {
        'availability_data': availability_data,
        'selected_date': selected_date,
        'config': config,
    }
    return render(request, 'classroom/view_availability.html', context)

# -------------------------
# AJAX VIEWS (DYNAMIC DROPDOWNS)
# -------------------------

def load_subjects(request):
    department = request.GET.get('department')
    year = request.GET.get('year')
    semester = request.GET.get('semester')
    
    subjects = Subject.objects.none()
    if department and year and semester:
        subjects = Subject.objects.filter(
            department=department, 
            year=year, 
            semester=semester
        ).order_by('name')
        
    return JsonResponse(list(subjects.values('id', 'name')), safe=False)

def load_semesters(request):
    year = request.GET.get('year')
    semesters = get_allowed_semesters(year)
    data = [{'id': s, 'name': s} for s in semesters]
    return JsonResponse(data, safe=False)

def load_divisions(request):
    department = request.GET.get('department')
    divisions = get_allowed_divisions(department)
    data = [{'id': d, 'name': d} for d in divisions]
    return JsonResponse(data, safe=False)