from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg, Count
from django.http import JsonResponse
from datetime import date, datetime
from .models import User, Classroom, Booking, Feedback, SystemConfig, Subject, AuthorizedEmail
from .forms import UserRegistrationForm, UserLoginForm, ForgotPasswordForm, ClassroomForm, BookingForm, FeedbackForm, SystemBrandingForm, get_allowed_divisions, get_allowed_semesters

# -------------------------
# AUTHENTICATION VIEWS
# -------------------------

def user_login(request):
    if request.user.is_authenticated:
        return redirect('classroom:dashboard')
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            email_credential = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            # Direct Authentication using Email
            user = authenticate(request, username=email_credential, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome, {user.first_name}!')
                return redirect('classroom:dashboard')
            else:
                if AuthorizedEmail.objects.filter(email=email_credential).exists():
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
        form = UserRegistrationForm(request.POST) 
        
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
            auth_entry = AuthorizedEmail.objects.get(email=email)
            user, created = User.objects.get_or_create(username=email, email=email)

            user.first_name = auth_entry.first_name
            user.last_name = auth_entry.last_name
            user.role = auth_entry.role

            if user.role == 'Student':
                user.department = auth_entry.department
                user.year = auth_entry.year
                user.division = auth_entry.division
            else:
                user.department = None
                user.year = None
                user.division = None
            
            user.set_password(password)
            user.save()

            status_msg = "Account created!" if created else "Password updated!"
            messages.success(request, f"{status_msg} You can now log in.")
            return redirect('classroom:login')

        except AuthorizedEmail.DoesNotExist:
            messages.error(request, "This email is not authorized.")
            return render(request, 'classroom/forgot_password.html', {'form': UserRegistrationForm(initial={'email': email})})

    else:
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
    
    today = date.today()
    now = datetime.now()
    
    # 1. SETUP DATA FOR DROPDOWNS
    student_subjects = Subject.objects.filter(
        department=request.user.department,
        year=request.user.year
    ).order_by('semester', 'name')

    # 2. SEARCH LOGIC (If user clicked "Search")
    search_results = None
    is_searching = False
    
    if request.GET.get('action') == 'search':
        is_searching = True
        search_date = request.GET.get('date', today.isoformat())
        search_subject = request.GET.get('subject')
        guest_only = request.GET.get('guest_only')
        
        # Start with all bookings for that date
        query = Booking.objects.filter(booking_date=search_date).select_related('classroom', 'faculty')
        
        if search_subject:
             try:
                 subj_obj = Subject.objects.get(id=search_subject)
                 query = query.filter(subject=subj_obj.name)
             except:
                 pass
        
        if guest_only:
            query = query.filter(is_guest_lecture=True)
            
        search_results = query

    # 3. MY SCHEDULE LOGIC (Timeline)
    # Fetch ALL relevant bookings for TODAY
    my_bookings = Booking.objects.filter(booking_date=today).order_by('slot')
    
    timeline = []
    for booking in my_bookings:
        # Filter relevance (Student's dept/year/div)
        is_relevant = False
        if booking.is_guest_lecture:
            if not booking.department or booking.department == request.user.department:
                is_relevant = True
        else:
            if (booking.department == request.user.department and 
                booking.year == request.user.year and
                (not booking.division or booking.division == request.user.division)):
                is_relevant = True
        
        if is_relevant:
            status = "Upcoming"
            can_feedback = False
            
            try:
                # Parse slot times (e.g., "8:00 - 9:30")
                start_str, end_str = booking.slot.split(' - ')
                start_time = datetime.strptime(start_str, "%H:%M").time()
                end_time = datetime.strptime(end_str, "%H:%M").time()
                
                current_time = now.time()
                
                if current_time < start_time:
                    status = "Upcoming"
                elif start_time <= current_time <= end_time:
                    status = "Live Now"
                    can_feedback = True
                else:
                    status = "Completed"
                    can_feedback = True
            except:
                status = "Scheduled"

            # Check if feedback already exists
            has_feedback = Feedback.objects.filter(booking=booking, student=request.user).exists()
            
            timeline.append({
                'obj': booking,
                'status': status,
                'can_feedback': can_feedback,
                'has_feedback': has_feedback
            })

    # Feedback Form for the Modal
    feedback_form = FeedbackForm()

    context = {
        'today': today,
        'student_subjects': student_subjects,
        'timeline': timeline,
        'search_results': search_results,
        'is_searching': is_searching,
        'feedback_form': feedback_form,
        'user': request.user,
        'config': SystemConfig.get_config(),
    }
    return render(request, 'classroom/student_dashboard.html', context)

@login_required
def faculty_dashboard(request):
    """
    Unified Faculty Dashboard: Shows Availability Grid + Booking Form + History
    """
    if request.user.role != 'Faculty':
        messages.error(request, 'Access denied')
        return redirect('classroom:dashboard')
    
    # 1. Date Selection
    selected_date_str = request.GET.get('date', date.today().isoformat())
    selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
    
    # 2. Availability Grid Logic
    classrooms = Classroom.objects.all()
    config = SystemConfig.get_config()
    
    availability_data = []
    for classroom in classrooms:
        classroom_data = {'classroom': classroom, 'slots': {}}
        for slot in config.class_slots:
            # Look for existing booking
            booking = Booking.objects.filter(
                classroom=classroom,
                booking_date=selected_date,
                slot=slot
            ).first()
            classroom_data['slots'][slot] = booking
        availability_data.append(classroom_data)

    # 3. "My Bookings" Side Panel
    my_bookings = Booking.objects.filter(faculty=request.user).order_by('-booking_date')[:5]
    for b in my_bookings:
        b.avg_rating = b.get_average_rating()
    
    # 4. Booking Form (for the Modal)
    booking_form = BookingForm(initial={'booking_date': selected_date})

    context = {
        'availability_data': availability_data,
        'config': config,
        'selected_date': selected_date_str,
        'my_bookings': my_bookings,
        'form': booking_form,
    }
    return render(request, 'classroom/faculty_dashboard.html', context)

@login_required
def admin_dashboard(request):
    """
    Secure Admin Dashboard with Analytics & Configuration
    """
    # 1. SECURITY CHECK
    if request.user.role != 'Admin' and not request.user.is_superuser:
        messages.error(request, 'Access denied. Administrator privileges required.')
        return redirect('classroom:dashboard')
    
    config = SystemConfig.get_config()

    # 2. HANDLE BRANDING UPDATES
    if request.method == 'POST' and 'update_branding' in request.POST:
        # Pass request.FILES for the logo upload and user for password check
        branding_form = SystemBrandingForm(request.POST, request.FILES, instance=config, user=request.user)
        
        if branding_form.is_valid():
            branding_form.save()
            messages.success(request, 'System branding updated successfully.')
            return redirect('classroom:admin_dashboard')
        else:
            messages.error(request, 'Update failed. Check your password or data.')
    else:
        # Initial form load
        branding_form = SystemBrandingForm(instance=config)
    
    # 3. ANALYTICS DATA
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
        'config': config,
        'branding_form': branding_form, # Pass the form to template
    }
    return render(request, 'classroom/admin_dashboard.html', context)

# -------------------------
# ACTION VIEWS
# -------------------------

@login_required
def create_booking(request):
    """
    Handles POST requests from the Faculty Dashboard Modal
    """
    if request.user.role != 'Faculty':
        messages.error(request, 'Only faculty can create bookings')
        return redirect('classroom:dashboard')
    
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.faculty = request.user
            
            if not booking.faculty_name:
                booking.faculty_name = f"{request.user.first_name} {request.user.last_name}"

            if booking.is_guest_lecture:
                if not booking.lecture_title or not booking.guest_speaker:
                    messages.error(request, "Guest lectures require a Title and Speaker.")
                    return redirect('classroom:faculty_dashboard')
                
                # Manual capture of guest fields
                booking.department = request.POST.get('guest_department')
                booking.year = request.POST.get('guest_year')
                booking.subject = None
                booking.division = None
                booking.semester = None

            else:
                subject_id = form.cleaned_data.get('subject')
                try:
                    if str(subject_id).isdigit():
                        booking.subject = Subject.objects.get(id=int(subject_id)).name
                    else:
                        booking.subject = subject_id
                except:
                    booking.subject = subject_id

            # Conflict Check
            if Booking.objects.filter(classroom=booking.classroom, booking_date=booking.booking_date, slot=booking.slot).exists():
                messages.error(request, 'Slot already booked!')
            else:
                booking.save()
                messages.success(request, 'Booking confirmed!')
                
            return redirect('classroom:faculty_dashboard')
        else:
            messages.error(request, 'Booking failed. Please check details.')
            return redirect('classroom:faculty_dashboard')
    
    return redirect('classroom:faculty_dashboard')

@login_required
def cancel_booking(request, booking_id):
    """
    Allows faculty to cancel their own bookings.
    Frees up the slot by deleting the record.
    """
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
    # This view is now redundant for faculty but kept for students/admin search
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