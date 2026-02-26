import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LMS.settings')
django.setup()

from applib.models import User, AdminProfile

username = '123456789'
try:
    user = User.objects.get(username=username)
    print(f"Found user: {user.username}, Role: {user.role}")
    
    # Fix role
    if user.role != 'admin':
        user.role = 'admin'
        user.save()
        print(f"Updated role to: {user.role}")
    
    # Fix/Create AdminProfile
    profile, created = AdminProfile.objects.get_or_create(user=user, defaults={'admin_id': username})
    print(f"AdminProfile created: {created}, profile admin_id: {profile.admin_id}")
    
    if not created and profile.admin_id != username:
        profile.admin_id = username
        profile.save()
        print(f"Updated profile admin_id to: {profile.admin_id}")

except User.DoesNotExist:
    print(f"User {username} not found.")
except Exception as e:
    print(f"Error: {e}")
