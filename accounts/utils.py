from django.contrib.auth.models import User

def create_organizer_account():
    username = "organizer"
    password = "organizer_Strong_Password!123"
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, password=password, email="")
        print("Organizer account created.")