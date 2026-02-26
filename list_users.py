import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LMS.settings')
django.setup()

from applib.models import User

users = User.objects.all()
print(f"Total users: {users.count()}")
for user in users:
    print(f"Username: {user.username}, Role: {user.role}, Identifier: {user.identifier}")
