import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LMS.settings')
django.setup()

from applib.models import User, AdminProfile, PreRegisteredAdmin

username = '123456789'
password = 'password123'

# 1. Pre-register
admin_pre, _ = PreRegisteredAdmin.objects.get_or_create(
    admin_id=username,
    defaults={
        'first_name': 'Test',
        'last_name': 'Admin',
        'email': 'admin@example.com',
        'mobile': '1234567890',
        'department': 'Administration'
    }
)

# 2. Get or Create User
user, created = User.objects.get_or_create(
    username=username,
    defaults={
        'email': 'admin@example.com',
        'first_name': 'Test',
        'last_name': 'Admin',
        'role': 'admin'
    }
)
user.set_password(password)
user.role = 'admin'
user.save()
print(f"User check: {user.username}, Role: {user.role}")

# 3. Handle AdminProfile
try:
    # Try to find by admin_id first since we know it exists
    profile = AdminProfile.objects.get(admin_id=username)
    profile.user = user
    profile.password = password
    profile.save()
    print(f"Linked existing AdminProfile (admin_id={username}) to User.")
except AdminProfile.DoesNotExist:
    # If it doesn't exist, create it
    profile = AdminProfile.objects.create(
        user=user,
        admin_id=username,
        password=password
    )
    print(f"Created new AdminProfile for User.")

print(f"\nSUCCESS: Admin account {username} is ready with password: {password}")
