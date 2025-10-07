# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login,logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required


@login_required
def home_view(request):
    """
    Homepage for logged-in users.
    """
    return render(request, "accounts/home.html", {"user": request.user})



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
        # Already logged in → just redirect to login again (or later dashboard)
        return redirect("accounts:login")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # remember me handling
            if request.POST.get("remember_me"):
                request.session.set_expiry(1209600)  # 2 weeks
            else:
                request.session.set_expiry(0)  # until browser close

            messages.success(request, f"Welcome back, {user.username}!")
            return redirect("accounts:home")
            return redirect("accounts:login")  # stays on login page for now
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