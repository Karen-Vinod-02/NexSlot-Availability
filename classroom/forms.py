from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Classroom, Booking, Feedback, SystemConfig, AuthorizedEmail

# --- CONSTANTS & LOGIC ---
DEPT_CHOICES = [
    ('Computer Engineering', 'Computer Engineering'),
    ('Electronics & Telecom (EXTC)', 'Electronics & Telecom (EXTC)'),
    ('Mechanical Engineering', 'Mechanical Engineering'),
    ('Civil Engineering', 'Civil Engineering'),
    ('Chemical Engineering', 'Chemical Engineering'),
]

YEAR_CHOICES = [
    ('FE', 'First Year (FE)'),
    ('SE', 'Second Year (SE)'),
    ('TE', 'Third Year (TE)'),
    ('BE', 'Final Year (BE)'),
]

SEM_CHOICES = [
    ('Sem 1', 'Sem 1'), ('Sem 2', 'Sem 2'),
    ('Sem 3', 'Sem 3'), ('Sem 4', 'Sem 4'),
    ('Sem 5', 'Sem 5'), ('Sem 6', 'Sem 6'),
    ('Sem 7', 'Sem 7'), ('Sem 8', 'Sem 8'),
]

DIV_CHOICES = [
    ('A', 'A'),
    ('B', 'B'),
    ('C', 'C'),
]

def get_allowed_divisions(department):
    """Return allowed divisions based on department rules."""
    if department == 'Computer Engineering':
        return ['A', 'B', 'C']
    elif department in ['Electronics & Telecom (EXTC)', 'Mechanical Engineering']:
        return ['A', 'B']
    elif department in ['Civil Engineering', 'Chemical Engineering']:
        return [] # No division option
    return []

def get_allowed_semesters(year):
    """Return allowed semesters based on year."""
    if year == 'FE': return ['Sem 1', 'Sem 2']
    if year == 'SE': return ['Sem 3', 'Sem 4']
    if year == 'TE': return ['Sem 5', 'Sem 6']
    if year == 'BE': return ['Sem 7', 'Sem 8']
    return []

class UserRegistrationForm(UserCreationForm):
    # Only ask for Email. Everything else is fetched from DB.
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ['email', 'password1', 'password2'] 
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        
        if not AuthorizedEmail.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is not authorized for registration. Contact Admin.")
        
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        email = self.cleaned_data['email']
        
        # Fetch details from Verification DB
        auth_entry = AuthorizedEmail.objects.get(email=email)
        
        user.username = email 
        user.email = email
        user.role = auth_entry.role
        user.first_name = auth_entry.first_name
        user.last_name = auth_entry.last_name
        
        # Decouple Faculty logic
        if auth_entry.role == 'Student':
            user.department = auth_entry.department
            user.year = auth_entry.year
            user.division = auth_entry.division
        else:
            user.department = None
            user.year = None
            user.division = None
        
        if commit:
            user.save()
        return user

class UserLoginForm(AuthenticationForm):
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Institutional Email'}),
        label="Email Address"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )

    def clean_username(self):
        email = self.cleaned_data.get('username')
        if email:
            if not (email.endswith('.ac.in') or email.endswith('.edu')):
                raise forms.ValidationError("Only .ac.in or .edu email addresses are allowed.")
        return email

class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your registered email'}),
        label="Email Address"
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not (email.endswith('.ac.in') or email.endswith('.edu')):
            raise forms.ValidationError("Invalid domain. Use your institutional email.")
        return email

class ClassroomForm(forms.ModelForm):
    class Meta:
        model = Classroom
        fields = ['room_number', 'capacity', 'has_smartboard']
        widgets = {
            'room_number': forms.TextInput(attrs={'class': 'form-control'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control'}),
            'has_smartboard': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class BookingForm(forms.ModelForm):
    department = forms.ChoiceField(choices=[('', '---------')] + DEPT_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_department'}))
    year = forms.ChoiceField(choices=[('', '---------')] + YEAR_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_year'}))
    semester = forms.ChoiceField(choices=[('', '---------')] + SEM_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_semester'}))
    division = forms.ChoiceField(choices=[('', '---------')] + DIV_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_division'}))
    
    # Subject is populated via AJAX
    subject = forms.CharField(required=False, widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_subject'})) 

    class Meta:
        model = Booking
        # --- FIXED: REMOVED 'faculty_name' FROM THIS LIST ---
        # The view (views.py) handles setting the faculty name automatically.
        fields = ['classroom', 'booking_date', 'slot', 'subject',
                  'is_guest_lecture', 'lecture_title', 'guest_speaker', 
                  'department', 'year', 'division', 'semester']
        widgets = {
            'classroom': forms.Select(attrs={'class': 'form-select'}),
            'booking_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'slot': forms.Select(attrs={'class': 'form-select'}),
            'is_guest_lecture': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_is_guest_lecture'}),
            'lecture_title': forms.TextInput(attrs={'class': 'form-control'}),
            'guest_speaker': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config = SystemConfig.get_config()
        self.fields['slot'].widget.choices = [(s, s) for s in config.class_slots]
        self.fields['subject'].widget.choices = []

    def clean(self):
        cleaned_data = super().clean()
        is_guest = cleaned_data.get('is_guest_lecture')
        department = cleaned_data.get('department')
        year = cleaned_data.get('year')
        semester = cleaned_data.get('semester')
        division = cleaned_data.get('division')

        if is_guest:
            if not cleaned_data.get('lecture_title'):
                self.add_error('lecture_title', "Lecture Title is required for Guest Lectures.")
            if not cleaned_data.get('guest_speaker'):
                self.add_error('guest_speaker', "Speaker Name is required for Guest Lectures.")
        else:
            if not cleaned_data.get('subject'):
                 self.add_error('subject', "Subject is required for regular lectures.")

            # Validate Semester matches Year
            allowed_sems = get_allowed_semesters(year)
            if semester not in allowed_sems:
                self.add_error('semester', f"Invalid semester for {year}. Allowed: {', '.join(allowed_sems)}")

            # Validate Division matches Department
            allowed_divs = get_allowed_divisions(department)
            if allowed_divs:
                if not division:
                    self.add_error('division', "Division is required for this department.")
                elif division not in allowed_divs:
                    self.add_error('division', f"Invalid division. Allowed: {', '.join(allowed_divs)}")
            else:
                cleaned_data['division'] = None

        return cleaned_data

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['rating', 'comments']
        widgets = {
            'rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
            'comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }