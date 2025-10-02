from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib import messages

# Create your views here.

def register_view(request):
    """
    Handles user registration using Django's built-in UserCreationForm.
    """
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            # Save the user and automatically log them in
            user = form.save()
            login(request, user)  # Logs the user in after successful registration
            messages.success(
                request,
                f"Registration successful! Welcome to Event CIT, {user.username}!"
            )
            # Redirect to the registration page itself after successful registration
            # You'll see a success message there.
            return redirect("accounts:register")
    else:
        form = UserCreationForm()

    return render(request, "accounts/register.html", {"form": form})

# IMPORTANT: login_view, logout_view, and home_view are REMOVED from this file.