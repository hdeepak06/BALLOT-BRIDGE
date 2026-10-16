from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from .models import UserProfile, UserRole, Election, Candidate, Announcement, ElectionStatus


class VoterRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Create a strong password (min. 8 characters)',
            'autocomplete': 'new-password'
        }),
        min_length=8,
        label="Password"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Re-enter your password to confirm',
            'autocomplete': 'new-password'
        }),
        label="Confirm Password"
    )
    role = forms.ChoiceField(
        choices=UserRole.choices,
        initial=UserRole.VOTER,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Account Role",
        help_text="Choose 'Voter' for standard participation, or 'Election Administrator' for admin privileges in this simulation."
    )
    demo_id_number = forms.CharField(
        max_length=64,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g. STU-2026-9042 or NAT-449102'
        }),
        label="Demo Identification Number",
        help_text="Simulated student/citizen ID for eligibility checks."
    )
    organization = forms.CharField(
        max_length=120,
        required=False,
        initial='Metropolitan University',
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g. Metropolitan University or National Civic Registry'
        }),
        label="Affiliated Organization"
    )
    department = forms.CharField(
        max_length=120,
        required=False,
        initial='College of Engineering & Sciences',
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g. Student Association, Faculty of Law, Public Affairs'
        }),
        label="Department / Constituency"
    )
    phone_number = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '+1 (555) 019-2834'
        }),
        label="Phone Number (Optional)"
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Unique username'}),
            'first_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'name@example.com'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already taken. Please choose another.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with this email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match. Please ensure both fields are identical.")

        return cleaned_data


class UserProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-input'}))
    last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-input'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-input'}))

    class Meta:
        model = UserProfile
        fields = ['demo_id_number', 'organization', 'department', 'phone_number']
        widgets = {
            'demo_id_number': forms.TextInput(attrs={'class': 'form-input'}),
            'organization': forms.TextInput(attrs={'class': 'form-input'}),
            'department': forms.TextInput(attrs={'class': 'form-input'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        user.email = self.cleaned_data.get('email', '')
        if commit:
            user.save()
            profile.save()
        return profile


class ElectionForm(forms.ModelForm):
    class Meta:
        model = Election
        fields = [
            'title', 'tagline', 'description', 'category', 'status',
            'start_time', 'end_time', 'eligibility_criteria',
            'banner_color', 'banner_icon', 'is_featured'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Election Title'}),
            'tagline': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Inspiring election summary tagline'}),
            'description': forms.Textarea(attrs={'class': 'form-input form-textarea', 'rows': 4, 'placeholder': 'Detailed background and instructions'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
            'eligibility_criteria': forms.Select(attrs={'class': 'form-select'}),
            'banner_color': forms.TextInput(attrs={'class': 'form-input', 'type': 'color'}),
            'banner_icon': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. vote, award, globe, building'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')
        if start and end and end <= start:
            self.add_error('end_time', "Election end time must be scheduled strictly after start time.")
        return cleaned_data


class CandidateForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = [
            'election', 'name', 'ballot_number', 'party_or_slate',
            'role_title', 'avatar_color', 'email', 'short_bio',
            'qualifications', 'manifesto', 'key_proposals'
        ]
        widgets = {
            'election': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Full Candidate Name'}),
            'ballot_number': forms.NumberInput(attrs={'class': 'form-input', 'min': 1}),
            'party_or_slate': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Party, Coalition, or Independent'}),
            'role_title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. President, Treasurer, Council Representative'}),
            'avatar_color': forms.TextInput(attrs={'class': 'form-input', 'type': 'color'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'candidate@ballotbridge.demo'}),
            'short_bio': forms.Textarea(attrs={'class': 'form-input form-textarea', 'rows': 3, 'placeholder': 'Concise candidate background summary...'}),
            'qualifications': forms.Textarea(attrs={'class': 'form-input form-textarea', 'rows': 4, 'placeholder': 'List qualifications and past leadership roles...'}),
            'manifesto': forms.Textarea(attrs={'class': 'form-input form-textarea', 'rows': 6, 'placeholder': 'Full campaign manifesto and vision statement...'}),
            'key_proposals': forms.Textarea(attrs={'class': 'form-input form-textarea', 'rows': 4, 'placeholder': 'Enter key policy initiatives, one per line...'}),
        }


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['election', 'title', 'message', 'is_pinned']
        widgets = {
            'election': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Announcement Title'}),
            'message': forms.Textarea(attrs={'class': 'form-input form-textarea', 'rows': 4, 'placeholder': 'Official bulletin message...'}),
            'is_pinned': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
