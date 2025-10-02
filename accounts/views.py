# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages

def register_view(request):
    """
    Register using Django's UserCreationForm. On success: log in and send to dashboard.
    """
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Registration successful! Welcome to Event CIT, {user.username}!")
            return redirect("dashboard")  # send them to the dashboard after signup
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserCreationForm()

    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    """
    Login view with error messaging and "remember me" session handling.
    If 'remember_me' is checked, session lasts for 2 weeks; otherwise expires on browser close.
    """
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # session management: remember me?
            if request.POST.get("remember_me"):
                # 2 weeks
                request.session.set_expiry(1209600)
            else:
                # expire on browser close
                request.session.set_expiry(0)

            messages.success(request, f"Welcome back, {user.username}!")
            return redirect("dashboard")
        else:
            # form will contain field-specific errors but we'll add a general message too
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = AuthenticationForm()

    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("accounts:login")
