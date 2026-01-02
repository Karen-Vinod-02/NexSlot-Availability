import os
import re
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg, Count
from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils import timezone
from datetime import date, datetime
from .models import User, Classroom, Booking, Feedback, SystemConfig, Subject, AuthorizedEmail
from .forms import UserRegistrationForm, UserLoginForm, ClassroomForm, BookingForm, FeedbackForm, SystemBrandingForm, get_allowed_divisions, get_allowed_semesters

# ---------------------------------------------------------
# AI CHATBOT CONFIGURATION & GLOBALS
# ---------------------------------------------------------
try:
    from langchain_chroma import Chroma
    from langchain_ollama import OllamaLLM, OllamaEmbeddings
    from langchain_core.prompts import PromptTemplate
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("⚠️ AI Libraries (langchain-chroma, langchain-ollama) not found. Chatbot will be offline.")

# Global Caches
chat_sessions = {}  
llm_cache = {}
embedding_cache = None

PROMPT_TEMPLATE = PromptTemplate(
    input_variables=["context", "question"],
    template="""You are the official academic assistant for Vivekanand Education Society's Institute of Technology (VESIT).

IMPORTANT NOTES:
- VESIT is the abbreviation for "Vivekanand Education Society's Institute of Technology"
- Both names refer to the SAME institution
- VESIT is located in Mumbai, India
- Answer ONLY using the context provided below
- If information is not in the context, say "This information is not available in the official data."
- Be consistent with institution names

Context:
{context}

Question: {question}

Answer (brief, clear, and accurate):"""
)

def get_embeddings():
    """Load embeddings once and cache globally"""
    global embedding_cache
    if embedding_cache is None and AI_AVAILABLE:
        embedding_cache = OllamaEmbeddings(
            model="qwen2.5:1.5b",
            base_url="http://localhost:11434"
        )
    return embedding_cache

def load_system(portal_name):
    """Load LLM and retriever for a specific portal"""
    if not AI_AVAILABLE:
        return None, None

    if portal_name in llm_cache:
        return llm_cache[portal_name]
    
    embeddings = get_embeddings()
    
    # Map portal to database paths
    base_dir = settings.BASE_DIR
    db_map = {
        "General Chat": os.path.join(base_dir, "chroma_db_general"),
        "About VESIT": os.path.join(base_dir, "chroma_db_general"),
        "Semester 4": os.path.join(base_dir, "chroma_db_sem4"),
        "Semester 5": os.path.join(base_dir, "chroma_db_sem5")
    }
    
    db_path = db_map.get(portal_name)
    if not db_path or not os.path.exists(db_path):
        print(f"❌ DB Path not found or invalid: {db_path}")
        return None, None
    
    vectorstore = Chroma(
        persist_directory=db_path,
        embedding_function=embeddings
    )
    
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 2}
    )
    
    llm = OllamaLLM(
        model="qwen2.5:1.5b",
        base_url="http://localhost:11434",
        temperature=0.1,
        num_predict=120,
        num_ctx=2048,
        top_k=20,
        top_p=0.95,
        repeat_penalty=1.2
    )
    
    llm_cache[portal_name] = (llm, retriever)
    return llm, retriever

def preprocess_question(question):
    """Expand abbreviations and normalize question"""
    replacements = {
        r'\bVESIT\b': 'Vivekanand Education Society Institute of Technology VESIT',
        r'\bVES\b': 'Vivekanand Education Society',
        r'\bIOT\b': 'Internet of Things',
        r'\bAI\b': 'Artificial Intelligence',
        r'\bML\b': 'Machine Learning',
        r'\bDS\b': 'Data Science',
    }
    processed = question
    for pattern, replacement in replacements.items():
        processed = re.sub(pattern, replacement, processed, flags=re.IGNORECASE)
    return processed

def post_process_answer(answer):
    return answer.strip()

# -------------------------
# AUTHENTICATION
# -------------------------

def user_login(request):
    if request.user.is_authenticated: return redirect('classroom:dashboard')
    config = SystemConfig.get_config()
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(request, username=form.cleaned_data.get('username'), password=form.cleaned_data.get('password'))
            if user:
                login(request, user)
                messages.success(request, f'Welcome, {user.first_name}!')
                return redirect('classroom:dashboard')
            else:
                if AuthorizedEmail.objects.filter(email=form.cleaned_data.get('username')).exists():
                    messages.error(request, "Invalid credentials. Please activate your account if new.")
                else:
                    messages.error(request, 'Invalid email or password.')
    else:
        form = UserLoginForm()
    
    # Pass 'branding' context so base.html updates UI colors
    return render(request, 'classroom/login.html', {'form': form, 'config': config, 'branding': config})

def forgot_password(request):
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
                user.department = user.year = user.division = None
            
            user.set_password(password)
            user.save()
            messages.success(request, "Password updated! Please log in.")
            return redirect('classroom:login')
        except AuthorizedEmail.DoesNotExist:
            messages.error(request, "Email not authorized.")
            return render(request, 'classroom/forgot_password.html', {'form': UserRegistrationForm(initial={'email': email})})
    return render(request, 'classroom/forgot_password.html', {'form': UserRegistrationForm()})

@login_required
def user_logout(request):
    logout(request)
    messages.info(request, 'Logged out.')
    return redirect('classroom:login')

@login_required
def dashboard(request):
    if request.user.is_superuser: return redirect('classroom:admin_dashboard')
    if request.user.role == 'Student': return redirect('classroom:student_dashboard')
    if request.user.role == 'Faculty': return redirect('classroom:faculty_dashboard')
    if request.user.role == 'Admin': return redirect('classroom:admin_dashboard')
    return redirect('classroom:login')

# -------------------------
# DASHBOARDS
# -------------------------

@login_required
def student_dashboard(request):
    if request.user.role != 'Student': return redirect('classroom:dashboard')
    current_datetime = timezone.localtime() 
    today = current_datetime.date()
    config = SystemConfig.get_config()
    
    student_subjects = Subject.objects.filter(department=request.user.department, year=request.user.year).order_by('semester', 'name')
    search_results = None
    is_searching = request.GET.get('action') == 'search'
    
    if is_searching:
        search_date = request.GET.get('date', today.isoformat())
        query = Booking.objects.filter(booking_date=search_date).select_related('classroom', 'faculty')
        if request.GET.get('subject'):
             try: query = query.filter(subject=Subject.objects.get(id=request.GET.get('subject')).name)
             except: pass
        if request.GET.get('guest_only'): query = query.filter(is_guest_lecture=True)
        search_results = query

    my_bookings = Booking.objects.filter(booking_date=today).order_by('slot')
    timeline = []
    
    for booking in my_bookings:
        is_relevant = False
        if booking.is_guest_lecture:
            if not booking.department or booking.department == request.user.department: is_relevant = True
        else:
            if (booking.department == request.user.department and booking.year == request.user.year and (not booking.division or booking.division == request.user.division)): is_relevant = True
        
        if is_relevant:
            status = "Upcoming"
            can_feedback = False
            try:
                start_str, end_str = booking.slot.split(' - ')
                start_time = datetime.strptime(start_str, "%H:%M").time()
                end_time = datetime.strptime(end_str, "%H:%M").time()
                if 1 <= start_time.hour <= 6: start_time = start_time.replace(hour=start_time.hour + 12)
                if 1 <= end_time.hour <= 6: end_time = end_time.replace(hour=end_time.hour + 12)
                
                now_time = current_datetime.time()
                if now_time < start_time: status = "Upcoming"
                elif start_time <= now_time <= end_time:
                    status = "Live Now"
                    can_feedback = True
                else:
                    status = "Completed"
                    can_feedback = True
            except: status = "Scheduled"

            timeline.append({'obj': booking, 'status': status, 'can_feedback': can_feedback, 'has_feedback': Feedback.objects.filter(booking=booking, student=request.user).exists()})

    context = {
        'today': today, 
        'student_subjects': student_subjects, 
        'timeline': timeline, 
        'search_results': search_results, 
        'is_searching': is_searching, 
        'feedback_form': FeedbackForm(), 
        'user': request.user, 
        'config': config,
        'branding': config # Pass branding for UI updates
    }
    return render(request, 'classroom/student_dashboard.html', context)

@login_required
def faculty_dashboard(request):
    if request.user.role != 'Faculty': return redirect('classroom:dashboard')
    current_datetime = timezone.localtime()
    selected_date_str = request.GET.get('date', current_datetime.date().isoformat())
    selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
    classrooms = Classroom.objects.all()
    config = SystemConfig.get_config()
    
    availability_data = []
    for classroom in classrooms:
        classroom_data = {'classroom': classroom, 'slots': {}}
        for slot in config.class_slots:
            booking = Booking.objects.filter(classroom=classroom, booking_date=selected_date, slot=slot).first()
            if booking:
                booking.is_cancellable = False
                if booking.booking_date > current_datetime.date(): booking.is_cancellable = True
                elif booking.booking_date == current_datetime.date() and not booking.is_past_or_ongoing(): booking.is_cancellable = True
            classroom_data['slots'][slot] = booking
        availability_data.append(classroom_data)

    my_bookings = Booking.objects.filter(faculty=request.user).order_by('-booking_date')[:5]
    context = {
        'availability_data': availability_data, 
        'config': config, 
        'branding': config, # Pass branding for UI updates
        'selected_date': selected_date_str, 
        'my_bookings': my_bookings, 
        'form': BookingForm(initial={'booking_date': selected_date})
    }
    return render(request, 'classroom/faculty_dashboard.html', context)

@login_required
def admin_dashboard(request):
    if request.user.role != 'Admin' and not request.user.is_superuser: return redirect('classroom:dashboard')
    config = SystemConfig.get_config()
    
    # Stats for Visualization
    all_bookings = Booking.objects.all()
    avg_rating = Feedback.objects.aggregate(Avg('rating'))['rating__avg'] or 0.0
    guest_feedback = Feedback.objects.filter(booking__is_guest_lecture=True)
    guest_avg = guest_feedback.aggregate(Avg('rating'))['rating__avg'] or 0.0
    
    # Most Booked Room
    most_booked = Booking.objects.values('classroom__room_number').annotate(total=Count('id')).order_by('-total').first()
    
    most_booked_room = None
    if most_booked:
        total_all_bookings = all_bookings.count() or 1
        percentage = (most_booked['total'] / total_all_bookings) * 100
        most_booked_room = {
            'number': most_booked['classroom__room_number'],
            'count': most_booked['total'],
            'percent': round(percentage, 1)
        }

    # Peak Times
    slot_stats = Booking.objects.values('slot').annotate(count=Count('id')).order_by('slot')
    slot_data = list(slot_stats)
    max_count = max([s['count'] for s in slot_data]) if slot_data else 1
    for s in slot_data: s['percent'] = (s['count'] / max_count) * 100

    if request.method == 'POST' and 'update_branding' in request.POST:
        branding_form = SystemBrandingForm(request.POST, request.FILES, instance=config, user=request.user)
        if branding_form.is_valid():
            branding_form.save()
            messages.success(request, 'System branding updated.')
            return redirect('classroom:admin_dashboard')
        else: messages.error(request, 'Update failed. Check password.')
    else: branding_form = SystemBrandingForm(instance=config)
    
    context = {
        'classrooms': Classroom.objects.all(),
        'all_bookings': all_bookings,
        'config': config,
        'branding': config, # Pass branding for UI updates
        'branding_form': branding_form,
        'avg_rating': avg_rating,
        'guest_avg': guest_avg,
        'total_feedback': Feedback.objects.count(),
        'guest_feedback_count': guest_feedback.count(),
        'most_booked_room': most_booked_room,
        'slot_data': slot_data
    }
    return render(request, 'classroom/admin_dashboard.html', context)

# -------------------------
# ACTIONS
# -------------------------

@login_required
def create_booking(request):
    if request.user.role != 'Faculty': return redirect('classroom:dashboard')
    if request.method == 'POST':
        config = SystemConfig.get_config()
        
        # --- FIX: Handle Corporate Mode Hidden Fields ---
        # When in Corporate mode, Semester/Division are hidden in HTML.
        # We inject dummy values into a copy of request.POST to pass validation.
        data = request.POST.copy()
        if config.org_type == 'Corporate':
            data['semester'] = '1'  # Dummy value
            data['division'] = 'A'  # Dummy value
        
        form = BookingForm(data)
        
        if form.is_valid():
            booking = form.save(commit=False)
            booking.faculty = request.user
            booking.faculty_name = f"{request.user.first_name} {request.user.last_name}"

            if booking.is_guest_lecture:
                booking.department = request.POST.get('guest_department')
                booking.year = request.POST.get('guest_year')
                booking.subject = booking.division = booking.semester = None
            else:
                raw_subject = form.cleaned_data.get('subject')
                if config.org_type == 'Corporate':
                    # Clean up the dummy values
                    booking.semester = None
                    booking.division = None
                    booking.subject = raw_subject
                else:
                    try:
                        if str(raw_subject).isdigit():
                            booking.subject = Subject.objects.get(id=int(raw_subject)).name
                        else:
                            booking.subject = raw_subject
                    except:
                        booking.subject = raw_subject

            if Booking.objects.filter(classroom=booking.classroom, booking_date=booking.booking_date, slot=booking.slot).exists():
                messages.error(request, 'Slot already booked!')
            else:
                booking.save()
                messages.success(request, 'Booking confirmed!')
            return redirect('classroom:faculty_dashboard')
        else:
            messages.error(request, f'Booking failed: {form.errors}')
            return redirect('classroom:faculty_dashboard')
    return redirect('classroom:faculty_dashboard')

@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.user.role != 'Faculty' or booking.faculty != request.user: return redirect('classroom:dashboard')
    booking.delete()
    messages.success(request, 'Booking cancelled.')
    return redirect('classroom:faculty_dashboard')

@login_required
def submit_feedback(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.user.role != 'Student': return redirect('classroom:dashboard')
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.booking = booking
            feedback.student = request.user
            feedback.save()
            messages.success(request, 'Feedback submitted!')
            return redirect('classroom:student_dashboard')
    return render(request, 'classroom/submit_feedback.html', {'form': FeedbackForm(), 'booking': booking})

@login_required
def add_classroom(request):
    if request.method == 'POST':
        form = ClassroomForm(request.POST)
        if form.is_valid(): form.save()
    return redirect('classroom:admin_dashboard')

@login_required
def delete_classroom(request, classroom_id):
    get_object_or_404(Classroom, id=classroom_id).delete()
    return redirect('classroom:admin_dashboard')

@login_required
def view_availability(request):
    selected_date = request.GET.get('date', date.today().isoformat())
    config = SystemConfig.get_config()
    availability_data = [{'classroom': c, 'slots': {s: Booking.objects.filter(classroom=c, booking_date=selected_date, slot=s).first() for s in config.class_slots}} for c in Classroom.objects.all()]
    return render(request, 'classroom/view_availability.html', {'availability_data': availability_data, 'selected_date': selected_date, 'config': config, 'branding': config})

# -------------------------
# AJAX
# -------------------------

def load_subjects(request):
    department = request.GET.get('department')
    year = request.GET.get('year')
    semester = request.GET.get('semester')
    subjects = Subject.objects.none()
    if department and year:
        qs = Subject.objects.filter(department=department, year=year)
        if semester: qs = qs.filter(semester=semester)
        subjects = qs.order_by('name')
    return JsonResponse(list(subjects.values('id', 'name')), safe=False)

def load_semesters(request):
    year = request.GET.get('year')
    semesters = get_allowed_semesters(year)
    return JsonResponse([{'id': s, 'name': s} for s in semesters], safe=False)

def load_divisions(request):
    department = request.GET.get('department')
    divisions = get_allowed_divisions(department)
    return JsonResponse([{'id': d, 'name': d} for d in divisions], safe=False)

# -------------------------
# AI CHATBOT VIEWS (REPLACING FLASK)
# -------------------------

@csrf_exempt
def chat_api(request):
    """
    Handle chat requests directly within Django.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    if not AI_AVAILABLE:
        return JsonResponse({'answer': 'AI System is offline (Libraries missing).', 'sources': []})

    try:
        data = json.loads(request.body)
        question = data.get('question', '')
        portal_name = data.get('portal', 'About VESIT')
        session_id = data.get('session_id', 'default')
        
        if not question:
            return JsonResponse({'error': 'No question provided'}, status=400)

        # Preprocessing
        question_processed = preprocess_question(question)
        
        # Load System
        llm, retriever = load_system(portal_name)
        if not llm:
            return JsonResponse({'answer': f'Database for {portal_name} not found on server.', 'sources': []})

        # Retrieve
        docs = retriever.invoke(question_processed)
        sources = []
        
        if not docs:
            answer = "This information is not available in the official data."
        else:
            context_text = "\n\n".join([doc.page_content for doc in docs[:2]])
            
            # Extract sources
            for doc in docs[:2]:
                src = doc.metadata.get("source")
                if src and src not in sources:
                    sources.append(src)
            
            # Generate Answer
            answer = llm.invoke(PROMPT_TEMPLATE.format(context=context_text, question=question))
            answer = post_process_answer(answer)
            
            # Check for "no info" responses
            no_info_phrases = ["not available", "no information", "cannot find"]
            if any(x in answer.lower() for x in no_info_phrases):
                sources = []

        # Store History (In-memory for now, could be DB model)
        session_key = f"{session_id}_{portal_name}"
        if session_key not in chat_sessions:
            chat_sessions[session_key] = []
        
        chat_sessions[session_key].append({
            'question': question,
            'answer': answer,
            'sources': sources
        })

        return JsonResponse({'answer': answer, 'sources': sources})

    except Exception as e:
        print(f"AI Error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def chat_history(request):
    """Get chat history"""
    session_id = request.GET.get('session_id', 'default')
    portal_name = request.GET.get('portal', 'About VESIT')
    session_key = f"{session_id}_{portal_name}"
    return JsonResponse({'history': chat_sessions.get(session_key, [])})

@csrf_exempt
@login_required
def clear_history(request):
    """Clear chat history"""
    if request.method == 'POST':
        data = json.loads(request.body)
        session_id = data.get('session_id', 'default')
        portal_name = data.get('portal', 'About VESIT')
        session_key = f"{session_id}_{portal_name}"
        if session_key in chat_sessions:
            chat_sessions[session_key] = []
        return JsonResponse({'status': 'success'})
    return JsonResponse({'error': 'Invalid method'}, status=405)

def download_pdf(request, filename):
    """Serve PDF files securely"""
    file_path = os.path.join(settings.BASE_DIR, 'data', filename)
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=filename)
    raise Http404("File not found")

@login_required
def upload_document(request):
    """Handle document uploads for RAG"""
    if request.method == 'POST' and request.FILES.get('document'):
        f = request.FILES['document']
        # Ensure 'data' directory exists
        path = os.path.join(settings.BASE_DIR, 'data')
        os.makedirs(path, exist_ok=True)
        
        # Save file
        with open(os.path.join(path, f.name), 'wb+') as dest:
            for chunk in f.chunks(): dest.write(chunk)
            
        messages.success(request, f"Uploaded {f.name}. The AI will index it shortly.")
    return redirect('classroom:faculty_dashboard')