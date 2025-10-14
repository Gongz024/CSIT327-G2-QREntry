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

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Event
from django.contrib.auth.decorators import login_required


@login_required
def create_event_view(request):
    if request.method == 'POST':
        event_name = request.POST.get('eventName', '').strip()
        venue = request.POST.get('venue', '').strip()
        category = request.POST.get('category', '')
        event_date = request.POST.get('eventDate', '')
        start_time = request.POST.get('startTime', '')
        end_time = request.POST.get('endTime', '')
        ticket_price = request.POST.get('ticketPrice', '')
        description = request.POST.get('description', '').strip()

        errors = {}

        # --- Validation ---
        if not event_name:
            errors['eventName'] = "Event name is required."
        if not venue:
            errors['venue'] = "Venue is required."
        if not category:
            errors['category'] = "Please select a category."
        if not event_date:
            errors['eventDate'] = "Event date is required."
        if not start_time:
            errors['startTime'] = "Start time is required."
        if not end_time:
            errors['endTime'] = "End time is required."
        if ticket_price == '' or float(ticket_price) < 0:
            errors['ticketPrice'] = "Please enter a valid ticket price."
        if not description:
            errors['description'] = "Description is required."

        # Check if any errors exist
        if errors:
            return render(request, 'accounts/create_event.html', {
                'errors': errors,
                'values': request.POST,  # Keep form values
            })

        # ✅ If all good, create event
        Event.objects.create(
            organizer=request.user,
            event_name=event_name,
            event_venue=venue,
            event_category=category,
            event_date=event_date,
            event_time_in=start_time,
            event_time_out=end_time,
            ticket_price=ticket_price,
            event_description=description
        )

        messages.success(request, '✅ Event successfully created!')
        return redirect('accounts:event_created')

    return render(request, 'accounts/create_event.html')


@login_required
def event_created_view(request):
    return render(request, 'accounts/event_created.html')

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