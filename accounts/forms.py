# accounts/forms.py
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import re
from .models import Event
from .models import Profile

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'input-field', 'placeholder': 'Email'}),
        }

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_picture']

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'event_name', 'event_description', 'event_category',
            'event_venue', 'event_date', 'event_time_in',
            'event_time_out', 'ticket_price'
        ]
        widgets = {
            'event_date': forms.DateInput(attrs={'type': 'date'}),
            'event_time_in': forms.TimeInput(attrs={'type': 'time'}),
            'event_time_out': forms.TimeInput(attrs={'type': 'time'}),
        }


class RegistrationForm(forms.ModelForm):
    gmail = forms.EmailField(
        label="Gmail Account",
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your Gmail account'})
    )

    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={'placeholder': 'Type your password'}),
        help_text="Use a strong password (Django validators apply)."
    )
    password2 = forms.CharField(
        label="Confirm Password",
        strip=False,
        widget=forms.PasswordInput(attrs={'placeholder': 'Type your password again'}),
    )

    class Meta:
        model = User
        fields = ("username", "gmail")
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Type your email or username'}),
        }

    # --- Custom Gmail Validation ---
    def clean_gmail(self):
        gmail = self.cleaned_data.get("gmail", "").strip().lower()

        # Must be a valid Google email
        if not re.match(r"^[a-zA-Z0-9._%+-]+@gmail\.com$", gmail):
            raise ValidationError("Please enter a valid Gmail address (must end with @gmail.com).")

        # Prevent duplicate Gmail accounts
        if User.objects.filter(email__iexact=gmail).exists():
            raise ValidationError("An account with this Gmail already exists.")

        return gmail

    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")
        if password1:
            validate_password(password1, user=None)
        return password1

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Passwords do not match.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["gmail"]
        user.set_password(self.cleaned_data["password1"])
        user.is_active = True
        if commit:
            user.save()
        return user
