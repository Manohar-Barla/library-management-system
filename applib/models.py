from django.db import models
from django.contrib.auth.models import AbstractUser

# ----------------------------
# Custom User Model
# ----------------------------
class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('student', 'Student'),
        ('faculty', 'Faculty'),
        ('staff', 'Staff'),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='student'
    )
    
    # We remove old specific fields from here to separate them into their respective profiles
    identifier = models.CharField(max_length=50, unique=True, null=True, blank=True) # Used for ID/Roll No

    mobile = models.CharField(max_length=15, null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    mobile_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.username


# ==========================================
# ACTIVE USER PROFILES
# ==========================================

class AdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    admin_id = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Admin: {self.admin_id}"

class FacultyProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    faculty_id = models.CharField(max_length=50, unique=True)
    department = models.CharField(max_length=100, null=True, blank=True)
    designation = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Faculty: {self.faculty_id}"

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    roll_no = models.CharField(max_length=50, unique=True)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)
    course = models.CharField(max_length=100, null=True, blank=True)
    branch = models.CharField(max_length=100, null=True, blank=True)
    year = models.CharField(max_length=50, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    pincode = models.CharField(max_length=10, null=True, blank=True)
    fine_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    def __str__(self):
        return f"Student: {self.roll_no}"


# ==========================================
# PRE-REGISTERED DATA (Admin filled)
# ==========================================

class PreRegisteredAdmin(models.Model):
    admin_id = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=15, unique=True)
    department = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.admin_id} - {self.first_name} {self.last_name}"


class PreRegisteredFaculty(models.Model):
    faculty_id = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=15, unique=True)
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.faculty_id} - {self.first_name} {self.last_name}"


class PreRegisteredStudent(models.Model):
    BRANCH_CHOICES = (
        ('CSE', 'Computer Science & Engineering'),
        ('ECE', 'Electronics & Communication Engineering'),
        ('Mech', 'Mechanical Engineering'),
        ('Civil', 'Civil Engineering'),
        ('IT', 'Information Technology'),
        ('AI', 'Artificial Intelligence'),
        ('Other', 'Other'),
    )

    roll_no = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=15, unique=True)
    branch = models.CharField(max_length=100, choices=BRANCH_CHOICES)
    year_of_joining = models.IntegerField()

    def __str__(self):
        return f"{self.roll_no} - {self.first_name} {self.last_name}"


# ----------------------------
# Category Model
# ----------------------------
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


# ----------------------------
# Author Model
# ----------------------------
class Author(models.Model):
    name = models.CharField(max_length=100, unique=True)
    bio = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


# ----------------------------
# Book Model
# ----------------------------
class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    isbn = models.CharField(max_length=20, unique=True)
    total_copies = models.IntegerField(default=1)
    available_copies = models.IntegerField(default=1)

    def __str__(self):
        return self.title


# ----------------------------
# Book Issue Model
# ----------------------------
from django.utils import timezone

class BookIssue(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    return_date = models.DateField(null=True, blank=True)
    returned = models.BooleanField(default=False)

    @property
    def days_remaining(self):
        if self.returned or not self.due_date:
            return None
        delta = self.due_date - timezone.now().date()
        return delta.days

    def __str__(self):
        return f"{self.student.username} - {self.book.title}"


# ----------------------------
# Fine Model
# ----------------------------
class Fine(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    book_issue = models.ForeignKey(BookIssue, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} - ₹{self.amount}"


# ----------------------------
# OTP Verification Model
# ----------------------------
class OTPVerification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - OTP"


# ----------------------------
# Activity Log (Admin Monitoring)
# ----------------------------
class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.action}"
