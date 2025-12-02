# accounts/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib import messages
from django.urls import reverse
from .models import Event, Bookmark, Ticket, Profile
from .forms import RegistrationForm, UserUpdateForm, ProfileUpdateForm
from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.db import transaction
from django.db.models import F
import qrcode
from io import BytesIO
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
from django.conf import settings
from decimal import Decimal

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from django.urls import reverse

from datetime import datetime

@login_required
def live_search_tickets(request):
    query = request.GET.get('q', '').strip().lower()
    user = request.user
    tickets = user.ticket_set.select_related("event").all()

    now = datetime.now()

    if query:
        tickets = tickets.filter(event__event_name__icontains=query)

    data = {
        "tickets": []
    }

    for t in tickets:
        event_end = datetime.combine(t.event.event_date, t.event.event_time_out)
        is_expired = now > event_end

        data["tickets"].append({
            "id": t.id,
            "event_name": t.event.event_name,
            "event_venue": t.event.event_venue,
            "event_date": t.event.event_date.strftime("%Y-%m-%d"),
            "event_time_in": t.event.event_time_in.strftime("%I:%M %p"),
            "event_time_out": t.event.event_time_out.strftime("%I:%M %p"),
            "ticket_price": t.event.ticket_price,
            "is_edited": t.event.is_edited,
            "is_deleted": t.event.is_deleted,
            "is_expired": is_expired,
        })
    return JsonResponse(data)


@login_required
def ticket_owned_view(request):
    tickets = Ticket.objects.filter(user=request.user).select_related('event')

    now = datetime.now()

    for t in tickets:
        event_datetime_end = datetime.combine(t.event.event_date, t.event.event_time_out)
        t.is_expired = now > event_datetime_end  # ✔ Add field dynamically

    return render(request, 'accounts/ticket_owned.html', {
        'tickets': tickets
    })


@login_required
def delete_ticket_view(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id, user=request.user)
    event = ticket.event
    profile = get_object_or_404(Profile, user=request.user)

    # Determine if expired
    event_end = datetime.combine(event.event_date, event.event_time_out)
    is_expired = datetime.now() > event_end

    try:
        with transaction.atomic():

            # If NOT expired → refund + return ticket to event
            if not is_expired:
                profile.wallet_balance += event.ticket_price
                profile.save(update_fields=['wallet_balance'])

                event.ticket_limit = F('ticket_limit') + 1
                event.save(update_fields=['ticket_limit'])

                messages.success(
                    request,
                    f"🗑️ Ticket for '{event.event_name}' deleted. Refunded ₱{event.ticket_price:.2f}."
                )

            else:
                # EXPIRED → delete without refund
                messages.warning(
                    request,
                    f"❌ Ticket for '{event.event_name}' was expired and has been deleted with no refund."
                )

            # Delete the ticket
            ticket.delete()

    except Exception as e:
        print("❌ Error deleting ticket:", e)
        messages.error(request, "Something went wrong. Please try again.")

    return redirect('accounts:ticket_owned')


@login_required
def user_profile_view(request):
    user = request.user
    profile, created = Profile.objects.get_or_create(user=user)
    
    # Fetch bookmarks and tickets related to user
    bookmarks = Bookmark.objects.filter(user=user).select_related('event')
    tickets = Ticket.objects.filter(user=user).select_related('event')
    
    if request.method == 'POST' and 'remove_profile' in request.POST:
        if profile.profile_picture:
            profile.profile_picture.delete(save=False)
        profile.profile_picture = 'profile_pics/default.png'
        profile.save()
        messages.success(request, "🗑️ Your profile photo has been reset to default.")
        return redirect('accounts:user_profile')

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
        'profile_form': profile_form,
        'profile': profile,
        'bookmarks': bookmarks,
        'tickets': tickets,
    })


@login_required
def avail_ticket(request, event_id):
    """
    Purchase/avail a ticket:
    - Prevent duplicate tickets
    - Use transaction + select_for_update to avoid race conditions
    - Use Decimal arithmetic (no float/Decimal mixing)
    - Decrement ticket_limit safely with F()
    """
    user = request.user
    event = get_object_or_404(Event, id=event_id)
    profile = get_object_or_404(Profile, user=user)

    # Prevent duplicate ticket purchase
    if Ticket.objects.filter(user=user, event=event).exists():
        messages.warning(request, "⚠️ You already have a ticket for this event.")
        return redirect('accounts:event_detail', event_id=event.id)

    try:
        with transaction.atomic():
            # Lock rows
            locked_event = Event.objects.select_for_update().get(id=event.id)
            locked_profile = Profile.objects.select_for_update().get(user=user)

            # ticket_price is a DecimalField on Event => it's already a Decimal
            ticket_price = locked_event.ticket_price
            # ensure types
            if not isinstance(ticket_price, Decimal):
                ticket_price = Decimal(str(ticket_price or "0"))

            # remaining tickets (int)
            remaining = int(locked_event.ticket_limit or 0)

            if remaining <= 0:
                messages.error(request, "❌ This event is sold out.")
                return redirect('accounts:event_detail', event_id=event.id)

            if locked_profile.wallet_balance < ticket_price:
                messages.error(request, f"❌ Insufficient wallet balance (₱{locked_profile.wallet_balance:.2f}).")
                return redirect('accounts:event_detail', event_id=event.id)

            # Deduct wallet using Decimal arithmetic
            locked_profile.wallet_balance = locked_profile.wallet_balance - ticket_price
            locked_profile.save(update_fields=["wallet_balance"])

            # Decrement ticket_limit using F()
            locked_event.ticket_limit = F('ticket_limit') - 1
            locked_event.save(update_fields=["ticket_limit"])
            # refresh to get actual integer value after F() expression
            locked_event.refresh_from_db(fields=['ticket_limit'])

            # Create Ticket
            ticket = Ticket.objects.create(user=user, event=locked_event)

    except Event.DoesNotExist:
        messages.error(request, "Event not found.")
        return redirect('accounts:home')
    except Profile.DoesNotExist:
        messages.error(request, "Profile not found.")
        return redirect('accounts:home')
    except Exception as e:
        print("❌ Transaction failed:", e)
        messages.error(request, "❌ Something went wrong while processing your ticket. Please try again.")
        return redirect('accounts:event_detail', event_id=event.id)

    # Generate QR and email
    qr_data = f"Ticket ID: {ticket.qr_code_id}\nEvent: {locked_event.event_name}\nUser: {user.username}\nEmail: {user.email}"
    qr = qrcode.make(qr_data.strip())
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    qr_base64 = buffer.getvalue()
    qr_base64_b64 = __import__('base64').b64encode(qr_base64).decode("utf-8")

    # Convert times to AM/PM format
    start_time = locked_event.event_time_in.strftime("%I:%M %p")
    end_time = locked_event.event_time_out.strftime("%I:%M %p")

    subject = f"🎟️ Your Ticket for {locked_event.event_name}"
    message = (
        f"Hello {user.first_name or user.username},\n\n"
        f"You have successfully purchased a ticket for '{locked_event.event_name}'.\n"
        f"💰 Remaining balance: ₱{locked_profile.wallet_balance:.2f}\n\n"
        f"Event Details:\n"
        f"📍 {locked_event.event_venue}\n"
        f"📅 {locked_event.event_date}\n"
        f"🕒 {start_time} - {end_time}\n\n"
        f"Ticket ID: {ticket.qr_code_id}\n\n"
        f"Thank you for using QREntry!"
    )

    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        email = Mail(
            from_email=settings.FROM_EMAIL,
            to_emails=user.email,
            subject=subject,
            plain_text_content=message,
        )

        attached_qr = Attachment(
            FileContent(qr_base64_b64),
            FileName(f"ticket_{ticket.qr_code_id}.png"),
            FileType("image/png"),
            Disposition("attachment")
        )
        email.add_attachment(attached_qr)
        sg.send(email)
        messages.success(request, "✅ Ticket purchased successfully! Check your email for the QR code.")
    except Exception as e:
        print("❌ Email sending failed:", e)
        messages.warning(request, "Ticket created but failed to send email. Check your inbox later.")

    return redirect("accounts:qr_code_sent_with_balance",
                    price=str(ticket_price),
                    balance=str(locked_profile.wallet_balance))



@login_required
def qr_code_sent_with_balance_view(request, price, balance):
    return render(request, 'accounts/qr_code_sent.html', {
        'price': price,
        'balance': balance,
        'transaction_success': True
    })


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

        # =============== REQUIRED FIELD CHECKS ===============
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

        # =============== VALIDATIONS ===============
        if event_date:
            try:
                event_date_obj = datetime.strptime(event_date, "%Y-%m-%d").date()
                start_time_obj = datetime.strptime(start_time, "%H:%M").time() if start_time else None
                end_time_obj = datetime.strptime(end_time, "%H:%M").time() if end_time else None

                today = datetime.now().date()
                current_time = datetime.now().time()

                # ❌ Rule 1: Past Date
                if event_date_obj < today:
                    errors['eventDate'] = "❌ You cannot create an event before today's date."

                # ❌ Rule 2: Same-day but past start time
                if event_date_obj == today and start_time_obj and start_time_obj <= current_time:
                    errors['startTime'] = "❌ Start time cannot be earlier than the current time."

                # ❌ Rule 3: End time must be after start time
                if start_time_obj and end_time_obj and end_time_obj <= start_time_obj:
                    errors['endTime'] = "❌ End time must be later than the start time."

            except ValueError:
                errors['eventDate'] = "Invalid event date."

        # =============== RETURN IF ERRORS ===============
        if errors:

            # Show one combined message to the organizer
            for field, error_text in errors.items():
                messages.error(request, f"{error_text}")

            return render(request, 'accounts/create_event.html', {
                'errors': errors,
                'values': request.POST,
            })

        # =============== CREATE EVENT ===============
        Event.objects.create(
            organizer=request.user,
            event_name=event_name,
            event_venue=venue,
            event_category=category,
            event_date=event_date,
            event_time_in=start_time,
            event_time_out=end_time,
            ticket_limit=int(ticket_limit or 0),
            ticket_price=Decimal(str(ticket_price)),
            event_description=description
        )

        messages.success(request, '✅ Event successfully created!')
        return redirect('accounts:event_created')

    return render(request, 'accounts/create_event.html')

def confirmlogout_organizer_view(request):
    return render(request, 'accounts/confirmlogout_organizer.html')


@login_required
def event_created_view(request):
    return render(request, 'accounts/event_created.html')


@login_required
def add_bookmark_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    # Create bookmark safely (no duplicates)
    Bookmark.objects.get_or_create(user=request.user, event=event)

    # Redirect with confirmation
    return redirect('accounts:confirmation_bookmark', event_id=event.id)


@login_required
def confirmation_bookmark_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    return render(request, 'accounts/confirmation_bookmark.html', {'event': event})


@login_required
def remove_bookmark(request, event_id):
    bookmark = Bookmark.objects.filter(user=request.user, event_id=event_id).first()
    if bookmark:
        bookmark.delete()
        from django.contrib import messages
        messages.success(request, "⭐ Bookmark removed successfully!")
    else:
        messages.warning(request, "Bookmark not found.")
    return redirect('accounts:bookmarks')



@login_required
def bookmarks_view(request):
    bookmarks = Bookmark.objects.filter(user=request.user).select_related("event")

    now = timezone.now()

    for b in bookmarks:
        event_end = datetime.combine(b.event.event_date, b.event.event_time_out)
        event_end = timezone.make_aware(event_end)
        b.is_expired = now > event_end

    return render(request, "accounts/bookmark.html", {"bookmarks": bookmarks})


@login_required
def remove_bookmark(request, event_id):
    bookmark = Bookmark.objects.filter(user=request.user, event_id=event_id).first()
    if bookmark:
        bookmark.delete()
        messages.success(request, "⭐ Bookmark removed successfully!")
    else:
        messages.warning(request, "Bookmark not found!")

    return redirect('accounts:bookmarks')

@login_required
def view_events_view(request):
    events = Event.objects.filter(is_deleted=False).order_by('-created_at')

    now = timezone.now()

    for e in events:
        # Combine event date + time into a full datetime
        event_end = datetime.combine(e.event_date, e.event_time_out)

        # Make it timezone-aware so comparison won't error
        event_end = timezone.make_aware(event_end)

        # Add custom field so template can show “Expired!”
        e.is_expired = now > event_end

    return render(request, 'accounts/event.html', {'events': events})

@login_required
def organizer_events_view(request):
    events = Event.objects.filter(organizer=request.user).order_by('-created_at')
    return render(request, 'accounts/event.html', {'events': events})


@login_required
def edit_event_view(request, event_id):
    event = get_object_or_404(Event, id=event_id, organizer=request.user)

    if request.method == 'POST':

        before = {
            "name": event.event_name,
            "venue": event.event_venue,
            "category": event.event_category,
            "date": str(event.event_date),
            "time_in": str(event.event_time_in),
            "time_out": str(event.event_time_out),
            "ticket_limit": event.ticket_limit,
            "ticket_price": str(event.ticket_price),
            "description": event.event_description,
        }

        event_name = request.POST.get('event_name', '').strip()
        event_venue = request.POST.get('event_venue', '').strip()
        event_category = request.POST.get('event_category', '').strip()
        event_date = request.POST.get('event_date', '').strip()
        event_time_in = request.POST.get('event_time_in', '').strip()
        event_time_out = request.POST.get('event_time_out', '').strip()
        ticket_limit = request.POST.get('ticket_limit', '').strip()
        ticket_price = request.POST.get('ticket_price', '').replace(',', '').strip()
        event_description = request.POST.get('event_description', '').strip()

        event.ticket_limit = int(ticket_limit or 0)

        # -------- REQUIRED FIELD CHECK --------
        if not all([
            event_name, event_venue, event_category, event_date,
            event_time_in, event_time_out, ticket_price, event_description
        ]):
            messages.error(request, '⚠️ Please fill in all fields before saving.')
            event.event_name = event_name
            event.event_venue = event_venue
            event.event_category = event_category
            event.event_date = event_date
            event.event_time_in = event_time_in
            event.event_time_out = event_time_out
            event.event_description = event_description
            return render(request, 'accounts/edit_event.html', {'event': event})

        # -------- VALIDATION: YEAR --------
        try:
            event_year = datetime.strptime(event_date, "%Y-%m-%d").year
            if event_year < 2025 or event_year > 2030:
                messages.error(request, "⚠️ Event year must be between 2025 and 2030.")
                return render(request, 'accounts/edit_event.html', {'event': event})
        except ValueError:
            messages.error(request, "⚠️ Invalid date format. Please select a valid date.")
            return render(request, 'accounts/edit_event.html', {'event': event})

        # -------- VALIDATION: PRICE --------
        try:
            ticket_price_value = float(ticket_price)
            if ticket_price_value <= 0:
                messages.error(request, "⚠️ Ticket price cannot be less than or equal to 0.")
                return render(request, 'accounts/edit_event.html', {'event': event})
        except ValueError:
            messages.error(request, "⚠️ Enter a valid numeric ticket price.")
            return render(request, 'accounts/edit_event.html', {'event': event})

        # ============= NEW RULES BELOW =============

        try:
            # Convert
            event_date_obj = datetime.strptime(event_date, "%Y-%m-%d").date()
            start_time_obj = datetime.strptime(event_time_in, "%H:%M").time()
            end_time_obj = datetime.strptime(event_time_out, "%H:%M").time()

            today = datetime.now().date()
            current_time = datetime.now().time()

            # ❌ RULE 1: Date cannot be before today
            if event_date_obj < today:
                messages.error(request, "❌ You cannot set an event date BEFORE today.")
                return render(request, 'accounts/edit_event.html', {'event': event})

            # ❌ RULE 2: Start time cannot be before current time if event is today
            if event_date_obj == today and start_time_obj <= current_time:
                messages.error(request, "❌ Start time cannot be earlier than the current time.")
                return render(request, 'accounts/edit_event.html', {'event': event})

            # ❌ RULE 3: End time must be after start time
            if end_time_obj <= start_time_obj:
                messages.error(request, "❌ End time must be later than the start time.")
                return render(request, 'accounts/edit_event.html', {'event': event})

        except Exception:
            messages.error(request, "⚠️ Invalid date or time format.")
            return render(request, 'accounts/edit_event.html', {'event': event})

        # ============= SAVE EVENT =============
        event.event_name = event_name
        event.event_venue = event_venue
        event.event_category = event_category
        event.event_date = event_date
        event.event_time_in = event_time_in
        event.event_time_out = event_time_out
        event.ticket_price = Decimal(str(ticket_price))
        event.event_description = event_description
        event.save()

        # -------- CHANGE DETECTION --------
        after = {
            "name": event.event_name,
            "venue": event.event_venue,
            "category": event.event_category,
            "date": str(event.event_date),
            "time_in": str(event.event_time_in),
            "time_out": str(event.event_time_out),
            "ticket_limit": event.ticket_limit,
            "ticket_price": str(event.ticket_price),
            "description": event.event_description,
        }

        if before != after:
            event.is_edited = True
            event.save(update_fields=['is_edited'])

            tickets = Ticket.objects.filter(event=event).select_related('user')
            for ticket in tickets:
                send_event_status_email(ticket.user, event, status="edited")

        messages.success(request, '✅ Event updated successfully!')
        return redirect('accounts:event')

    return render(request, 'accounts/edit_event.html', {'event': event})


@login_required
def delete_event_view(request, event_id):
    event = get_object_or_404(Event, id=event_id, organizer=request.user)
    if request.method == 'POST':
        # For debugging: confirm handler runs
        print(f"[delete_event_view] user={request.user} deleting event={event.id}")

        event.is_deleted = True
        event.save(update_fields=['is_deleted'])

        # Notify all users who bought a ticket (if any)
        tickets = Ticket.objects.filter(event=event).select_related("user")
        for ticket in tickets:
            try:
                send_event_status_email(ticket.user, event, "deleted")
            except Exception as e:
                print("Failed sending deletion email to", ticket.user.email, e)

        messages.success(request, '🗑️ Event deleted successfully!')
        return redirect('accounts:event')
    return render(request, 'accounts/confirm_delete.html', {'event': event})


def send_event_status_email(user, event, status):
    subject = ""
    text = ""

    if status == "deleted":
        subject = f"❌ Event Deleted: {event.event_name}"
        text = (
            f"Hello {user.username},\n\n"
            f"The event '{event.event_name}' has been deleted by the organizer.\n"
            f"Your ticket is no longer valid.\n\n"
            f"Thank you."
        )
    elif status == "edited":
        subject = f"✏️ Event Updated: {event.event_name}"
        text = (
            f"Hello {user.username},\n\n"
            f"The event '{event.event_name}' has been updated by the organizer.\n"
            f"Please check the event page for new details.\n\n"
            f"Thank you."
        )

    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        email = Mail(
            from_email=settings.FROM_EMAIL,
            to_emails=user.email,
            subject=subject,
            plain_text_content=text,
        )
        sg.send(email)
    except Exception as e:
        print("Email failed:", e)

@login_required
def live_search_organizer_events(request):
    """
    Live search for organizer's events (exclude deleted).
    Returns the full set of fields needed by the frontend.
    """
    query = request.GET.get("q", "").strip()
    user = request.user

    # Only organizer's not-deleted events
    events = Event.objects.filter(organizer=user, is_deleted=False).select_related()

    if query:
        events = events.filter(event_name__icontains=query)

    # Order newest -> oldest so frontend will place newest first
    events = events.order_by("-created_at")

    results = []
    for e in events:
        results.append({
            "id": e.id,
            "event_name": e.event_name,
            "event_venue": e.event_venue,
            "event_category": e.event_category,
            "event_date": e.event_date.strftime("%Y-%m-%d"),
            "event_time_in": e.event_time_in.strftime("%I:%M %p"),
            "event_time_out": e.event_time_out.strftime("%I:%M %p"),
            "ticket_price": str(e.ticket_price),
            "ticket_limit": e.ticket_limit,
            "event_description": e.event_description,
            "is_deleted": e.is_deleted,
            # Provide edit/delete urls for organizer UI
            "edit_url": reverse("accounts:edit_event", args=[e.id]),
            "delete_url": reverse("accounts:delete_event", args=[e.id]),
            # Optional detail url (if you use it)
            "detail_url": reverse("accounts:event_detail", args=[e.id]),
        })

    return JsonResponse({"events": results})


@login_required
def organizer_view(request):
    event_created = request.GET.get('created') == 'true'
    return render(request, "accounts/organizer.html", {"event_created": event_created})


from datetime import datetime
from django.utils import timezone

def home_view(request):
    query = request.GET.get('q', '').strip()

    events_query = Event.objects.filter(is_deleted=False)

    if query:
        from django.db.models import Q
        events_query = events_query.filter(
            Q(event_name__icontains=query) |
            Q(event_venue__icontains=query) |
            Q(event_date__icontains=query)
        )

    events = events_query.order_by('-created_at')

    now = timezone.now()

    for e in events:
        # new/recent tag
        one_week_ago = now - timedelta(days=7)
        e.status = "new" if e.created_at >= one_week_ago else "recent"

        # EXPIRED CHECK
        event_end = datetime.combine(e.event_date, e.event_time_out)
        event_end = timezone.make_aware(event_end)  # FIX offset-aware comparison
        e.is_expired = now > event_end

    return render(request, 'accounts/home.html', {
        'events': events,
        'query': query,
    })

from accounts.models import Bookmark

def event_detail_view(request, event_id):
    event = get_object_or_404(Event, id=event_id, is_deleted=False)

    user_has_ticket = False
    if request.user.is_authenticated:
        user_has_ticket = Ticket.objects.filter(user=request.user, event=event).exists()

    # ADD THIS:
    is_bookmarked = False
    if request.user.is_authenticated:
        is_bookmarked = Bookmark.objects.filter(user=request.user, event=event).exists()

    remaining = int(event.ticket_limit or 0)
    sold_out = (remaining <= 0)

    return render(request, 'accounts/event_detail.html', {
        'event': event,
        'user_has_ticket': user_has_ticket,
        'sold_out': sold_out,
        'is_bookmarked': is_bookmarked,  # 👈 add this
    })



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
    if request.user.is_authenticated:
        return redirect("accounts:home")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.username == "organizer" and request.POST.get("password") == "organizer_Strong_Password!123":
                request.session.set_expiry(0)
                return redirect("accounts:event")
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
    if request.method == "POST":
        logout(request)
        messages.info(request, "You have been logged out successfully.")
        return redirect("accounts:login")
    return render(request, "accounts/confirm_logout.html")

from django.http import JsonResponse

from datetime import timedelta
from django.utils import timezone

def live_search_events(request):
    q = request.GET.get("q", "").strip()

    # Search by name, venue, or date
    from django.db.models import Q
    
    events = Event.objects.filter(
        Q(event_name__icontains=q) |
        Q(event_venue__icontains=q) |
        Q(event_date__icontains=q),
        is_deleted=False
    ).order_by("-created_at")

    results = []
    now = timezone.now()
    one_week_ago = now - timedelta(days=7)

    for e in events:
        status = "new" if e.created_at >= one_week_ago else "recent"

        results.append({
            "id": e.id,
            "name": e.event_name,
            "status": status,
            "url": reverse("accounts:event_detail", args=[e.id]),
        })

    return JsonResponse({"events": results})