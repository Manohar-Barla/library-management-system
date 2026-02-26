from django.contrib import admin
from .models import *

admin.site.register(User)
admin.site.register(AdminProfile)
admin.site.register(FacultyProfile)
admin.site.register(StudentProfile)
admin.site.register(PreRegisteredAdmin)
admin.site.register(PreRegisteredFaculty)
admin.site.register(PreRegisteredStudent)

admin.site.register(Book)
admin.site.register(Category)
admin.site.register(Author)
admin.site.register(BookIssue)
admin.site.register(Fine)
admin.site.register(OTPVerification)
admin.site.register(ActivityLog)