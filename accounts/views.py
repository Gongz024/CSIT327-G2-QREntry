# accounts/views.py
from asyncio import events
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login,logout
from django.contrib import messages
from .models import Event
from .forms import EventForm
from django.contrib.auth.decorators import login_required

from django.contrib import messages

from django.contrib import messages
from django.shortcuts import render, redirect
from .models import Event

def create_event_view(request):
    if request.method == 'POST':
        event_name = request.POST['event_name']
        venue = request.POST['venue']
        category = request.POST['category']
        start_time = request.POST['start_time']
        end_time = request.POST['end_time']
        description = request.POST['description']

        Event.objects.create(
            event_name=event_name,
            venue=venue,
            category=category,
            start_time=start_time,
            end_time=end_time,
            description=description,
            organizer=request.user
        )

        messages.success(request, '✅ Event successfully created!')
        return redirect('accounts:organizer')

    return render(request, 'accounts/create_event.html')


def view_events_view(request):
    events = Event.objects.all()
    return render(request, 'accounts/event.html', {'events': events})

@login_required
def organizer_view(request):
    event_created = request.GET.get('created') == 'true'
    return render(request, "accounts/organizer.html", {"event_created": event_created})



def home_view(request):
    category = request.GET.get('category')
    if category:
        events = Event.objects.filter(event_category=category)
    else:
        events = Event.objects.all()
    return render(request, 'accounts/home.html', {'events': events})



def register_view(request):
    """
    Register using Django's UserCreationForm.
    """
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Registration successful! Welcome to Event CIT, {user.username}!")
            return redirect("accounts:home")  # send them to the dashboard after signup
            messages.success(request, f"Registration successful! Welcome, {user.username}!")
            return redirect("accounts:login")  # after register, go to login
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserCreationForm()

    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    """
    Login view with error messages + session handling.
    """
    if request.user.is_authenticated:
        return redirect("accounts:home")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Organizer check
            if user.username == "organizer" and request.POST.get("password") == "organizer_Strong_Password!123":
                # Optional: set session expiry for organizer
                request.session.set_expiry(0)
                return redirect("accounts:organizer")  # make sure you create a URL name for organizer.html

            # Normal user session handling
            if request.POST.get("remember_me"):
                request.session.set_expiry(1209600)  # 2 weeks
            else:
                request.session.set_expiry(0)  # until browser close

            messages.success(request, f"Welcome back, {user.username}!")
            return redirect("accounts:home")

        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("accounts:login")  # redirects back to login after logout


def confirm_logout_view(request):
    """Show a confirmation page before logout."""
    if request.method == "POST":
        logout(request)
        messages.info(request, "You have been logged out successfully.")
        return redirect("accounts:login")
    return render(request, "accounts/confirm_logout.html")