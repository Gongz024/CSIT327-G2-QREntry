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

 