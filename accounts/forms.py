# accounts/forms.py
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Event

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
        fields = ("username", "email")
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Type your email or username'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Type your email or username'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email

    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")
        if password1:
            # This will run the validators from settings.AUTH_PASSWORD_VALIDATORS
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
        user.set_password(self.cleaned_data["password1"])
        # Option: require email verification before login (set False)
        # user.is_active = False
        user.is_active = True
        if commit:
            user.save()
        return user
