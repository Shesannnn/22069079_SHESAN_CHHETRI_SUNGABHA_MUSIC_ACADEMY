import requests
import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib import messages
from .models import Course, HomeCourse, Level, Assignment, Profile, Payment, CourseContent, Certificate, Notification, Progress
from .forms import CourseForm, CourseContentForm
from .forms import UserLoginForm, UserRegisterForm, CourseForm
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO

# Home page view
def home(request):
    home_courses = HomeCourse.objects.all()
    return render(request, 'home.html', {'home_courses': home_courses})

# Courses list view with category filtering
def courses_list(request):
    category = request.GET.get('category', 'All')
    
    # Dynamically get unique category choices from model
    all_categories = ['All'] + [choice[0] for choice in Course.CATEGORY_CHOICES]

    if category == 'All':
        courses = Course.objects.all()
    else:
        courses = Course.objects.filter(category=category)

    return render(request, 'courses.html', {
        'courses': courses,
        'categories': all_categories,
        'selected_category': category
    })

# Login view
def login_view(request):
    form = UserLoginForm(request.POST or None)
    next_url = request.GET.get('next')  # Get the 'next' parameter from the URL
    if request.method == "POST":
        print("Form is valid:", form.is_valid())  # Debug: Check form validation
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            print("Attempting to authenticate user:", username)  # Debug: Log username
            user = authenticate(username=username, password=password)
            print("Authenticated user:", user)  # Debug: Check if user is found
            if user:
                login(request, user)
                # Redirect to 'next' URL if present, otherwise to 'home'
                return redirect(next_url or 'home')
            else:
                # Add error message for invalid credentials
                messages.error(request, "Invalid username or password.")
        else:
            print("Form errors:", form.errors)  # Debug: Log form errors
    return render(request, 'login.html', {'form': form})

# Register view
def register_view(request):
    next_url = request.GET.get('next')
    form = UserRegisterForm(request.POST or None)
    
    if form.is_valid():
        user = form.save(commit=False)
        password = form.cleaned_data.get('password')
        user.set_password(password)
        user.save()

        # Create a Profile
        role = form.cleaned_data.get('role')
        Profile.objects.create(user=user, role=role)

        new_user = authenticate(username=user.username, password=password)
        login(request, new_user)
        # Add success message
        messages.success(request, "Registration successful! Welcome to the platform.")
        if next_url:
            return redirect(next_url)
        return redirect('home')
    
    return render(request, "register.html", {'form': form})

# Logout view
def logout_view(request):
    logout(request)
    return redirect('login')

# Course detail view
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    return render(request, 'course_detail.html', {'course': course})

# Course payment view
@login_required
def course_detail_payment(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    return render(request, 'course_detail_payment.html', {'course': course})

# Teacher dashboard view
@login_required
def teacher_dashboard_view(request):
    user = request.user

    if not user.is_authenticated:
        print("Redirecting: User not authenticated")
        return redirect('login')

    if not hasattr(user, 'profile') or user.profile.role != 'Teacher':
        print("Redirecting: User is not a teacher")
        return redirect('home')

    # Handle Course Creation
    if request.method == 'POST' and 'add_course' in request.POST:
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            title = form.cleaned_data['title']
            if Course.objects.filter(title=title, teacher=user).exists():
                form.add_error('title', 'You already have a course with this title.')
            else:
                course = form.save(commit=False)
                course.teacher = user
                course.save()
                form.save_m2m()
                messages.success(request, f'Course "{title}" added successfully!')
                return redirect('teacher_dashboard')
        else:
            messages.error(request, 'Failed to add course. Please check the form.')
    else:
        form = CourseForm()

    # Handle Course Content Creation
    if request.method == 'POST' and 'add_content' in request.POST:
        print("Content form submitted with data:", request.POST, request.FILES)
        content_form = CourseContentForm(request.POST, request.FILES)
        if content_form.is_valid():
            print("Content form is valid")
            course_id = request.POST.get('course_id')
            print(f"Course ID from form: {course_id}")
            try:
                course = get_object_or_404(Course, id=course_id, teacher=user)
                print(f"Course found: {course.title}")
                content = content_form.save(commit=False)
                content.course = course
                content.save()
                print(f"Content saved: {content.title}")
                # Notify enrolled students
                for student in course.students.all():
                    Notification.objects.create(
                        user=student,
                        message=f"New content '{content.title}' added to {course.title}.",
                        is_read=False
                    )
                messages.success(request, f'Content "{content.title}" added to {course.title} successfully!')
                return redirect('teacher_dashboard')
            except Exception as e:
                print(f"Error saving content: {str(e)}")
                messages.error(request, f'Failed to add content: {str(e)}')
        else:
            print("Content form is invalid. Errors:", content_form.errors)
            messages.error(request, 'Failed to add content. Please check the form.')
    else:
        content_form = CourseContentForm()

    # Filter courses taught by the logged-in teacher
    courses = Course.objects.filter(teacher=user)
    print(f"Courses found: {[course.title for course in courses]}")

    # Prepare course_data with all necessary information
    course_data = []
    total_amount_usd = 0
    for course in courses:
        payments = Payment.objects.filter(course=course, status='Completed')
        students = []
        for payment in payments:
            progress = Progress.objects.filter(user=payment.user, course=course).first()
            students.append({
                'user': payment.user,
                'level': payment.level,
                'amount': payment.amount,
                'created_at': payment.created_at,
                'progress': progress.percentage if progress else 0.0
            })
        enrolled_count = len(students)
        assignments = Assignment.objects.filter(course=course)
        contents = CourseContent.objects.filter(course=course)
        print(f"Contents for {course.title}: {list(contents)}")
        for payment in payments:
            total_amount_usd += float(payment.amount)
        course_data.append({
            'course': course,
            'enrolled_count': enrolled_count,
            'students': students,
            'assignments': assignments,
            'contents': contents,
        })

    levels = Level.objects.all()

    context = {
        'course_data': course_data,
        'form': form,
        'content_form': content_form,
        'levels': levels,
        'total_amount_usd': round(total_amount_usd, 2),
    }
    return render(request, 'teacher_dashboard.html', context)

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Course, Payment, Assignment

@login_required
def student_dashboard_view(request):
    user = request.user
    print(f"User: {user.username}, Role: {user.profile.role if hasattr(user, 'profile') else 'No profile'}")

    if not user.is_authenticated:
        print("Redirecting: User not authenticated")
        return redirect('login')

    if not hasattr(user, 'profile') or user.profile.role != 'Student':
        print("Redirecting: User is not a student")
        return redirect('home')

    # Get all completed payments for the student
    completed_payments = Payment.objects.filter(user=user, status='Completed')
    print(f"Completed payments: {list(completed_payments)}")

    # Get the courses the student is enrolled in
    enrolled_courses = [payment.course for payment in completed_payments]
    print(f"Enrolled courses: {[course.title for course in enrolled_courses]}")

    # Calculate the total amount paid (in NPR, assuming amount is stored in USD)
    total_amount_npr = 0
    for payment in completed_payments:
        total_amount_npr += float(payment.amount) * 134
    print(f"Total amount in NPR: {total_amount_npr}")

    # Fetch assignments for each enrolled course and notify about upcoming deadlines
    from datetime import datetime, timedelta
    course_assignments = {}
    for course in enrolled_courses:
        assignments = Assignment.objects.filter(course=course)
        course_assignments[course.id] = assignments
        # Notify about assignments due within 3 days
        for assignment in assignments:
            if assignment.due_date:
                days_until_due = (assignment.due_date - datetime.now().date()).days
                if 0 <= days_until_due <= 3:
                    Notification.objects.get_or_create(
                        user=user,
                        message=f"Reminder: Assignment '{assignment.title}' for {course.title} is due on {assignment.due_date}.",
                        defaults={'created_at': datetime.now(), 'is_read': False}
                    )

    # Fetch progress for each enrolled course
    course_progress = {}
    for course in enrolled_courses:
        progress = Progress.objects.filter(user=user, course=course).first()
        if not progress:
            progress = Progress.objects.create(user=user, course=course, percentage=0.0)
        course_progress[course.id] = progress.percentage

    # Fetch notifications for the user
    notifications = Notification.objects.filter(user=user, is_read=False).order_by('-created_at')[:5]

    # Fetch certificates for the student
    certificates = Certificate.objects.filter(user=user)
    print(f"Certificates found: {[f'{cert.course.title} issued on {cert.issue_date}' for cert in certificates]}")

    context = {
        'user': user,
        'paid_courses': enrolled_courses,
        'total_amount_npr': round(total_amount_npr, 2),
        'course_assignments': course_assignments,
        'course_progress': course_progress,
        'notifications': notifications,
        'certificates': certificates,
    }
    return render(request, 'student_dashboard.html', context)

# User dashboard redirect based on role
@login_required
def user_dashboard(request):
    role = request.user.profile.role
    if role == 'Teacher':
        return redirect('teacher_dashboard')
    elif role == 'Student':
        return redirect('student_dashboard')
    else:
        return redirect('home')

# Khalti payment initiation view
@login_required
def initiate_payment(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid request method")

    level_id = request.POST.get('level')
    course_id = request.POST.get('course_id')
    if not level_id or not course_id:
        return JsonResponse({'error': 'Level and Course are required'}, status=400)

    level = get_object_or_404(Level, id=level_id)
    course = get_object_or_404(Course, id=course_id)
    user = request.user

    if level not in course.levels.all():
        return JsonResponse({'error': 'Selected level does not belong to this course'}, status=400)

    amount_usd = float(level.price)
    amount_npr = amount_usd * settings.USD_TO_NPR_RATE
    amount_paisa = int(amount_npr * 100)

    # Create payment record
    payment = Payment.objects.create(
        user=user,
        course=course,
        level=level,
        purchase_order_name=f"{course.title} - {level.name}",
        amount=amount_usd,
        amount_paisa=amount_paisa,
        status='Initiated'
    )

    # Include payment_id in the return_url
    return_url = f"{settings.KHALTI_RETURN_URL}?payment_id={payment.id}"

    payload = {
        "return_url": return_url,
        "website_url": settings.WEBSITE_URL,
        "amount": amount_paisa,
        "purchase_order_id": str(payment.purchase_order_id),
        "purchase_order_name": f"{course.title} - {level.name}",
        "customer_info": {
            "name": user.username or "Guest",
            "email": user.email or "guest@example.com",
            "phone": "9800000001"
        }
    }
    
    print("Khalti Return URL:", payload["return_url"])

    headers = {
        "Authorization": f"key {settings.KHALTI_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            settings.KHALTI_INITIATE_URL,
            json=payload,
            headers=headers,
            timeout=10
        )
        print("Khalti API Response Status:", response.status_code)
        print("Khalti API Response Text:", response.text)

        if response.status_code == 503:
            return JsonResponse({
                "error": "Payment service is temporarily unavailable. Please try again later."
            }, status=503)

        response_data = response.json()

        if response.status_code == 200 and "payment_url" in response_data:
            payment.pidx = response_data["pidx"]
            payment.save()
            return JsonResponse({"payment_url": response_data["payment_url"]})
        else:
            error_message = response_data.get("error_key", "Failed to initiate payment")
            return JsonResponse({"error": error_message}, status=400)
    except requests.RequestException as e:
        print("Request Exception:", str(e))
        return JsonResponse({"error": f"Payment initiation failed: {str(e)}"}, status=500)
    except ValueError as e:
        print("JSON Decode Error:", str(e))
        return JsonResponse({
            "error": "Payment service returned an invalid response. Please try again later."
        }, status=500)

# Khalti payment success callback view
def payment_success(request):
    payment_id = request.GET.get('payment_id')
    if not payment_id:
        return HttpResponseBadRequest("Payment ID is required")

    payment = get_object_or_404(Payment, id=payment_id)
    pidx = request.GET.get('pidx')
    transaction_id = request.GET.get('transaction_id') or request.GET.get('txnId')
    status = request.GET.get('status')
    amount_paisa = request.GET.get('total_amount')
    purchase_order_id = request.GET.get('purchase_order_id')

    if pidx and payment.pidx != pidx:
        return HttpResponseBadRequest("Invalid payment identifier")

    SANDBOX_SIMULATION = True

    if SANDBOX_SIMULATION:
        if status == 'Completed':
            payment.status = 'Completed'
            payment.transaction_id = transaction_id
            payment.save()

            # Enroll the student in the course
            course = payment.course
            course.students.add(payment.user)

            # Update the user's Profile role to "Student"
            try:
                profile = payment.user.profile
                if profile.role != 'Student':
                    profile.role = 'Student'
                    profile.save()
                    print(f"Updated user {payment.user.username}'s role to Student")
            except Profile.DoesNotExist:
                Profile.objects.create(user=payment.user, role='Student')
                print(f"Created Profile for user {payment.user.username} with role Student")

            # Create success notification
            Notification.objects.create(
                user=payment.user,
                message=f"Payment successful! You are now enrolled in {course.title} - {payment.level.name}.",
                is_read=False
            )

            messages.success(request, f"Payment successful! You are now enrolled in {course.title} - {payment.level.name}.")
            return redirect('payment_success_page', payment_id=payment.id)
        else:
            payment.status = status
            payment.save()
            # Create failure notification
            Notification.objects.create(
                user=payment.user,
                message=f"Payment for {payment.course.title} - {payment.level.name} failed or was canceled.",
                is_read=False
            )
            messages.error(request, "Payment failed or was canceled.")
            return redirect('payment_failure_page', payment_id=payment.id)
    else:
        # Verify the payment with Khalti's API (in production)
        khalti_verify_url = settings.KHALTI_VERIFY_URL
        headers = {
            "Authorization": f"key {settings.KHALTI_SECRET_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "pidx": pidx,
        }

        try:
            response = requests.post(khalti_verify_url, headers=headers, json=payload)
            response_data = response.json()

            if response.status_code == 200 and response_data.get('state') == 'Completed':
                payment.status = 'Completed'
                payment.transaction_id = transaction_id
                payment.save()

                # Enroll the student in the course
                course = payment.course
                course.students.add(payment.user)

                # Update the user's Profile role to "Student"
                try:
                    profile = payment.user.profile
                    if profile.role != 'Student':
                        profile.role = 'Student'
                        profile.save()
                        print(f"Updated user {payment.user.username}'s role to Student")
                except Profile.DoesNotExist:
                    Profile.objects.create(user=payment.user, role='Student')
                    print(f"Created Profile for user {payment.user.username} with role Student")

                # Create success notification
                Notification.objects.create(
                    user=payment.user,
                    message=f"Payment successful! You are now enrolled in {course.title} - {payment.level.name}.",
                    is_read=False
                )

                messages.success(request, f"Payment successful! You are now enrolled in {course.title} - {payment.level.name}.")
                return redirect('payment_success_page', payment_id=payment.id)
            else:
                payment.status = response_data.get('state', 'Failed')
                payment.save()
                # Create failure notification
                Notification.objects.create(
                    user=payment.user,
                    message=f"Payment for {payment.course.title} - {payment.level.name} failed or was canceled.",
                    is_read=False
                )
                messages.error(request, "Payment verification failed.")
                return redirect('payment_failure_page', payment_id=payment.id)
        except requests.RequestException as e:
            payment.status = 'Failed'
            payment.save()
            # Create failure notification
            Notification.objects.create(
                user=payment.user,
                message=f"Payment for {payment.course.title} - {payment.level.name} failed due to an error.",
                is_read=False
            )
            messages.error(request, f"Error verifying payment: {str(e)}")
            return redirect('payment_failure_page', payment_id=payment.id)
        
# Payment success page view
def payment_success_page(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)

    # Ensure the user is authenticated and matches the payment user
    if not request.user.is_authenticated:
        return redirect(f"{settings.LOGIN_URL}?next={request.path}")
    if request.user != payment.user:
        return HttpResponseBadRequest("You are not authorized to view this payment")

    return render(request, 'payment_success.html', {'payment': payment})

# Payment failure page view
def payment_failure_page(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)

    # Ensure the user is authenticated and matches the payment user
    if not request.user.is_authenticated:
        return redirect(f"{settings.LOGIN_URL}?next={request.path}")
    if request.user != payment.user:
        return HttpResponseBadRequest("You are not authorized to view this payment")

    return render(request, 'payment_failure.html', {'payment': payment})

@login_required
def update_profile(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        user = request.user
        user.email = email
        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('student_dashboard')
    return redirect('student_dashboard')

@login_required
def download_invoice(request, payment_id):
    # Fetch the payment
    payment = get_object_or_404(Payment, id=payment_id)

    # Ensure the user is authorized to download this invoice
    if request.user != payment.user:
        return HttpResponseBadRequest("You are not authorized to download this invoice")

    # Create a buffer for the PDF
    buffer = BytesIO()

    # Create the PDF object
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    # Styles for the PDF
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=20,
        textColor=colors.HexColor("#07301f"),
        alignment=1  # Center
    )
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=10,
        textColor=colors.black
    )
    bold_style = ParagraphStyle(
        'Bold',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=10,
        textColor=colors.black,
        fontName='Helvetica-Bold'
    )

    # Add invoice title
    elements.append(Paragraph("Sungabha Music Academy", title_style))
    elements.append(Paragraph("Payment Invoice", title_style))
    elements.append(Spacer(1, 12))

    # Add user and payment details
    elements.append(Paragraph(f"Student: {payment.user.username}", normal_style))
    elements.append(Paragraph(f"Email: {payment.user.email or 'Not provided'}", normal_style))
    elements.append(Spacer(1, 12))

    # Create a table for payment details
    data = [
        ["Description", "Details"],
        ["Course", payment.course.title],
        ["Level", payment.level.name],
        ["Amount", f"USD {payment.amount}"],
        ["Transaction ID", payment.transaction_id],
        ["Payment Date", payment.created_at.strftime("%Y-%m-%d %H:%M:%S")],
    ]

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#d1fae5")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))

    # Add footer text
    elements.append(Paragraph("Thank you for choosing Sungabha Music Academy!", normal_style))
    elements.append(Paragraph("Contact us: sungabhamusicacademy@gmail.com | Phone: 987-4563210", normal_style))

    # Build the PDF
    doc.build(elements)

    # Get the PDF data from the buffer
    buffer.seek(0)
    pdf = buffer.getvalue()
    buffer.close()

    # Create the HTTP response with the PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{payment_id}.pdf"'
    response.write(pdf)

    return response

@login_required
def course_content_view(request, course_id):
    user = request.user
    print(f"User: {user.username}, Role: {user.profile.role if hasattr(user, 'profile') else 'No profile'}")
    
    if not hasattr(user, 'profile') or user.profile.role != 'Student':
        print("Redirecting: User is not a student")
        return redirect('home')

    course = get_object_or_404(Course, id=course_id)
    print(f"Course: {course.title} (ID: {course_id})")

    payment = Payment.objects.filter(user=user, course=course, status='Completed').first()
    print(f"Payment found: {payment is not None}")
    if not payment:
        print("Redirecting: No completed payment found")
        return redirect('student_dashboard')

    contents = CourseContent.objects.filter(course=course)
    print(f"Contents found: {list(contents)}")

    # Update progress
    if contents.exists():
        total_contents = contents.count()
        progress, created = Progress.objects.get_or_create(
            user=user,
            course=course,
            defaults={'percentage': 0.0}
        )
        # Assume viewing the content page means completing one "unit" of content
        # For simplicity, increment progress by 1/total_contents per visit, up to 100%
        if progress.percentage < 100:
            progress.percentage = min(progress.percentage + (100 / total_contents), 100)
            progress.save()
            print(f"Updated progress for {user.username} in {course.title}: {progress.percentage}%")

    context = {
        'course': course,
        'contents': contents,
        'progress': progress.percentage if 'progress' in locals() else 0.0,
    }
    return render(request, 'course_content.html', context)

@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    if request.method == 'POST':
        notification.is_read = True
        notification.save()
        messages.success(request, "Notification marked as read.")
    return redirect('student_dashboard')