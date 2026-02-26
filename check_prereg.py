import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LMS.settings')
django.setup()

from applib.models import PreRegisteredAdmin

try:
    admin = PreRegisteredAdmin.objects.get(admin_id='123456789')
    print(f"ID 123456789 is pre-registered: {admin.first_name} {admin.last_name}")
except PreRegisteredAdmin.DoesNotExist:
    print("ID 123456789 is NOT pre-registered as Admin.")

admins = PreRegisteredAdmin.objects.all()
print(f"Total pre-registered admins: {admins.count()}")
for a in admins:
    print(f"ID: {a.admin_id}, Name: {a.first_name} {a.last_name}")
