from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import random
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum
from twilio.rest import Client
from .models import Book, BookIssue, Fine, StudentProfile, PreRegisteredAdmin, PreRegisteredFaculty, PreRegisteredStudent
from datetime import datetime, timedelta

def members(request):
    template = loader.get_template('Home.html')
    return HttpResponse(template.render())

def register_view(request):
    if request.method == 'POST':
        roll_number = request.POST.get('roll_number')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        mobile = request.POST.get('mobile')
        user_type = request.POST.get('user_type', 'student')
        
        # Profile fields
        dob = request.POST.get('dob')
        gender = request.POST.get('gender')
        course = request.POST.get('course', '')
        branch = request.POST.get('branch', '')
        year = request.POST.get('year', '')
        address = request.POST.get('address', '')
        city = request.POST.get('city', '')
        pincode = request.POST.get('pincode', '')
        
        if User.objects.filter(username=roll_number).exists():
            messages.error(request, "A user with this Roll Number/ID is already registered.")
            return redirect('register')
            
        if User.objects.filter(email=email).exists():
            messages.error(request, "This email is already registered.")
            return redirect('register')
            
        # Create User
        user = User.objects.create_user(
            username=roll_number,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            identifier=roll_number,
            mobile=mobile,
            role=user_type # Use user_type from form
        )
        
        # Create Profile
        from .models import StudentProfile, FacultyProfile, AdminProfile
        
        if user_type == 'student':
            StudentProfile.objects.create(
                user=user,
                roll_no=roll_number,
                dob=dob if dob else None,
                gender=gender,
                course=course,
                branch=branch,
                year=year,
                address=address,
                city=city,
                pincode=pincode
            )
        elif user_type == 'faculty':
            FacultyProfile.objects.create(
                user=user,
                faculty_id=roll_number,
                department=branch,
                designation='Faculty'
            )
        elif user_type == 'admin':
            AdminProfile.objects.create(
                user=user,
                admin_id=roll_number,
                password=password
            )
            
        messages.success(request, "Registration successful! You can now log in.")
        return redirect('login')
        
    return render(request, 'Register.html')

def login_view(request):
    if request.method == 'POST':
        identifier = request.POST.get('username') # ID from form
        password = request.POST.get('password')
        role_selected = request.POST.get('role')

        user = authenticate(request, username=identifier, password=password)
        
        if user is not None:
            # Check if role matches what they selected (optional security step)
            if user.role != role_selected:
                messages.error(request, "Selected category does not match your assigned role.")
                return redirect('login')

            login(request, user)
            
            if user.role == 'admin':
                return redirect('admin_dashboard')
            elif user.role == 'student':
                return redirect('student_dashboard')
            # Add teacher/staff later if needed
            return redirect('members')
        else:
            messages.error(request, "Invalid ID or Password.")
            return redirect('login')

    return render(request, 'login.html')

@login_required
def admin_dashboard(request):
    if request.user.role != 'admin':
        return HttpResponse("Unauthorized", status=401)
        
    total_students = StudentProfile.objects.count()
    total_books = Book.objects.count()
    total_issued = BookIssue.objects.filter(returned=False).count()
    
    total_fines_agg = Fine.objects.aggregate(total=Sum('amount'))
    total_fines = total_fines_agg['total'] if total_fines_agg['total'] else 0.00
    
    recent_issues = BookIssue.objects.order_by('-issue_date')[:5]
    
    context = {
        'total_students': total_students,
        'total_books': total_books,
        'total_issued': total_issued,
        'total_fines': total_fines,
        'recent_issues': recent_issues
    }
    return render(request, 'admin_dashboard.html', context)


@login_required
def student_dashboard(request):
    if request.user.role != 'student':
        return HttpResponse("Unauthorized", status=401)
        
    recent_issues = BookIssue.objects.filter(student=request.user).select_related('book').order_by('-issue_date')[:5]
    issued_count = BookIssue.objects.filter(student=request.user, returned=False).count()
    
    context = {
        'issued_count': issued_count,
        'recent_issues': recent_issues,
    }
    return render(request, 'student_dashboard.html', context)

@login_required
def student_profile(request):
    if request.user.role != 'student':
        return HttpResponse("Unauthorized", status=401)
        
    profile = StudentProfile.objects.filter(user=request.user).first()
    
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name')
        request.user.last_name = request.POST.get('last_name')
        request.user.mobile = request.POST.get('mobile')
        request.user.save()
        
        if profile:
            profile.course = request.POST.get('course')
            profile.branch = request.POST.get('branch')
            profile.year = request.POST.get('year')
            profile.address = request.POST.get('address')
            profile.city = request.POST.get('city')
            profile.pincode = request.POST.get('pincode')
            profile.save()
            
        messages.success(request, "Profile updated successfully.")
        return redirect('student_profile')
        
    return render(request, 'student_profile.html', {'profile': profile})

@login_required
def student_library(request):
    if request.user.role != 'student':
        return HttpResponse("Unauthorized", status=401)
        
    query = request.GET.get('q', '').strip()
    books = Book.objects.select_related('author', 'category').all()
    
    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__name__icontains=query) |
            Q(category__name__icontains=query) |
            Q(isbn__icontains=query)
        )
        
    return render(request, 'student_library.html', {'books': books})

@login_required
def student_issued(request):
    if request.user.role != 'student':
        return HttpResponse("Unauthorized", status=401)
        
    issues = BookIssue.objects.filter(student=request.user).select_related('book__author', 'book__category').order_by('-issue_date')
    return render(request, 'student_issued.html', {'issues': issues})

@login_required
def student_change_password(request):
    if request.user.role != 'student':
        return HttpResponse("Unauthorized", status=401)
        
    from django.contrib.auth import update_session_auth_hash
    
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not request.user.check_password(old_password):
            messages.error(request, "Incorrect current password.")
        elif new_password != confirm_password:
            messages.error(request, "New passwords do not match.")
        else:
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, "Password updated successfully.")
            return redirect('student_dashboard')
            
    return render(request, 'student_change_password.html')


# ==========================================
# CATEGORY MANAGEMENT
# ==========================================

from .models import Category

@login_required
def category_list(request):
    if request.user.role != 'admin':
        return HttpResponse("Unauthorized", status=401)
    categories = Category.objects.all()
    return render(request, 'category_list.html', {'categories': categories})

@login_required
def category_add(request):
    if request.user.role != 'admin':
        return HttpResponse("Unauthorized", status=401)
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        if Category.objects.filter(name__iexact=name).exists():
            messages.error(request, "Category with this name already exists.")
        else:
            Category.objects.create(name=name, description=description)
            messages.success(request, "Category added successfully.")
            return redirect('category_list')
    return render(request, 'category_form.html')

@login_required
def category_edit(request, pk):
    if request.user.role != 'admin':
        return HttpResponse("Unauthorized", status=401)
    from django.shortcuts import get_object_or_404
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        if Category.objects.filter(name__iexact=name).exclude(pk=pk).exists():
            messages.error(request, "Another category with this name already exists.")
        else:
            category.name = name
            category.description = description
            category.save()
            messages.success(request, "Category updated successfully.")
            return redirect('category_list')
            
    return render(request, 'category_form.html', {'category': category})

@login_required
def category_delete(request, pk):
    if request.user.role != 'admin':
        return HttpResponse("Unauthorized", status=401)
    from django.shortcuts import get_object_or_404
    category = get_object_or_404(Category, pk=pk)
    category.delete()
    messages.success(request, "Category deleted successfully.")
    return redirect('category_list')


# ==========================================
# AUTHOR MANAGEMENT
# ==========================================

from .models import Author

@login_required
def author_list(request):
    if request.user.role != 'admin':
        return HttpResponse("Unauthorized", status=401)
    authors = Author.objects.all()
    return render(request, 'author_list.html', {'authors': authors})

@login_required
def author_add(request):
    if request.user.role != 'admin':
        return HttpResponse("Unauthorized", status=401)
    if request.method == 'POST':
        name = request.POST.get('name')
        bio = request.POST.get('bio')
        if Author.objects.filter(name__iexact=name).exists():
            messages.error(request, "Author with this name already exists.")
        else:
            Author.objects.create(name=name, bio=bio)
            messages.success(request, "Author added successfully.")
            return redirect('author_list')
    return render(request, 'author_form.html')

@login_required
def author_edit(request, pk):
    if request.user.role != 'admin':
        return HttpResponse("Unauthorized", status=401)
    from django.shortcuts import get_object_or_404
    author = get_object_or_404(Author, pk=pk)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        bio = request.POST.get('bio')
        if Author.objects.filter(name__iexact=name).exclude(pk=pk).exists():
            messages.error(request, "Another author with this name already exists.")
        else:
            author.name = name
            author.bio = bio
            author.save()
            messages.success(request, "Author updated successfully.")
            return redirect('author_list')
            
    return render(request, 'author_form.html', {'author': author})

@login_required
def author_delete(request, pk):
    if request.user.role != 'admin':
        return HttpResponse("Unauthorized", status=401)
    from django.shortcuts import get_object_or_404
    author = get_object_or_404(Author, pk=pk)
    author.delete()
    messages.success(request, "Author deleted successfully.")
    return redirect('author_list')


# ==========================================
# BOOK MANAGEMENT
# ==========================================

@login_required
def book_list(request):
    if request.user.role != 'admin':
        return HttpResponse("Unauthorized", status=401)
    books = Book.objects.select_related('author', 'category').all()
    return render(request, 'book_list.html', {'books': books})

@login_required
def book_add(request):
    if request.user.role != 'admin':
        return HttpResponse("Unauthorized", status=401)
    
    from .models import Category, Author
    if request.method == 'POST':
        isbn = request.POST.get('isbn')
        title = request.POST.get('title')
        author_id = request.POST.get('author')
        category_id = request.POST.get('category')
        total_copies = request.POST.get('total_copies')
        available_copies = request.POST.get('available_copies')
        
        if Book.objects.filter(isbn=isbn).exists():
            messages.error(request, "A book with this ISBN already exists.")
        else:
            Book.objects.create(
                isbn=isbn,
                title=title,
                author_id=author_id,
                category_id=category_id,
                total_copies=total_copies,
                available_copies=available_copies
            )
            messages.success(request, "Book registered successfully.")
            return redirect('book_list')
            
    categories = Category.objects.all()
    authors = Author.objects.all()
    return render(request, 'book_form.html', {'categories': categories, 'authors': authors})

@login_required
def book_edit(request, pk):
    if request.user.role != 'admin':
        return HttpResponse("Unauthorized", status=401)
        
    from django.shortcuts import get_object_or_404
    from .models import Category, Author
    book = get_object_or_404(Book, pk=pk)
    
    if request.method == 'POST':
        isbn = request.POST.get('isbn')
        title = request.POST.get('title')
        author_id = request.POST.get('author')
        category_id = request.POST.get('category')
        total_copies = request.POST.get('total_copies')
        available_copies = request.POST.get('available_copies')
        
        if Book.objects.filter(isbn=isbn).exclude(pk=pk).exists():
            messages.error(request, "Another book with this ISBN already exists.")
        else:
            book.isbn = isbn
            book.title = title
            book.author_id = author_id
            book.category_id = category_id
            book.total_copies = total_copies
            book.available_copies = available_copies
            book.save()
            
            messages.success(request, "Book updated successfully.")
            return redirect('book_list')
            
    categories = Category.objects.all()
    authors = Author.objects.all()
    return render(request, 'book_form.html', {
        'book': book,
        'categories': categories, 
        'authors': authors
    })

@login_required
def book_delete(request, pk):
    if request.user.role != 'admin':
        return HttpResponse("Unauthorized", status=401)
    from django.shortcuts import get_object_or_404
    book = get_object_or_404(Book, pk=pk)
    book.delete()
    messages.success(request, "Book deleted successfully.")
    return redirect('book_list')


# ==========================================
# BOOK ISSUE AND RETURN
# ==========================================

from django.utils import timezone
from .models import User

@login_required
def issue_list(request):
    if request.user.role != 'admin':
        return HttpResponse("Unauthorized", status=401)
    issues = BookIssue.objects.select_related('student', 'book').all().order_by('-issue_date')
    return render(request, 'issue_list.html', {'issues': issues})

@login_required
def issue_add(request):
    if request.user.role != 'admin':
        return HttpResponse("Unauthorized", status=401)
        
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        book_id = request.POST.get('book_id')
        
        student = User.objects.get(id=student_id)
        book = Book.objects.get(id=book_id)
        
        if book.available_copies <= 0:
            messages.error(request, "This book goes out of stock.")
        else:
            # Check if student already has this book issued and not returned
            if BookIssue.objects.filter(student=student, book=book, returned=False).exists():
                messages.error(request, "Student has already issued this book and not returned it.")
            else:
                due_date = request.POST.get('due_date')
                BookIssue.objects.create(
                    student=student, 
                    book=book,
                    due_date=due_date if due_date else None
                )
                book.available_copies -= 1
                book.save()
                messages.success(request, f"Book '{book.title}' issued successfully to {student.username}.")
                return redirect('issue_list')
                
    students = User.objects.filter(role='student')
    books = Book.objects.filter(available_copies__gt=0)
    return render(request, 'issue_form.html', {'students': students, 'books': books})

@login_required
def issue_return(request, pk):
    if request.user.role != 'admin':
        return HttpResponse("Unauthorized", status=401)
    
    from django.shortcuts import get_object_or_404
    issue = get_object_or_404(BookIssue, pk=pk)
    
    if request.method == 'POST':
        if not issue.returned:
            issue.returned = True
            issue.return_date = timezone.now()
            issue.save()
            
            book = issue.book
            book.available_copies += 1
            book.save()
            
            messages.success(request, f"Book '{book.title}' returned successfully.")
            
    return redirect('issue_list')


# ==========================================
# STUDENT MANAGEMENT
# ==========================================

from django.db.models import Q

@login_required
def student_list(request):
    if request.user.role != 'admin':
        return HttpResponse("Unauthorized", status=401)
        
    query = request.GET.get('q', '').strip()
    students = StudentProfile.objects.select_related('user').all()
    
    if query:
        students = students.filter(
            Q(user__username__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query)
        )
        
    return render(request, 'student_list.html', {'students': students})

@login_required
def student_detail(request, user_id):
    if request.user.role != 'admin':
        return HttpResponse("Unauthorized", status=401)
        
    from django.shortcuts import get_object_or_404
    student_user = get_object_or_404(User, id=user_id, role='student')
    student_profile = StudentProfile.objects.filter(user=student_user).first()
    
    issue_history = BookIssue.objects.filter(student=student_user).select_related('book').order_by('-issue_date')
    
    context = {
        'student_user': student_user,
        'student_profile': student_profile,
        'issue_history': issue_history,
    }
    return render(request, 'student_detail.html', context)


# ==========================================
# AUTHENTICATION & PROFILE
# ==========================================

@login_required
def admin_change_password(request):
    if request.user.role != 'admin':
        return HttpResponse("Unauthorized", status=401)
        
    from django.contrib.auth import update_session_auth_hash
    
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not request.user.check_password(old_password):
            messages.error(request, "Incorrect current password.")
        elif new_password != confirm_password:
            messages.error(request, "New passwords do not match.")
        else:
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user) # Keeps user logged in
            messages.success(request, "Password updated successfully.")
            return redirect('admin_dashboard')
            
    return render(request, 'admin_change_password.html')

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('login')


def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        new_password = request.POST.get('new_password')
        
        try:
            # First map the email to the user
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            messages.success(request, "Password has been successfully recovered. Please log in.")
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, "This email is not registered in our system.")
            return redirect('forgot_password')
            
    return render(request, 'forgot_password.html')




# Store OTP temporarily (for demo purpose)
EMAIL_OTP_STORE = {}

def send_email_otp(request):
    if request.method == "POST":
        email = request.POST.get('email')
        otp = str(random.randint(100000, 999999))  # 6-digit OTP
        print(otp)

        # Store OTP in session for verification
        request.session['email_otp'] = otp

        # Send Email
        send_mail(
            subject="Your OTP Code",
            message=f"Your OTP is {otp}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
            
        )
        return JsonResponse({'status': 'OTP sent successfully'})
    return JsonResponse({'status': 'Invalid request'}, status=400)

otp_storage = {}

# @csrf_exempt
# def send_mobile_otp(request):
#     if request.method != 'POST':
#         return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

#     mobile = request.POST.get('mobile')

#     if not mobile:
#         return JsonResponse({'status': 'error', 'message': 'Mobile number required'})

#     # Prevent sending OTP to Twilio number itself
#     if f"+91{mobile}" == settings.TWILIO_PHONE_NUMBER:
#         return JsonResponse({
#             'status': 'error',
#             'message': 'Cannot send OTP to Twilio sender number'
#         })

#     otp = str(random.randint(100000, 999999))

#     # Store OTP with expiry (5 minutes)
#     request.session['mobile_otp'] = otp
#     request.session['mobile_otp_expiry'] = (
#         datetime.now() + timedelta(minutes=5)
#     ).isoformat()

#     print("Generated Mobile OTP:", otp)

#     try:
#         client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

#         client.messages.create(
#             body=f"Your OTP is {otp}",
#             from_=settings.TWILIO_PHONE_NUMBER,
#             to=f"+91{mobile}"
#         )

#         return JsonResponse({
#             'status': 'success',
#             'message': 'OTP sent successfully'
#         })

#     except Exception as e:
#         print("Twilio Error:", e)
#         return JsonResponse({
#             'status': 'error',
#             'message': 'Failed to send OTP'
#         })
    


def verify_email_otp(request):
    if request.method == "POST":
        entered_otp = request.POST.get("otp")
        saved_otp = request.session.get("email_otp")

        if entered_otp == saved_otp:
            request.session["email_verified"] = True
            return JsonResponse({
                "status": "success",
                "message": "✅ Email OTP verified successfully"
            })

        return JsonResponse({
            "status": "error",
            "message": "❌ Invalid Email OTP"
        })


# def verify_mobile_otp(request):
#     if request.method == "POST":
#         entered_otp = request.POST.get("otp")
#         saved_otp = request.session.get("mobile_otp")

#         if entered_otp == saved_otp:
#             request.session["mobile_verified"] = True
#             return JsonResponse({
#                 "status": "success",
#                 "message": "✅ Mobile OTP verified successfully"
#             })

#         return JsonResponse({
#             "message": "❌ Invalid Mobile OTP"
#         })


def fetch_user_details(request):
    identifier = request.GET.get('roll_no')  # your frontend sends roll_no

    if not identifier:
        return JsonResponse({
            "status": "error",
            "message": "ID is required."
        })

    # 1️⃣ Check Student
    try:
        student = PreRegisteredStudent.objects.get(roll_no=identifier)

        return JsonResponse({
            "status": "success",
            "data": {
                "email": student.email,
                "mobile": student.mobile,
                "first_name": student.first_name,
                "last_name": student.last_name,
                "branch": student.branch,
                "year_of_joining": student.year_of_joining,
                "user_type": "student"
            }
        })

    except PreRegisteredStudent.DoesNotExist:
        pass

    # 2️⃣ Check Faculty
    try:
        faculty = PreRegisteredFaculty.objects.get(faculty_id=identifier)

        return JsonResponse({
            "status": "success",
            "data": {
                "email": faculty.email,
                "mobile": faculty.mobile,
                "first_name": faculty.first_name,
                "last_name": faculty.last_name,
                "branch": faculty.department, # Map department to branch for UI
                "user_type": "faculty"
            }
        })

    except PreRegisteredFaculty.DoesNotExist:
        pass

    # 3️⃣ Check Admin
    try:
        admin = PreRegisteredAdmin.objects.get(admin_id=identifier)

        return JsonResponse({
            "status": "success",
            "data": {
                "email": admin.email,
                "mobile": admin.mobile,
                "first_name": admin.first_name,
                "last_name": admin.last_name,
                "user_type": "admin"
            }
        })

    except PreRegisteredAdmin.DoesNotExist:
        return JsonResponse({
            "status": "error",
            "message": "ID not found. Contact management."
        })