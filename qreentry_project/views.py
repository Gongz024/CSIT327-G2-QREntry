from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def home_view(request):
    """
    Homepage view that shows different content based on authentication status.
    """
    context = {
        'user': request.user,
    }
    return render(request, 'home.html', context)

# Optional: Add a simple dashboard for logged-in users
@login_required
def dashboard_view(request):
    """
    Dashboard view for authenticated users (for future QR entry features).
    """
    return render(request, 'dashboard.html', {'user': request.user})

    EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")

@require_POST
def forgot_password(request):
    try:
        payload = json.loads(request.body.decode("utf-8")) if request.body else {}
    except Exception:
        payload = {}

    email = (payload.get("email") or request.POST.get("email") or "").strip()

    if not email or not EMAIL_REGEX.match(email):
        return JsonResponse({"errors": {"email": [{"message": "Enter a valid email address"}]}}, status=400)

    redirect_to = getattr(settings, "SUPABASE_RESET_REDIRECT", "http://127.0.0.1:8000/accounts/reset-password/")

    try:
        supabase.auth.reset_password_for_email(email, {"redirect_to": redirect_to})
        return JsonResponse({"success": True, "message": "A reset link has been sent to your email."})
    except Exception as e:
        if getattr(settings, "DEBUG", False):
            try:
                detail = e.args[0]
            except Exception:
                detail = repr(e)
            return JsonResponse({"errors": {"supabase": [{"message": detail or "Auth error"}]}}, status=400)
        print("Forgot password error:", repr(e))
        return JsonResponse({"success": True, "message": "A reset link has been sent to your email."})

def reset_password_page(request):
    return render(request, "accounts/password_reset_confirm.html")