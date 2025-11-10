
from django.contrib.auth.models import User
from accounts.models import Profile, DEFAULT_WALLET_BALANCE 


def create_organizer_account():
    username = "organizer"
    password = "organizer_Strong_Password!123"
    
    if not User.objects.filter(username=username).exists():
        # 1. Create the Superuser
        user = User.objects.create_superuser(
            username=username, 
            password=password, 
            email=""
        )
        
        # 2. Explicitly Create the Profile to ensure it has the correct fields (e.g., wallet_balance)
        # We assume the signal (post_save) will handle this, but explicitly creating it here 
        # ensures it is created with the correct default value (10000.00).
        # Note: If the post_save signal is active, this line is technically redundant, 
        # but it provides a clean fallback if the signal fails or is slow.
        try:
            # Check if a profile was created by the signal; if not, create one
            if not hasattr(user, 'profile'):
                 Profile.objects.create(user=user, wallet_balance=DEFAULT_WALLET_BALANCE)
                 
        except Exception:
            # This catch is mainly for cases where the signal is not yet connected
            Profile.objects.create(user=user, wallet_balance=DEFAULT_WALLET_BALANCE)


        print("Organizer account created.")
    else:
        print("Organizer account already exists.")