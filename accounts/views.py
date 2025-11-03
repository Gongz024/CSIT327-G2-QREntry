# accounts/views.py
from asyncio import events
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib import messages
from .models import Event, Bookmark
from .forms import EventForm
from .forms import RegistrationForm
from django.contrib.auth.decorators import login_required
from datetime import datetime  # ✅ fixed import
import base64

from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

import qrcode
from io import BytesIO
from django.core.mail import EmailMessage
from django.conf import settings
from .models import Ticket
from .models import Profile
from .forms import UserUpdateForm, ProfileUpdateForm

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition

@login_required
def user_profile_view(request):
    user = request.user
    profile, created = Profile.objects.get_or_create(user=user)

    # 🧹 Check if user clicked the "Remove Profile Photo" button
    if request.method == 'POST' and 'remove_profile' in request.POST:
        if profile.profile_picture:
            profile.profile_picture.delete(save=False)  # delete the file from storage
        profile.profile_picture = 'profile_pics/default.png'  # reset to default
        profile.save()
        messages.success(request, "🗑️ Your profile photo has been reset to default.")
        return redirect('accounts:user_profile')

    # 🧩 Handle profile update form normally
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, '✅ Your profile has been updated successfully!')
            return redirect('accounts:user_profile')
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = ProfileUpdateForm(instance=profile)

    return render(request, 'accounts/user_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })

@login_required
def avail_ticket(request, event_id):
    import base64
    import qrcode
    from io import BytesIO
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
    from django.conf import settings
    from django.contrib import messages
    from django.shortcuts import render, redirect, get_object_or_404
    from .models import Event, Ticket

    user = request.user
    event = get_object_or_404(Event, id=event_id)

    # 1️⃣ Create or get existing ticket
    ticket, created = Ticket.objects.get_or_create(
        user=user,
        event_name=event.event_name,
    )

    # 2️⃣ Generate QR Code
    qr_data = f"""
    Ticket ID: {ticket.qr_code_id}
    Event: {event.event_name}
    User: {user.username}
    Email: {user.email}
    """
    qr = qrcode.make(qr_data.strip())
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    qr_img = buffer.getvalue()
    qr_base64 = base64.b64encode(qr_img).decode("utf-8")

    # 3️⃣ Prepare Email
    subject = f"🎟️ Your Ticket for {event.event_name}"
    message = (
        f"Hello {user.first_name or user.username},\n\n"
        f"You have successfully availed a ticket for '{event.event_name}'.\n\n"
        f"Event Details:\n"
        f"📍 Venue: {event.event_venue}\n"
        f"📅 Date: {event.event_date}\n"
        f"🕒 Time: {event.event_time_in} - {event.event_time_out}\n"
        f"💵 Price: ₱{event.ticket_price}\n\n"
        f"Please present the attached QR code at the event gate.\n\n"
        f"Ticket ID: {ticket.qr_code_id}\n\n"
        f"Thank you for using QREntry!"
    )

    # 4️⃣ Send Email using SendGrid
    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)

        email = Mail(
            from_email=settings.FROM_EMAIL,
            to_emails=user.email,
            subject=subject,
            plain_text_content=message,
        )

        # ✅ FIXED — must be plural “attachments”
        attached_qr = Attachment(
            FileContent(qr_base64),
            FileName(f"ticket_{ticket.qr_code_id}.png"),
            FileType("image/png"),
            Disposition("attachment")
        )
        email.add_attachment(attached_qr)

        # 🔍 Debug print for Render logs
        response = sg.send(email)
        print("📨 SENDGRID RESPONSE:", response.status_code, response.body)

        if response.status_code in [200, 202]:
            messages.success(request, "✅ Ticket email has been sent successfully!")
        else:
            messages.warning(
                request,
                f"⚠️ SendGrid returned {response.status_code}. "
                f"Please check logs or verify sender identity."
            )

    except Exception as e:
        print("❌ Email sending error:", e)
        messages.error(request, f"❌ Failed to send email: {e}")

    # 5️⃣ Redirect to confirmation page
    return redirect("accounts:qr_code_sent")


@login_required
def qr_code_sent_view(request):
    return render(request, 'accounts/qr_code_sent.html')


@login_required
def create_event_view(request):
    if request.method == 'POST':
        event_name = request.POST.get('eventName', '').strip()
        venue = request.POST.get('venue', '').strip()
        category = request.POST.get('category', '')
        event_date = request.POST.get('eventDate', '')
        start_time = request.POST.get('startTime', '')
        end_time = request.POST.get('endTime', '')
        ticket_limit = request.POST.get('ticketLimit')
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
            ticket_limit=ticket_limit,
            ticket_price=ticket_price,
            event_description=description
        )

        messages.success(request, '✅ Event successfully created!')
        return redirect('accounts:event_created')

    return render(request, 'accounts/create_event.html')


@login_required
def event_created_view(request):
    return render(request, 'accounts/event_created.html')


# ✅ Modified: redirect to confirmation page after bookmarking
@login_required
def add_bookmark_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    Bookmark.objects.get_or_create(user=request.user, event=event)
    return redirect('accounts:confirmation_bookmark', event_id=event.id)


# ✅ New confirmation page view
@login_required
def confirmation_bookmark_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    return render(request, 'accounts/confirmation_bookmark.html', {'event': event})


@login_required
def remove_bookmark_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    # Delete the bookmark if it exists
    Bookmark.objects.filter(user=request.user, event=event).delete()
    return redirect("accounts:event_detail", event_id=event_id)


@login_required
def bookmarks_view(request):
    # Get all bookmarks for the logged-in user
    bookmarks = Bookmark.objects.filter(user=request.user).select_related("event")
    return render(request, "accounts/bookmark.html", {"bookmarks": bookmarks})

@login_required
def remove_bookmark(request, event_id):
    bookmark = Bookmark.objects.filter(user=request.user, event_id=event_id).first()
    if bookmark:
        bookmark.delete()
    return redirect('accounts:bookmarks')


def view_events_view(request):
    events = Event.objects.all()
    return render(request, 'accounts/event.html', {'events': events})


@login_required
def edit_event_view(request, event_id):
    event = get_object_or_404(Event, id=event_id, organizer=request.user)

    if request.method == 'POST':
        # Get form input
        event_name = request.POST.get('event_name', '').strip()
        event_venue = request.POST.get('event_venue', '').strip()
        event_category = request.POST.get('event_category', '').strip()
        event_date = request.POST.get('event_date', '').strip()
        event_time_in = request.POST.get('event_time_in', '').strip()
        event_time_out = request.POST.get('event_time_out', '').strip()
        event.ticket_limit = request.POST.get('ticket_limit', '').strip()
        ticket_price = request.POST.get('ticket_price', '').replace(',', '').strip()
        event_description = request.POST.get('event_description', '').strip()

        # Validate all required fields
        if not all([event_name, event_venue, event_category, event_date, event_time_in, event_time_out, ticket_price, event_description]):
            messages.error(request, '⚠️ Please fill in all fields before saving.')
            event.event_name = event_name
            event.event_venue = event_venue
            event.event_category = event_category
            event.event_date = event_date
            event.event_time_in = event_time_in
            event.event_time_out = event_time_out
            event.event_description = event_description
            return render(request, 'accounts/edit_event.html', {'event': event})

        # ✅ Validate event date (must be between 2025 and 2030)
        try:
            event_year = datetime.strptime(event_date, "%Y-%m-%d").year
            if event_year < 2025 or event_year > 2030:
                messages.error(request, "⚠️ Event year must be between 2025 and 2030.")
                event.event_name = event_name
                event.event_venue = event_venue
                event.event_category = event_category
                event.event_date = event_date
                event.event_time_in = event_time_in
                event.event_time_out = event_time_out
                event.event_description = event_description
                event.ticket_price = ticket_price
                return render(request, 'accounts/edit_event.html', {'event': event})
        except ValueError:
            messages.error(request, "⚠️ Invalid date format. Please select a valid date.")
            return render(request, 'accounts/edit_event.html', {'event': event})

        # Validate ticket price
        try:
            ticket_price_value = float(ticket_price)
            if ticket_price_value <= 0:
                messages.error(request, "⚠️ Ticket price cannot be less than or equal to 0.")
                event.event_name = event_name
                event.event_venue = event_venue
                event.event_category = event_category
                event.event_date = event_date
                event.event_time_in = event_time_in
                event.event_time_out = event_time_out
                event.event_description = event_description
                event.ticket_price = ticket_price
                return render(request, 'accounts/edit_event.html', {'event': event})
        except ValueError:
            messages.error(request, "⚠️ Please enter a valid numeric ticket price.")
            event.event_name = event_name
            event.event_venue = event_venue
            event.event_category = event_category
            event.event_date = event_date
            event.event_time_in = event_time_in
            event.event_time_out = event_time_out
            event.event_description = event_description
            event.ticket_price = ticket_price
            return render(request, 'accounts/edit_event.html', {'event': event})

        # If all is valid, save
        event.event_name = event_name
        event.event_venue = event_venue
        event.event_category = event_category
        event.event_date = event_date
        event.event_time_in = event_time_in
        event.event_time_out = event_time_out
        event.ticket_price = ticket_price_value
        event.event_description = event_description
        event.save()

        messages.success(request, '✅ Event updated successfully!')
        return redirect('accounts:event')

    return render(request, 'accounts/edit_event.html', {'event': event})


@login_required
def delete_event_view(request, event_id):
    event = get_object_or_404(Event, id=event_id, organizer=request.user)
    if request.method == 'POST':
        event.delete()
        messages.success(request, '🗑️ Event deleted successfully!')
        return redirect('accounts:event')

    return render(request, 'accounts/confirm_delete.html', {'event': event})


@login_required
def organizer_view(request):
    event_created = request.GET.get('created') == 'true'
    return render(request, "accounts/organizer.html", {"event_created": event_created})


def home_view(request):
    """Display only event names on homepage with search filter."""
    query = request.GET.get('q', '').strip()  # Get the search query from the URL
    if query:
        events = Event.objects.filter(event_name__icontains=query)  # Case-insensitive search
    else:
        events = Event.objects.all()

    return render(request, 'accounts/home.html', {
        'events': events,
        'query': query,  # Pass current search value back to the template
    })


def event_detail_view(request, event_id):
    """Show event details when clicked from home."""
    event = get_object_or_404(Event, id=event_id)
    return render(request, 'accounts/event_detail.html', {'event': event})


def register_view(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Registration successful! Welcome to Event CIT, {user.username}!")
            return redirect("accounts:home")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = RegistrationForm()

    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    """Login view with error messages + session handling."""
    if request.user.is_authenticated:
        return redirect("accounts:home")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            if user.username == "organizer" and request.POST.get("password") == "organizer_Strong_Password!123":
                request.session.set_expiry(0)
                return redirect("accounts:organizer")

            if request.POST.get("remember_me"):
                request.session.set_expiry(1209600)
            else:
                request.session.set_expiry(0)

            messages.success(request, f"Welcome back, {user.username}!")
            return redirect("accounts:home")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("accounts:login")


def confirm_logout_view(request):
    """Show a confirmation page before logout."""
    if request.method == "POST":
        logout(request)
        messages.info(request, "You have been logged out successfully.")
        return redirect("accounts:login")
    return render(request, "accounts/confirm_logout.html")
