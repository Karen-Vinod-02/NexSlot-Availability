from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Classroom, Booking, Feedback, SystemConfig, AuthorizedEmail, Document

# --- COLLEGE CONSTANTS ---
DEPT_CHOICES = [
    ('Computer Engineering', 'Computer Engineering'),
    ('Electronics & Telecom (EXTC)', 'Electronics & Telecom (EXTC)'),
    ('Mechanical Engineering', 'Mechanical Engineering'),
    ('Civil Engineering', 'Civil Engineering'),
    ('Chemical Engineering', 'Chemical Engineering'),
]

YEAR_CHOICES = [('FE', 'First Year'), ('SE', 'Second Year'), ('TE', 'Third Year'), ('BE', 'Final Year')]
SEM_CHOICES = [(f'Sem {i}', f'Sem {i}') for i in range(1, 9)]
DIV_CHOICES = [('A', 'A'), ('B', 'B'), ('C', 'C')]

# --- CORPORATE CONSTANTS ---
CORP_DEPT_CHOICES = [
    ('Engineering', 'Engineering'), ('Marketing', 'Marketing'),
    ('Sales', 'Sales'), ('HR', 'HR'), ('Finance', 'Finance'),
]
CORP_LEVEL_CHOICES = [('Junior', 'Junior'), ('Mid-Level', 'Mid-Level'), ('Senior', 'Senior'), ('Executive', 'Executive')]

# --- HELPERS ---
def get_allowed_divisions(department):
    if department == 'Computer Engineering': return ['A', 'B', 'C']
    elif department in ['Electronics & Telecom (EXTC)', 'Mechanical Engineering']: return ['A', 'B']
    return []

def get_allowed_semesters(year):
    if year == 'FE': return ['Sem 1', 'Sem 2']
    if year == 'SE': return ['Sem 3', 'Sem 4']
    if year == 'TE': return ['Sem 5', 'Sem 6']
    if year == 'BE': return ['Sem 7', 'Sem 8']
    return []

class UserRegistrationForm(UserCreationForm):
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
            raise forms.ValidationError("Email already registered.")
        if not AuthorizedEmail.objects.filter(email=email).exists():
            raise forms.ValidationError("Email not authorized.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        email = self.cleaned_data['email']
        auth_entry = AuthorizedEmail.objects.get(email=email)
        user.username = email 
        user.email = email
        user.role = auth_entry.role
        user.first_name = auth_entry.first_name
        user.last_name = auth_entry.last_name
        
        if auth_entry.role in ('Student', 'Employee'):
            user.department = auth_entry.department
            user.year = auth_entry.year
            user.division = auth_entry.division
        
        if commit: user.save()
        return user

class UserLoginForm(AuthenticationForm):
    username = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}), label="Email")
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

    def clean_username(self):
        email = self.cleaned_data.get('username')
        config = SystemConfig.get_config()
        if email and config.org_type == 'College':
            if not (email.endswith('.ac.in') or email.endswith('.edu')):
                raise forms.ValidationError("Use institutional email (.ac.in/.edu).")
        return email

class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}), label="Email Address")

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
    department = forms.ChoiceField(choices=[('', '---------')], required=False, widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_department'}))
    year = forms.ChoiceField(choices=[('', '---------')], required=False, widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_year'}))
    semester = forms.ChoiceField(choices=[('', '---------')], required=False, widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_semester'}))
    division = forms.ChoiceField(choices=[('', '---------')], required=False, widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_division'}))
    
    # Placeholder; actual widget logic is in __init__
    subject = forms.CharField(required=False, widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_subject'})) 

    class Meta:
        model = Booking
        fields = ['classroom', 'booking_date', 'slot', 'subject', 'is_guest_lecture', 'lecture_title', 'guest_speaker', 'department', 'year', 'division', 'semester']
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
        self.config = SystemConfig.get_config()
        self.fields['slot'].widget.choices = [(s, s) for s in self.config.class_slots]

        if self.config.org_type == 'Corporate':
            # --- CORPORATE CONFIGURATION ---
            self.fields['department'].choices = [('', '---------')] + CORP_DEPT_CHOICES
            self.fields['year'].choices = [('', '---------')] + CORP_LEVEL_CHOICES
            self.fields['year'].label = "Level"
            
            # Disable academic fields so they don't block validation visually
            self.fields['semester'].widget.attrs['disabled'] = True
            self.fields['division'].widget.attrs['disabled'] = True
            
            # Change Subject to simple Text Input for Meeting Names
            self.fields['subject'].widget = forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Meeting Topic / Organizer'})
            self.fields['subject'].label = "Topic / Organizer"
        else:
            # --- COLLEGE CONFIGURATION ---
            self.fields['department'].choices = [('', '---------')] + DEPT_CHOICES
            self.fields['year'].choices = [('', '---------')] + YEAR_CHOICES
            self.fields['semester'].choices = [('', '---------')] + SEM_CHOICES
            self.fields['division'].choices = [('', '---------')] + DIV_CHOICES
            
            # Keep Subject as Select (AJAX populated)
            self.fields['subject'].widget = forms.Select(attrs={'class': 'form-select', 'id': 'id_subject'})
            self.fields['subject'].widget.choices = []

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('is_guest_lecture'):
            if not cleaned_data.get('lecture_title'): self.add_error('lecture_title', "Title is required.")
            if not cleaned_data.get('guest_speaker'): self.add_error('guest_speaker', "Speaker is required.")
        else:
            if not cleaned_data.get('subject'): self.add_error('subject', "Subject/Topic is required.")
            
            # Academic Validation only for Colleges
            if self.config.org_type == 'College':
                allowed_sems = get_allowed_semesters(cleaned_data.get('year'))
                if cleaned_data.get('semester') not in allowed_sems:
                    # We skip this error if semester is None (handled in views for corporate)
                    if cleaned_data.get('semester'):
                        self.add_error('semester', f"Invalid semester for {cleaned_data.get('year')}")
            else:
                # Corporate cleanup
                cleaned_data['semester'] = None
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

class SystemBrandingForm(forms.ModelForm):
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label="Admin Password", required=True)
    
    class Meta:
        model = SystemConfig
        fields = [
            'site_name', 'site_logo', 'org_type', 'primary_color', 'accent_color', 
            'secondary_color', 'navbar_color', 'sidebar_color',
            # New Chatbot Fields
            'chatbot_enabled', 'chatbot_source_url', 'chatbot_greeting'
        ]
        widgets = {
            'site_name': forms.TextInput(attrs={'class': 'form-control'}),
            'org_type': forms.Select(attrs={'class': 'form-select'}),
            'primary_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control'}),
            'accent_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control'}),
            'secondary_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control'}),
            'navbar_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control'}),
            'sidebar_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control'}),
            'site_logo': forms.FileInput(attrs={'class': 'form-control'}),
            
            # Chatbot Widgets
            'chatbot_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
            'chatbot_source_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://university.edu/handbook'}),
            'chatbot_greeting': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Hello! How can I help you today?'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Ensure optional fields don't block validation
        optional_fields = ['site_name', 'primary_color', 'site_logo', 'chatbot_source_url', 'chatbot_greeting']
        for f in optional_fields: 
            if f in self.fields:
                self.fields[f].required = False

    def clean_confirm_password(self):
        password = self.cleaned_data.get('confirm_password')
        if not self.user or not self.user.check_password(password):
            raise forms.ValidationError("Incorrect password.")
        return password

class DocumentUploadForm(forms.ModelForm):
    department = forms.ChoiceField(choices=[('', 'General / All')] + DEPT_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    year = forms.ChoiceField(choices=[('', 'General / All')] + YEAR_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    semester = forms.ChoiceField(choices=[('', 'General / All')] + SEM_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = Document
        fields = ['file', 'title', 'department', 'year', 'semester']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.txt'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Syllabus 2026'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config = SystemConfig.get_config()
        if config.org_type == 'Corporate':
            self.fields['department'].choices = [('', 'General / All')] + CORP_DEPT_CHOICES
            self.fields['year'].choices = [('', 'General / All')] + CORP_LEVEL_CHOICES
            self.fields['year'].label = "Level"
            self.fields['semester'].widget = forms.HiddenInput() # Hide semester for corporate