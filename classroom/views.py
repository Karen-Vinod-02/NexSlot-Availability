import os
import re
import json
import csv
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg, Count
from django.http import JsonResponse, FileResponse, Http404, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils import timezone
from datetime import date, datetime

# --- IMPORT MODELS & FORMS ---
from .models import User, Classroom, Booking, Feedback, SystemConfig, Subject, AuthorizedEmail, Document
from .forms import (
    UserRegistrationForm, UserLoginForm, ClassroomForm, BookingForm, 
    FeedbackForm, SystemBrandingForm, DocumentUploadForm, 
    get_allowed_divisions, get_allowed_semesters
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# AI CHATBOT & SCRAPING CONFIGURATION
# ---------------------------------------------------------

# 1. AI Libraries Check
try:
    from langchain_chroma import Chroma
    from langchain_ollama import OllamaLLM, OllamaEmbeddings
    from langchain_core.prompts import PromptTemplate
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_community.document_loaders import PyPDFLoader, TextLoader
    from langchain_core.documents import Document as LangChainDocument
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("⚠️ AI Libraries (LangChain/Chroma/Ollama) not found. Chatbot will be offline.")

# 2. Scraping Libraries Check
try:
    import requests
    from bs4 import BeautifulSoup
    import urllib3
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    SCRAPING_AVAILABLE = True
except ImportError:
    SCRAPING_AVAILABLE = False
    print("⚠️ Scraping Libraries (BeautifulSoup/Requests) not found. URL ingestion will be skipped.")

# Global Caches for AI
chat_sessions = {}  
llm_cache = {}
embedding_cache = None

def get_prompt_template(system_name="System"):
    """
    Returns a strict prompt template to reduce hallucinations.
    """
    return PromptTemplate(
        input_variables=["context", "question"],
        template=f"""You are the official AI assistant for {system_name}.

STRICT RULES:
1. Answer ONLY using the context provided below.
2. If the answer is NOT in the context, strictly say: "I cannot find this information in the official documents or website provided."
3. Do not make up information or use outside knowledge.
4. Be concise and professional.

Context:
{{context}}

Question: {{question}}

Answer:"""
    )

def get_embeddings():
    """Load embeddings once and cache globally to save RAM"""
    global embedding_cache
    if embedding_cache is None and AI_AVAILABLE:
        embedding_cache = OllamaEmbeddings(
            model="qwen2.5:1.5b",
            base_url="http://localhost:11434"
        )
    return embedding_cache

def load_system(portal_name):
    """Load LLM and retriever for a specific knowledge base (portal)"""
    if not AI_AVAILABLE:
        return None, None

    # Return cached if available
    if portal_name in llm_cache:
        return llm_cache[portal_name]
    
    embeddings = get_embeddings()
    base_dir = settings.BASE_DIR
    
    # Map "Portals" to specific ChromeDB folders
    db_map = {
        "General Chat": os.path.join(base_dir, "chroma_db_general"),
        "About VESIT": os.path.join(base_dir, "chroma_db_general"),
        "Semester 4": os.path.join(base_dir, "chroma_db_sem4"),
        "Semester 5": os.path.join(base_dir, "chroma_db_sem5")
    }
    
    db_path = db_map.get(portal_name, os.path.join(base_dir, "chroma_db_general"))
    
    # If DB doesn't exist yet, we can't retrieve
    if not os.path.exists(db_path):
         return None, None 

    vectorstore = Chroma(
        persist_directory=db_path,
        embedding_function=embeddings
    )
    
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3} 
    )
    
    llm = OllamaLLM(
        model="qwen2.5:1.5b",
        base_url="http://localhost:11434",
        temperature=0.1,
        num_predict=200,
        num_ctx=2048,
        top_k=20,
        top_p=0.95
    )
    
    llm_cache[portal_name] = (llm, retriever)
    return llm, retriever

def preprocess_question(question):
    """Expand abbreviations and normalize question"""
    replacements = {
        r'\bVESIT\b': 'Vivekanand Education Society Institute of Technology',
        r'\bSFIT\b': 'St. Francis Institute of Technology',
        r'\bIOT\b': 'Internet of Things',
        r'\bAI\b': 'Artificial Intelligence',
    }
    processed = question
    for pattern, replacement in replacements.items():
        processed = re.sub(pattern, replacement, processed, flags=re.IGNORECASE)
    return processed

def post_process_answer(answer):
    return answer.strip()

# --- INGESTION LOGIC (Files & URLs) ---

def _add_texts_to_chroma(texts, metadatas, db_folder="chroma_db_general"):
    """Helper to save chunks to ChromaDB"""
    if not AI_AVAILABLE or not texts: 
        return False
    
    try:
        db_path = os.path.join(settings.BASE_DIR, db_folder)
        embeddings = get_embeddings()
        vectorstore = Chroma(persist_directory=db_path, embedding_function=embeddings)
        vectorstore.add_texts(texts=texts, metadatas=metadatas)
        logger.info(f"✅ Successfully added {len(texts)} chunks to {db_folder}")
        return True
    except Exception as e:
        logger.error(f"❌ Chroma DB Error: {e}")
        return False

def clear_general_knowledge_base():
    """
    Clear the general knowledge base before ingesting new website content.
    """
    if not AI_AVAILABLE:
        return False
    
    try:
        db_path = os.path.join(settings.BASE_DIR, "chroma_db_general")
        
        # Delete the entire database directory
        if os.path.exists(db_path):
            import shutil
            shutil.rmtree(db_path)
            logger.info(f"🗑️ Cleared general knowledge base at {db_path}")
        
        # Clear cache
        if "General Chat" in llm_cache:
            del llm_cache["General Chat"]
        if "About VESIT" in llm_cache:
            del llm_cache["About VESIT"]
        
        return True
    except Exception as e:
        logger.error(f"❌ Error clearing knowledge base: {e}")
        return False

def ingest_website(url, clear_existing=True):
    """
    Heavy-duty scraper using Session, Retries, and Browser Masquerading.
    """
    if not AI_AVAILABLE:
        logger.warning("⚠️ Skipping scrape: AI libraries not available")
        return False
    
    if not SCRAPING_AVAILABLE:
        logger.warning("⚠️ Skipping scrape: Scraping libraries not available")
        return False

    try:
        if clear_existing:
            logger.info(f"🧹 Clearing existing general knowledge base...")
            clear_general_knowledge_base()
        
        logger.info(f"🕸️ Attempting to scrape: {url}...")

        session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        session.mount('https://', HTTPAdapter(max_retries=retries))
        session.mount('http://', HTTPAdapter(max_retries=retries))

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

        response = session.get(url, headers=headers, timeout=30, verify=False)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for element in soup(["script", "style", "nav", "footer", "header", "iframe", "noscript", "svg"]):
            element.decompose()
        
        main_content = soup.find('main') or soup.find('article') or soup.find('div', id='content') or soup.body
        if main_content:
            text_content = main_content.get_text(separator=' ', strip=True)
        else:
            text_content = soup.get_text(separator=' ', strip=True)
        
        text_content = re.sub(r'\s+', ' ', text_content).strip()
        
        if len(text_content) < 100:
            logger.warning(f"⚠️ Content too short ({len(text_content)} chars).")
            return False

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_text(text_content)
        
        metadatas = [{"source": url, "title": soup.title.string if soup.title else url, "type": "website"} for _ in chunks]
        
        success = _add_texts_to_chroma(chunks, metadatas, "chroma_db_general")
        
        if success:
            if "About VESIT" in llm_cache: del llm_cache["About VESIT"]
            if "General Chat" in llm_cache: del llm_cache["General Chat"]
            logger.info("✅ Scrape Successful!")
        
        return success

    except Exception as e:
        logger.error(f"❌ SCRAPE FAILED: {str(e)}")
        return False

def ingest_document(doc_instance):
    """Process uploaded PDF/TXT"""
    if not AI_AVAILABLE: 
        return False

    try:
        file_path = doc_instance.file.path
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.pdf': 
            loader = PyPDFLoader(file_path)
        elif ext == '.txt': 
            loader = TextLoader(file_path)
        else: 
            return False
            
        docs = loader.load()
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        chunks_docs = splitter.split_documents(docs)
        
        texts = [d.page_content for d in chunks_docs]
        metadatas = [{
            "source": doc_instance.file.name,
            "title": doc_instance.title,
            "department": doc_instance.department or "",
            "type": "document"
        } for _ in chunks_docs]
        
        target_db = "chroma_db_general"
        portal_key = "About VESIT"
        
        if doc_instance.semester == "Sem 4":
            target_db = "chroma_db_sem4"
            portal_key = "Semester 4"
        elif doc_instance.semester == "Sem 5":
            target_db = "chroma_db_sem5"
            portal_key = "Semester 5"
            
        success = _add_texts_to_chroma(texts, metadatas, target_db)
        
        if portal_key in llm_cache: 
            del llm_cache[portal_key]
        
        if success:
            logger.info(f"✅ Successfully ingested document: {doc_instance.title}")
            
        return success
    except Exception as e:
        logger.error(f"❌ Ingestion Error for {doc_instance.file.name}: {e}")
        return False

# -------------------------
# AUTHENTICATION VIEWS
# -------------------------

def user_login(request):
    if request.user.is_authenticated: 
        return redirect('classroom:dashboard')
    config = SystemConfig.get_config()
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(
                request, 
                username=form.cleaned_data.get('username'), 
                password=form.cleaned_data.get('password')
            )
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
    
    return render(request, 'classroom/login.html', {
        'form': form, 
        'config': config, 
        'branding': config
    })

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password1')
        confirm = request.POST.get('password2')

        if not email or not password:
            messages.error(request, "All fields are required.")
            return render(request, 'classroom/forgot_password.html', {
                'form': UserRegistrationForm()
            })
        
        if password != confirm:
            messages.error(request, "Passwords do not match.")
            return render(request, 'classroom/forgot_password.html', {
                'form': UserRegistrationForm(initial={'email': email})
            })

        try:
            auth_entry = AuthorizedEmail.objects.get(email=email)
            user, created = User.objects.get_or_create(username=email, email=email)
            user.first_name = auth_entry.first_name
            user.last_name = auth_entry.last_name
            user.role = auth_entry.role
            
            if user.role in ('Student', 'Employee'):
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
            return render(request, 'classroom/forgot_password.html', {
                'form': UserRegistrationForm(initial={'email': email})
            })
    
    return render(request, 'classroom/forgot_password.html', {
        'form': UserRegistrationForm()
    })

@login_required
def user_logout(request):
    logout(request)
    messages.info(request, 'Logged out.')
    return redirect('classroom:login')

@login_required
def dashboard(request):
    if request.user.is_superuser: 
        return redirect('classroom:admin_dashboard')
    if request.user.role in ('Student', 'Employee'):
        return redirect('classroom:student_dashboard')
    if request.user.role == 'Faculty': 
        return redirect('classroom:faculty_dashboard')
    if request.user.role == 'Admin': 
        return redirect('classroom:admin_dashboard')
    return redirect('classroom:login')

# -------------------------
# DASHBOARDS
# -------------------------

@login_required
def student_dashboard(request):
    """
    Handles Student/Employee Dashboard logic.
    Updated to handle both Academic (Dropdown ID) and Corporate (Text Search) filters correctly.
    """
    if request.user.role not in ('Student', 'Employee'):
        return redirect('classroom:dashboard')
    
    current_datetime = timezone.localtime() 
    today = current_datetime.date()
    config = SystemConfig.get_config()
    
    student_subjects = Subject.objects.filter(
        department=request.user.department, 
        year=request.user.year
    ).order_by('semester', 'name')
    
    search_results = None
    is_searching = request.GET.get('action') == 'search'
    
    if is_searching:
        search_date = request.GET.get('date', today.isoformat())
        query = Booking.objects.filter(
            booking_date=search_date
        ).select_related('classroom', 'faculty')
        
        # --- FIXED SEARCH LOGIC ---
        search_term = request.GET.get('subject') # 'subject' comes from the form input name
        
        if search_term:
            if config.org_type == 'Corporate':
                # Corporate: Text based search (Topic OR Organizer)
                # Using Q objects to search across multiple fields
                query = query.filter(
                    Q(subject__icontains=search_term) | 
                    Q(lecture_title__icontains=search_term) |
                    Q(faculty_name__icontains=search_term)
                )
            else:
                # College: Dropdown ID search (Standard Academic Flow)
                # Ensure input is a valid ID before querying
                if str(search_term).isdigit():
                    try: 
                        subject_name = Subject.objects.get(id=int(search_term)).name
                        query = query.filter(subject=subject_name)
                    except Subject.DoesNotExist:
                        pass # ID doesn't exist, return empty or filtered by date only
        # --------------------------
        
        if request.GET.get('guest_only'): 
            query = query.filter(is_guest_lecture=True)
        
        search_results = query

    my_bookings = Booking.objects.filter(booking_date=today).order_by('slot')
    timeline = []
    
    for booking in my_bookings:
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
                start_str, end_str = booking.slot.split(' - ')
                fmt = "%H:%M"
                start_time = datetime.strptime(start_str.strip(), fmt).time()
                end_time = datetime.strptime(end_str.strip(), fmt).time()
                
                if 1 <= start_time.hour <= 6: 
                    start_time = start_time.replace(hour=start_time.hour + 12)
                if 1 <= end_time.hour <= 6: 
                    end_time = end_time.replace(hour=end_time.hour + 12)
                
                now_time = current_datetime.time()
                if now_time < start_time: 
                    status = "Upcoming"
                elif start_time <= now_time <= end_time:
                    status = "Live Now"
                    can_feedback = True
                else:
                    status = "Completed"
                    can_feedback = True
            except:
                status = "Scheduled"

            timeline.append({
                'obj': booking, 
                'status': status, 
                'can_feedback': can_feedback, 
                'has_feedback': Feedback.objects.filter(
                    booking=booking, 
                    student=request.user
                ).exists()
            })

    context = {
        'today': today, 
        'student_subjects': student_subjects, 
        'timeline': timeline, 
        'search_results': search_results, 
        'is_searching': is_searching, 
        'feedback_form': FeedbackForm(), 
        'user': request.user, 
        'config': config 
    }
    return render(request, 'classroom/student_dashboard.html', context)

@login_required
def faculty_dashboard(request):
    if request.user.role != 'Faculty': 
        return redirect('classroom:dashboard')
    
    current_datetime = timezone.localtime()
    selected_date_str = request.GET.get('date', current_datetime.date().isoformat())
    selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
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
            
            if booking:
                booking.is_cancellable = False
                if booking.booking_date > current_datetime.date(): 
                    booking.is_cancellable = True
                elif booking.booking_date == current_datetime.date() and not booking.is_past_or_ongoing(): 
                    booking.is_cancellable = True
            
            classroom_data['slots'][slot] = booking
        availability_data.append(classroom_data)

    my_bookings = Booking.objects.filter(faculty=request.user).order_by('-booking_date')[:5]
    
    context = {
        'availability_data': availability_data, 
        'config': config, 
        'selected_date': selected_date_str, 
        'my_bookings': my_bookings, 
        'form': BookingForm(initial={'booking_date': selected_date}),
        'document_form': DocumentUploadForm()
    }
    return render(request, 'classroom/faculty_dashboard.html', context)

@login_required
def admin_dashboard(request):
    if request.user.role != 'Admin' and not request.user.is_superuser: 
        return redirect('classroom:dashboard')
    
    config = SystemConfig.get_config()
    
    # Dashboard Metrics
    all_bookings = Booking.objects.all()
    avg_rating = Feedback.objects.aggregate(Avg('rating'))['rating__avg'] or 0.0
    guest_feedback = Feedback.objects.filter(booking__is_guest_lecture=True)
    guest_avg = guest_feedback.aggregate(Avg('rating'))['rating__avg'] or 0.0
    
    most_booked = Booking.objects.values('classroom__room_number').annotate(
        total=Count('id')
    ).order_by('-total').first()
    
    most_booked_room = None
    if most_booked:
        total_all_bookings = all_bookings.count() or 1
        percentage = (most_booked['total'] / total_all_bookings) * 100
        most_booked_room = {
            'number': most_booked['classroom__room_number'],
            'count': most_booked['total'],
            'percent': round(percentage, 1)
        }

    slot_stats = Booking.objects.values('slot').annotate(
        count=Count('id')
    ).order_by('slot')
    slot_data = list(slot_stats)
    max_count = max([s['count'] for s in slot_data]) if slot_data else 1
    for s in slot_data: 
        s['percent'] = (s['count'] / max_count) * 100

    # Handle Settings Save
    if request.method == 'POST' and 'update_branding' in request.POST:
        branding_form = SystemBrandingForm(
            request.POST, 
            request.FILES, 
            instance=config, 
            user=request.user
        )
        
        if branding_form.is_valid():
            saved_config = branding_form.save()
            
            if saved_config.chatbot_source_url and SCRAPING_AVAILABLE:
                logger.info(f"🚀 Triggering web scrape for: {saved_config.chatbot_source_url}")
                scrape_success = ingest_website(saved_config.chatbot_source_url, clear_existing=True)
                
                if scrape_success:
                    messages.success(request, f"✅ Settings saved and website '{saved_config.chatbot_source_url}' successfully scraped!")
                else:
                    messages.warning(request, f"⚠️ Settings saved but failed to scrape. Check logs.")
            else:
                messages.success(request, '✅ System configuration updated.')
            
            return redirect('classroom:admin_dashboard')
        else: 
            messages.error(request, '❌ Update failed. Check password.')
    else: 
        branding_form = SystemBrandingForm(instance=config)
    
    context = {
        'classrooms': Classroom.objects.all(),
        'all_bookings': all_bookings,
        'config': config,
        'branding': config,
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
    if request.user.role != 'Faculty': 
        return redirect('classroom:dashboard')
    
    if request.method == 'POST':
        config = SystemConfig.get_config()
        data = request.POST.copy()
        
        if config.org_type == 'Corporate':
            data['semester'] = '1'
            data['division'] = 'A' 
        
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
                    booking.semester = None
                    booking.division = None
                    booking.subject = raw_subject # Text input directly
                else:
                    try:
                        if str(raw_subject).isdigit():
                            booking.subject = Subject.objects.get(id=int(raw_subject)).name
                        else:
                            booking.subject = raw_subject
                    except:
                        booking.subject = raw_subject

            if Booking.objects.filter(
                classroom=booking.classroom, 
                booking_date=booking.booking_date, 
                slot=booking.slot
            ).exists():
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
    if request.user.role != 'Faculty' or booking.faculty != request.user: 
        return redirect('classroom:dashboard')
    booking.delete()
    messages.success(request, 'Booking cancelled.')
    return redirect('classroom:faculty_dashboard')

@login_required
def submit_feedback(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.user.role not in ('Student', 'Employee'):
        return redirect('classroom:dashboard')
    
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.booking = booking
            feedback.student = request.user
            feedback.save()
            messages.success(request, 'Feedback submitted!')
            return redirect('classroom:student_dashboard')
    
    return render(request, 'classroom/submit_feedback.html', {
        'form': FeedbackForm(), 
        'booking': booking
    })

@login_required
def add_classroom(request):
    if request.method == 'POST':
        form = ClassroomForm(request.POST)
        if form.is_valid(): 
            form.save()
    return redirect('classroom:admin_dashboard')

@login_required
def delete_classroom(request, classroom_id):
    get_object_or_404(Classroom, id=classroom_id).delete()
    return redirect('classroom:admin_dashboard')

@login_required
def view_availability(request):
    selected_date = request.GET.get('date', date.today().isoformat())
    config = SystemConfig.get_config()
    
    availability_data = [
        {
            'classroom': c, 
            'slots': {
                s: Booking.objects.filter(
                    classroom=c, 
                    booking_date=selected_date, 
                    slot=s
                ).first() 
                for s in config.class_slots
            }
        } 
        for c in Classroom.objects.all()
    ]
    
    return render(request, 'classroom/view_availability.html', {
        'availability_data': availability_data, 
        'selected_date': selected_date, 
        'config': config
    })

@login_required
def upload_document(request):
    """Handle document uploads and trigger AI ingestion"""
    config = SystemConfig.get_config()
    if config.org_type == 'Corporate':
        can_upload = request.user.is_superuser or request.user.role in ('Admin', 'Employee')
    else:
        can_upload = request.user.role == 'Faculty'

    if not can_upload:
        return redirect('classroom:dashboard')
    
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.uploaded_by = request.user
            doc.save()
            
            # Trigger AI Ingestion
            if AI_AVAILABLE:
                success = ingest_document(doc)
                if success:
                    doc.processed = True
                    doc.save()
                    messages.success(request, f"✅ '{doc.title}' uploaded and indexed for AI Chat.")
                else:
                    messages.warning(request, f"⚠️ '{doc.title}' uploaded but AI indexing failed.")
            else:
                messages.info(request, f"'{doc.title}' uploaded. AI Indexing skipped (System Offline).")
            
            return redirect('classroom:dashboard')
    else:
        form = DocumentUploadForm()
    
    return render(request, 'classroom/upload_document.html', {'form': form, 'config': config})

@login_required
def delete_document(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id)
    config = SystemConfig.get_config()
    if config.org_type == 'Corporate':
        can_delete = (
            request.user.is_superuser
            or request.user.role == 'Admin'
            or (
                request.user.role == 'Employee'
                and doc.uploaded_by_id == request.user.id
            )
        )
    else:
        can_delete = request.user.role == 'Faculty'

    if not can_delete:
        return redirect('classroom:dashboard')
    
    doc.delete()
    messages.success(request, "Document deleted.")
    return redirect('classroom:dashboard')

# -------------------------
# REGISTRATION & UTILS
# -------------------------

def register(request):
    if request.user.is_authenticated:
        return redirect('classroom:dashboard')
        
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            try:
                auth_entry = AuthorizedEmail.objects.get(email=email)
                user = form.save(commit=False)
                user.username = email 
                user.role = auth_entry.role
                
                # Auto-fill details from AuthorizedEmail
                user.first_name = auth_entry.first_name
                user.last_name = auth_entry.last_name
                
                if user.role in ('Student', 'Employee'):
                    user.department = auth_entry.department
                    user.year = auth_entry.year
                    user.division = auth_entry.division
                
                user.save()
                messages.success(request, 'Account created! Please login.')
                return redirect('classroom:login')
                
            except AuthorizedEmail.DoesNotExist:
                messages.error(request, 'Email not authorized by Administrator.')
    else:
        form = UserRegistrationForm()
        
    return render(request, 'classroom/register.html', {'form': form})

def get_subjects(request):
    """AJAX endpoint for fetching subjects"""
    department = request.GET.get('department')
    year = request.GET.get('year')
    semester = request.GET.get('semester')
    
    subjects = Subject.objects.filter(department=department, year=year)
    if semester:
        subjects = subjects.filter(semester=semester)
        
    data = [{'id': s.id, 'name': s.name} for s in subjects]
    return JsonResponse(data, safe=False)

def api_get_divisions(request):
    """Return divisions based on year"""
    year = request.GET.get('year')
    divisions = get_allowed_divisions(year)
    return JsonResponse({'divisions': divisions})

def api_get_semesters(request):
    """Return semesters based on year"""
    year = request.GET.get('year')
    semesters = get_allowed_semesters(year)
    return JsonResponse({'semesters': semesters})

# -------------------------
# ANALYTICS & ADMIN TOOLS
# -------------------------

@login_required
def get_analytics_data(request):
    if request.user.role != 'Admin':
        raise Http404
        
    # Room Usage Data
    room_usage = Booking.objects.values('classroom__room_number').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Department Usage
    dept_usage = Booking.objects.values('department').annotate(
        count=Count('id')
    ).order_by('-count')

    data = {
        'rooms': {
            'labels': [x['classroom__room_number'] for x in room_usage],
            'data': [x['count'] for x in room_usage]
        },
        'departments': {
            'labels': [x['department'] for x in dept_usage if x['department']],
            'data': [x['count'] for x in dept_usage if x['department']]
        }
    }
    return JsonResponse(data)

@login_required
def export_analytics(request):
    if request.user.role != 'Admin':
        return redirect('classroom:dashboard')
        
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="analytics_{date.today()}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Date', 'Slot', 'Classroom', 'Faculty', 'Department', 'Subject', 'Is Guest', 'Rating'])
    
    bookings = Booking.objects.all().select_related('classroom', 'faculty')
    for b in bookings:
        feedback = Feedback.objects.filter(booking=b).aggregate(Avg('rating'))
        rating = feedback['rating__avg'] or 'N/A'
        
        writer.writerow([
            b.booking_date,
            b.slot,
            b.classroom.room_number,
            b.faculty_name,
            b.department,
            b.subject,
            'Yes' if b.is_guest_lecture else 'No',
            rating
        ])
        
    return response

@login_required
def manage_authorizations(request):
    if request.user.role != 'Admin':
        return redirect('classroom:dashboard')
    
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        if csv_file:
            decoded_file = csv_file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            count = 0
            for row in reader:
                AuthorizedEmail.objects.update_or_create(
                    email=row['email'],
                    defaults={
                        'role': row['role'],
                        'first_name': row.get('first_name', ''),
                        'last_name': row.get('last_name', ''),
                        'department': row.get('department'),
                        'year': row.get('year'),
                        'division': row.get('division')
                    }
                )
                count += 1
            messages.success(request, f'Successfully imported {count} users.')
    
    users = AuthorizedEmail.objects.all().order_by('role', 'email')
    return render(request, 'classroom/manage_auth.html', {'users': users})

# -------------------------
# AI CHATBOT VIEWS
# -------------------------

@login_required
def chat_view(request):
    """Renders the main chat interface"""
    config = SystemConfig.get_config()
    return render(request, 'classroom/chat.html', {
        'config': config, 
        'ai_active': AI_AVAILABLE
    })

@csrf_exempt
@login_required
def chat_api(request):
    """
    API Endpoint for the Chatbot.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)
    
    if not AI_AVAILABLE:
        return JsonResponse({"response": "System: AI services are currently offline. Please contact admin."}, status=503)

    try:
        data = json.loads(request.body)
        user_message = data.get("message", "").strip()
        portal = data.get("portal", "General Chat")
        
        if not user_message:
            return JsonResponse({"response": "Please enter a message."})

        # 1. Load specific Knowledge Base
        llm, retriever = load_system(portal)
        
        if not llm or not retriever:
            return JsonResponse({
                "response": f"System: Knowledge base for '{portal}' is not initialized or empty. Please upload documents/URLs first."
            })

        # 2. Preprocess
        processed_query = preprocess_question(user_message)
        
        # 3. Retrieve Documents
        docs = retriever.invoke(processed_query)
        
        if not docs:
            return JsonResponse({"response": "I couldn't find any relevant information in my database."})

        # 4. Construct Context
        context_text = "\n\n".join([d.page_content for d in docs])
        
        # 5. Generate Prompt
        template = get_prompt_template(portal)
        prompt_text = template.format(context=context_text, question=processed_query)
        
        # 6. LLM Inference
        raw_response = llm.invoke(prompt_text)
        final_response = post_process_answer(raw_response)
        
        return JsonResponse({"response": final_response})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Chat API Error: {str(e)}")
        return JsonResponse({"response": "An internal error occurred while processing your request."}, status=500)