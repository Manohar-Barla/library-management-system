import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LMS.settings')
django.setup()

from applib.models import User, AdminProfile

username = '123456789'
profiles = AdminProfile.objects.filter(admin_id=username)
print(f"Profiles found with admin_id={username}: {profiles.count()}")
for p in profiles:
    print(f"Profile ID: {p.id}, User: {p.user}")
