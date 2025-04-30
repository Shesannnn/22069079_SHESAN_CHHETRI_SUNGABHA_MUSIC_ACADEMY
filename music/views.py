import requests
import uuid
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib import messages
from django.views.decorators.cache import never_cache
from .models import Course, HomeCourse, Level, Assignment, Profile, Payment, CourseContent, Certificate, Notification, Progress, Teacher, AssignmentSubmission
from .forms import CourseForm, CourseContentForm, UserLoginForm, UserRegisterForm
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
from django.core.mail import send_mail
from datetime import datetime
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError
from django.contrib.auth.models import User
import re

logger = logging.getLogger(__name__)

# Home page view
def home(request):
    home_courses = HomeCourse.objects.all()
    logger.debug(f"Rendering home page for user: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
    return render(request, 'home.html', {'home_courses': home_courses})

# Courses list view with category filtering
def courses_list(request):
    category = request.GET.get('category', 'All')
    all_categories = ['All'] + [choice[0] for choice in Course.CATEGORY_CHOICES]
    courses = Course.objects.all() if category == 'All' else Course.objects.filter(category=category)
    logger.debug(f"Rendering courses list: category={category}, user={request.user.username if request.user.is_authenticated else 'Anonymous'}")
    return render(request, 'courses.html', {
        'courses': courses,
        'categories': all_categories,
        'selected_category': category
    })

# Login view
def login_view(request):
    form = UserLoginForm(request.POST or None)
    next_url = request.GET.get('next')
    if request.method == "POST":
        logger.debug(f"Login attempt: form_valid={form.is_valid()}")
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            logger.debug(f"Authenticating user: {username}")
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                logger.info(f"User {username} logged in")
                request.session.modified = True
                return redirect(next_url or 'home')
        else:
            # Display form errors as messages
            for error in form.non_field_errors():
                messages.error(request, error)
            logger.error(f"Form errors: {form.errors}")
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
        role = form.cleaned_data.get('role')
        Profile.objects.create(user=user, role=role)
        new_user = authenticate(username=user.username, password=password)
        login(request, new_user)
        logger.info(f"User {user.username} registered with role {role}")
        messages.success(request, "Registration successful! Welcome to the platform.")
        return redirect(next_url or 'home')
    logger.debug(f"Rendering register page: form_errors={form.errors}")
    return render(request, "register.html", {'form': form})

def logout_view(request):
    request.session.pop('payment_id', None)
    request.session.pop('payment_user', None)
    logout(request)
    logger.info(f"User {request.user.username if request.user.is_authenticated else 'Anonymous'} logged out")
    return redirect('login')

# Course detail view
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    logger.debug(f"Rendering course detail: course_id={course_id}, user={request.user.username if request.user.is_authenticated else 'Anonymous'}")
    return render(request, 'course_detail.html', {'course': course})

# Course payment view
@login_required
def course_detail_payment(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    logger.debug(f"Rendering course payment: course_id={course_id}, user={request.user.username}")
    return render(request, 'course_detail_payment.html', {'course': course})

# Teacher Dashboard View
@login_required
def teacher_dashboard_view(request):
    user = request.user
    logger.debug(f"Accessing teacher dashboard: user={user.username}")
    if not user.is_authenticated:
        logger.warning("Redirecting: User not authenticated")
        return redirect('login')
    if not hasattr(user, 'profile') or user.profile.role != 'Teacher':
        logger.warning(f"Redirecting: User {user.username} is not a teacher")
        return redirect('home')

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
                logger.info(f"Course {title} added by {user.username}")
                messages.success(request, f'Course "{title}" added successfully!')
                return redirect('teacher_dashboard')
        else:
            logger.error(f"Course form errors: {form.errors}")
            messages.error(request, 'Failed to add course. Please check the form.')
    else:
        form = CourseForm()

    if request.method == 'POST' and 'add_content' in request.POST:
        content_form = CourseContentForm(request.POST, request.FILES)
        if content_form.is_valid():
            course_id = request.POST.get('course_id')
            course = get_object_or_404(Course, id=course_id, teacher=user)
            content = content_form.save(commit=False)
            content.course = course
            content.save()
            for student in course.students.all():
                Notification.objects.create(
                    user=student,
                    message=f"New content '{content.title}' added to {course.title}.",
                    is_read=False
                )
            logger.info(f"Content {content.title} added to {course.title} by {user.username}")
            messages.success(request, f'Content "{content.title}" added to {course.title} successfully!')
            return redirect('teacher_dashboard')
        else:
            logger.error(f"Content form errors: {content_form.errors}")
            messages.error(request, 'Failed to add content. Please check the form.')
    else:
        content_form = CourseContentForm()

    if request.method == 'POST' and 'add_assignment' in request.POST:
        course_id = request.POST.get('course_id')
        course = get_object_or_404(Course, id=course_id, teacher=user)
        title = request.POST.get('title')
        description = request.POST.get('description')
        due_date = request.POST.get('due_date')

        try:
            due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
            assignment = Assignment.objects.create(
                course=course,
                title=title,
                description=description,
                due_date=due_date
            )
            for student in course.students.all():
                AssignmentSubmission.objects.create(
                    assignment=assignment,
                    student=student,
                    status='Not Started'
                )
                Notification.objects.create(
                    user=student,
                    message=f"New assignment '{assignment.title}' for {course.title} due on {assignment.due_date}.",
                    is_read=False
                )
            logger.info(f"Assignment {title} added to {course.title} by {user.username}")
            messages.success(request, f'Assignment "{title}" added to {course.title} successfully!')
            return redirect('teacher_dashboard')
        except ValueError as e:
            logger.error(f"Assignment creation error: {str(e)}")
            messages.error(request, 'Failed to add assignment. Please check the form (e.g., date format YYYY-MM-DD).')

    courses = Course.objects.filter(teacher=user)
    course_data = []
    total_amount_npr = 0
    for course in courses:
        payments = Payment.objects.filter(course=course, status='Completed')
        students = [{
            'user': payment.user,
            'level': payment.level,
            'amount': payment.amount,
            'created_at': payment.created_at,
            'progress': Progress.objects.filter(user=payment.user, course=course).first().percentage if Progress.objects.filter(user=payment.user, course=course).exists() else 0.0
        } for payment in payments]
        enrolled_count = len(students)
        assignments = Assignment.objects.filter(course=course)
        assignment_data = []
        for assignment in assignments:
            submissions = AssignmentSubmission.objects.filter(assignment=assignment)
            assignment_data.append({
                'assignment': assignment,
                'submissions': submissions
            })
        contents = CourseContent.objects.filter(course=course)
        for payment in payments:
            total_amount_npr += float(payment.amount)
        course_data.append({
            'course': course,
            'enrolled_count': enrolled_count,
            'students': students,
            'assignments': assignment_data,
            'contents': contents,
        })

    levels = Level.objects.all()
    context = {
        'course_data': course_data,
        'form': form,
        'content_form': content_form,
        'levels': levels,
        'total_amount_npr': round(total_amount_npr, 2),
    }
    logger.debug(f"Rendering teacher dashboard: courses={len(courses)}")
    return render(request, 'teacher_dashboard.html', context)

@login_required
def student_dashboard_view(request):
    user = request.user
    logger.debug(f"Accessing student dashboard: user={user.username}, role={user.profile.role if hasattr(user, 'profile') else 'No profile'}")
    if not user.is_authenticated:
        logger.warning("Redirecting: User not authenticated")
        return redirect('login')
    if not hasattr(user, 'profile') or user.profile.role != 'Student':
        logger.warning(f"Redirecting: User {user.username} is not a student")
        return redirect('home')

    completed_payments = Payment.objects.filter(user=user, status='Completed')
    enrolled_courses = [payment.course for payment in completed_payments]
    total_amount_npr = sum(float(payment.amount) for payment in completed_payments)

    from datetime import datetime
    course_assignments = []
    for course in enrolled_courses:
        assignments = Assignment.objects.filter(course=course)
        assignment_data = []
        for assignment in assignments:
            submission, created = AssignmentSubmission.objects.get_or_create(
                assignment=assignment,
                student=user,
                defaults={'status': 'Not Started'}
            )
            assignment_data.append({
                'assignment': assignment,
                'submission': submission
            })
        course_assignments.append({
            'course': course,
            'assignments': assignment_data
        })
        for assignment in assignments:
            if assignment.due_date:
                days_until_due = (assignment.due_date - datetime.now().date()).days
                if 0 <= days_until_due <= 3:
                    Notification.objects.get_or_create(
                        user=user,
                        message=f"Reminder: Assignment '{assignment.title}' for {course.title} is due on {assignment.due_date}.",
                        defaults={'is_read': False}
                    )

    course_progress = {course.id: Progress.objects.filter(user=user, course=course).first().percentage if Progress.objects.filter(user=user, course=course).exists() else 0.0 for course in enrolled_courses}
    notifications = Notification.objects.filter(user=user, is_read=False).order_by('-created_at')[:5]
    certificates = Certificate.objects.filter(user=user)

    context = {
        'user': user,
        'paid_courses': enrolled_courses,
        'total_amount_npr': round(total_amount_npr, 2),
        'course_assignments': course_assignments,
        'course_progress': course_progress,
        'notifications': notifications,
        'certificates': certificates,
    }
    logger.debug(f"Rendering student dashboard: courses={len(enrolled_courses)}, course_assignments={course_assignments}")
    return render(request, 'student_dashboard.html', context)

@login_required
def submit_assignment(request, assignment_id):
    user = request.user
    if not hasattr(user, 'profile') or user.profile.role != 'Student':
        logger.warning(f"Redirecting: User {user.username} is not a student")
        return redirect('home')

    assignment = get_object_or_404(Assignment, id=assignment_id)
    submission, created = AssignmentSubmission.objects.get_or_create(
        assignment=assignment,
        student=user,
        defaults={'status': 'Not Started'}
    )

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'submit':
            submission_text = request.POST.get('submission_text')
            submission_file = request.FILES.get('submission_file')
            submission.status = 'Submitted'
            submission.submission_text = submission_text
            if submission_file:
                submission.submission_file = submission_file
            submission.submitted_at = timezone.now()
            submission.save()
            if assignment.course.teacher:
                Notification.objects.create(
                    user=assignment.course.teacher,
                    message=f"Student {user.username} submitted assignment '{assignment.title}' for {assignment.course.title}.",
                    is_read=False
                )
            else:
                logger.warning(f"Cannot create notification: No teacher assigned to course {assignment.course.title}")
            messages.success(request, f"Assignment '{assignment.title}' submitted successfully!")
        elif action == 'complete':
            submission.status = 'Completed'
            submission.completed_at = timezone.now()
            submission.save()
            if assignment.course.teacher:
                Notification.objects.create(
                    user=assignment.course.teacher,
                    message=f"Student {user.username} marked assignment '{assignment.title}' as completed for {assignment.course.title}.",
                    is_read=False
                )
            else:
                logger.warning(f"Cannot create notification: No teacher assigned to course {assignment.course.title}")
            messages.success(request, f"Assignment '{assignment.title}' marked as completed!")
        return redirect('student_dashboard')

    return redirect('student_dashboard')

@login_required
def user_dashboard(request):
    user = request.user
    logger.debug(f"Accessing user_dashboard for user: {user.username}, Authenticated: {user.is_authenticated}")
    
    try:
        profile = user.profile
    except Profile.DoesNotExist:
        logger.error(f"User {user.username} has no Profile object")
        messages.error(request, "Your account is missing a profile. Please contact support.")
        Profile.objects.create(user=user, role='Student')
        return redirect('home')
    
    role = profile.role.strip()
    logger.debug(f"User {user.username} has role: '{role}'")
    
    if role.lower() == 'teacher':
        logger.info(f"Redirecting {user.username} to teacher_dashboard")
        return redirect('teacher_dashboard')
    elif role.lower() == 'student':
        logger.info(f"Redirecting {user.username} to student_dashboard")
        return redirect('student_dashboard')
    else:
        logger.warning(f"User {user.username} has unknown role: '{role}'. Redirecting to home.")
        return redirect('home')
    
@login_required
def initiate_payment(request):
    if request.method != "POST":
        logger.error("Invalid request method for initiate_payment")
        return HttpResponseBadRequest("Invalid request method")

    level_id = request.POST.get('level')
    course_id = request.POST.get('course_id')
    if not level_id or not course_id:
        logger.error("Level or Course ID missing")
        return JsonResponse({'error': 'Level and Course are required'}, status=400)

    level = get_object_or_404(Level, id=level_id)
    course = get_object_or_404(Course, id=course_id)
    user = request.user
    logger.debug(f"Initiating payment: user={user.username}, course={course.title}, level={level.name}")

    if level not in course.levels.all():
        logger.error(f"Level {level.name} does not belong to course {course.title}")
        return JsonResponse({'error': 'Selected level does not belong to this course'}, status=400)

    amount_npr = float(level.price)
    amount_paisa = int(amount_npr * 100)

    if Payment.objects.filter(user=user, course=course, level=level, status='Completed').exists():
        logger.warning(f"User {user.username} already paid for {course.title} - {level.name}")
        messages.error(request, "You have already enrolled in this course level.")
        return JsonResponse({'error': 'Already enrolled'}, status=400)

    request.session.pop('payment_id', None)
    request.session.pop('payment_user', None)

    payment = Payment.objects.create(
        user=user,
        course=course,
        level=level,
        purchase_order_name=f"{course.title} - {level.name}",
        amount=amount_npr,
        amount_paisa=amount_paisa,
        status='Initiated'
    )
    request.session['payment_id'] = str(payment.id)
    request.session['payment_user'] = user.username
    logger.info(f"Created payment: ID={payment.id}, user={user.username}, session: payment_id={request.session['payment_id']}, payment_user={request.session['payment_user']}")

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
    
    headers = {
        "Authorization": f"key {settings.KHALTI_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(settings.KHALTI_INITIATE_URL, json=payload, headers=headers, timeout=10)
        logger.debug(f"Khalti API response: status={response.status_code}, body={response.text}")
        if response.status_code == 503:
            logger.error("Khalti service unavailable")
            return JsonResponse({"error": "Payment service is temporarily unavailable. Please try again later."}, status=503)

        response_data = response.json()
        if response.status_code == 200 and "payment_url" in response_data:
            payment.pidx = response_data["pidx"]
            payment.save()
            logger.info(f"Payment initiated: pidx={payment.pidx}")
            return JsonResponse({"payment_url": response_data["payment_url"]})
        else:
            error_message = response_data.get("error_key", "Failed to initiate payment")
            logger.error(f"Payment initiation failed: {error_message}")
            return JsonResponse({"error": error_message}, status=400)
    except requests.RequestException as e:
        logger.error(f"Payment initiation error: {str(e)}")
        return JsonResponse({"error": f"Payment initiation failed: {str(e)}"}, status=500)
    except ValueError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return JsonResponse({"error": "Payment service returned an invalid response. Please try again later."}, status=500)

@login_required
def payment_success(request):
    logger.debug(f"Payment success called: GET={request.GET}, Session={request.session.items()}")
    payment_id = request.GET.get('payment_id') or request.session.get('payment_id')
    if not payment_id:
        logger.error("Payment ID missing")
        messages.error(request, "Payment ID is required")
        return HttpResponseBadRequest("Payment ID is required")

    try:
        payment = get_object_or_404(Payment, id=payment_id)
    except Payment.DoesNotExist:
        logger.error(f"Payment {payment_id} not found")
        messages.error(request, "Payment not found")
        return HttpResponseBadRequest("Payment not found")

    logger.info(f"Found payment: ID={payment.id}, user={payment.user.username if payment.user else 'None'}")

    if not request.user.is_authenticated:
        logger.error("Unauthenticated user in payment_success")
        messages.error(request, "You must be logged in to process this payment.")
        return redirect('login')

    session_payment_user = request.session.get('payment_user')
    if session_payment_user and session_payment_user != request.user.username:
        logger.error(f"Session user mismatch: session_payment_user={session_payment_user}, authenticated={request.user.username}")
        messages.error(request, "Session mismatch. Please initiate a new payment.")
        request.session.pop('payment_id', None)
        request.session.pop('payment_user', None)
        return HttpResponseBadRequest("Session mismatch. Please initiate a new payment.")

    if not payment.user:
        logger.error(f"Payment {payment_id} has no associated user")
        messages.error(request, "Invalid payment record. Please contact support.")
        return HttpResponseBadRequest("Invalid payment record.")

    if payment.user != request.user:
        logger.error(f"User mismatch: authenticated={request.user.username}, payment_user={payment.user.username}")
        messages.error(request, "You are not authorized to process this payment.")
        return HttpResponseBadRequest("You are not authorized to process this payment.")

    pidx = request.GET.get('pidx')
    transaction_id = request.GET.get('transaction_id') or request.GET.get('txnId')
    status = request.GET.get('status')
    amount_paisa = request.GET.get('total_amount')
    purchase_order_id = request.GET.get('purchase_order_id')

    if pidx and payment.pidx != pidx:
        logger.error(f"Invalid pidx: expected={payment.pidx}, got={pidx}")
        messages.error(request, "Invalid payment identifier")
        return HttpResponseBadRequest("Invalid payment identifier")

    SANDBOX_SIMULATION = True
    if SANDBOX_SIMULATION:
        if status and status.lower() == 'completed':
            payment.status = 'Completed'
            payment.transaction_id = transaction_id or f"TEST-{payment.id}-{uuid.uuid4().hex[:8]}"
            payment.save()
            course = payment.course
            logger.debug(f"Enrolling user {payment.user.username} in course {course.title}")
            course.students.add(payment.user)
            logger.info(f"User {payment.user.username} enrolled in course {course.title}")
            try:
                profile = payment.user.profile
                if profile.role != 'Student':
                    profile.role = 'Student'
                    profile.save()
                    logger.info(f"Updated user {payment.user.username}'s role to Student")
            except Profile.DoesNotExist:
                Profile.objects.create(user=payment.user, role='Student')
                logger.info(f"Created Profile for user {payment.user.username}")
            Notification.objects.create(
                user=payment.user,
                message=f"Payment successful! You are now enrolled in {course.title} - {payment.level.name}.",
                is_read=False
            )
            messages.success(request, f"Payment successful! You are now enrolled in {course.title} - {payment.level.name}.")
            request.session.pop('payment_id', None)
            request.session.pop('payment_user', None)
            logger.info(f"Payment {payment.id} completed, redirecting to success page")
            return redirect('payment_success_page', payment_id=payment.id)
        else:
            payment.status = status or 'Failed'
            payment.save()
            Notification.objects.create(
                user=payment.user,
                message=f"Payment for {payment.course.title} - {payment.level.name} failed or was canceled.",
                is_read=False
            )
            messages.error(request, f"Payment failed or was canceled. Status: {status or 'Unknown'}")
            logger.warning(f"Payment {payment.id} failed: status={status}")
            return redirect('payment_failure_page', payment_id=payment_id)
    else:
        khalti_verify_url = settings.KHALTI_VERIFY_URL
        headers = {
            "Authorization": f"key {settings.KHALTI_SECRET_KEY}",
            "Content-Type": "application/json",
        }
        payload = {"pidx": pidx}
        try:
            response = requests.post(khalti_verify_url, headers=headers, json=payload)
            response_data = response.json()
            logger.debug(f"Khalti verification: status={response.status_code}, body={response_data}")
            if response.status_code == 200 and response_data.get('status', '').lower() == 'completed':
                payment.status = 'Completed'
                payment.transaction_id = transaction_id or response_data.get('transaction_id', f"KH-{payment.id}")
                payment.save()
                course = payment.course
                logger.debug(f"Enrolling user {payment.user.username} in course {course.title}")
                course.students.add(payment.user)
                logger.info(f"User {payment.user.username} enrolled in course {course.title}")
                try:
                    profile = payment.user.profile
                    if profile.role != 'Student':
                        profile.role = 'Student'
                        profile.save()
                except Profile.DoesNotExist:
                    Profile.objects.create(user=payment.user, role='Student')
                Notification.objects.create(
                    user=payment.user,
                    message=f"Payment successful! You are now enrolled in {course.title} - {payment.level.name}.",
                    is_read=False
                )
                messages.success(request, f"Payment successful! You are now enrolled in {course.title} - {payment.level.name}.")
                request.session.pop('payment_id', None)
                request.session.pop('payment_user', None)
                logger.info(f"Payment {payment.id} verified, redirecting to success page")
                return redirect('payment_success_page', payment_id=payment.id)
            else:
                payment.status = response_data.get('status', 'Failed')
                payment.save()
                Notification.objects.create(
                    user=payment.user,
                    message=f"Payment for {payment.course.title} - {payment.level.name} failed or was canceled.",
                    is_read=False
                )
                messages.error(request, f"Payment verification failed: {response_data.get('message', 'Unknown error')}")
                logger.warning(f"Payment {payment.id} verification failed")
                return redirect('payment_failure_page', payment_id=payment_id)
        except requests.RequestException as e:
            logger.error(f"Khalti verification error: {str(e)}")
            payment.status = 'Failed'
            payment.save()
            Notification.objects.create(
                user=payment.user,
                message=f"Payment for {payment.course.title} - {payment.level.name} failed due to an error.",
                is_read=False
            )
            messages.error(request, f"Error verifying payment: {str(e)}")
            return redirect('payment_failure_page', payment_id=payment_id)
             
@never_cache
@login_required
def payment_success_page(request, payment_id):
    logger.debug(f"Accessing payment_success_page: payment_id={payment_id}")
    try:
        payment = get_object_or_404(Payment, id=payment_id)
    except Payment.DoesNotExist:
        logger.error(f"Payment {payment_id} not found")
        messages.error(request, "Payment not found")
        return HttpResponseBadRequest("Payment not found")

    logger.info(f"Payment details: ID={payment.id}, user={payment.user.username}")

    if payment.user != request.user:
        logger.error(f"User mismatch: authenticated={request.user.username}, payment_user={payment.user.username}")
        messages.error(request, "You are not authorized to view this payment.")
        return HttpResponseBadRequest("You are not authorized to view this payment.")

    if payment.status != 'Completed':
        logger.warning(f"Payment {payment_id} status is {payment.status}")
        messages.error(request, f"Payment is not completed. Status: {payment.status}")
        return redirect('payment_failure_page', payment_id=payment_id)

    context = {
        'payment': payment,
        'course_title': payment.course.title if payment.course else 'N/A',
        'level_name': payment.level.name if payment.level else 'N/A',
        'amount': payment.amount or 'N/A',
        'transaction_id': payment.transaction_id or 'N/A',
        'created_at': payment.created_at or 'N/A',
        'payment_user': payment.user.username,
        'current_user': request.user.username,
    }
    logger.info(f"Rendering payment_success.html for payment {payment_id}")
    return render(request, 'payment_success.html', context)

@never_cache
def payment_failure_page(request, payment_id):
    logger.debug(f"Accessing payment_failure_page: payment_id={payment_id}")
    payment = get_object_or_404(Payment, id=payment_id)
    logger.info(f"Payment details: ID={payment.id}, user={payment.user.username}")

    if not request.user.is_authenticated:
        logger.warning(f"Unauthenticated user accessing payment {payment_id}")
        return redirect(f"{settings.LOGIN_URL}?next={request.path}")

    if request.user != payment.user:
        logger.error(f"User mismatch: authenticated={request.user.username}, payment_user={payment.user.username}")
        return HttpResponseBadRequest(f"You are not authorized to view this payment")

    context = {
        'payment': payment,
        'course_title': payment.course.title if payment.course else 'N/A',
        'level_name': payment.level.name if payment.level else 'N/A',
        'amount': payment.amount or 'N/A',
        'transaction_id': payment.transaction_id or 'N/A',
        'created_at': payment.created_at or 'N/A',
    }
    logger.info(f"Rendering payment_failure.html for payment {payment_id}")
    return render(request, 'payment_failure.html', context)

@login_required
def update_profile(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        user = request.user

        try:
            validate_email(email)
            if username != user.username:
                if User.objects.filter(username=username).exclude(id=user.id).exists():
                    messages.error(request, 'This username is already taken.')
                    return redirect('student_dashboard')
            if phone_number:
                phone_pattern = r'^\+?\d{10,15}$'
                if not re.match(phone_pattern, phone_number):
                    messages.error(request, 'Please enter a valid phone number.')
                    return redirect('student_dashboard')
            user.username = username
            user.email = email
            user.profile.phone_number = phone_number if phone_number else None
            user.save()
            user.profile.save()
            messages.success(request, 'Your profile has been updated successfully!')
        except ValidationError:
            messages.error(request, 'Please enter a valid email address.')
        except IntegrityError:
            messages.error(request, 'An error occurred while updating your profile.')
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
        return redirect('student_dashboard')
    return redirect('student_dashboard')

@login_required
def delete_phone_number(request):
    if request.method == 'POST':
        try:
            user = request.user
            user.profile.phone_number = None
            user.profile.save()
            messages.success(request, 'Your phone number has been deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting phone number: {str(e)}')
        return redirect('student_dashboard')
    return redirect('student_dashboard')

@login_required
def download_invoice(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    if request.user != payment.user:
        logger.error(f"Unauthorized invoice download: user={request.user.username}, payment_user={payment.user.username}")
        return HttpResponseBadRequest("You are not authorized to download this invoice")

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=20, spaceAfter=20, textColor=colors.HexColor("#07301f"), alignment=1)
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=12, spaceAfter=10, textColor=colors.black)
    bold_style = ParagraphStyle('Bold', parent=styles['Normal'], fontSize=12, spaceAfter=10, textColor=colors.black, fontName='Helvetica-Bold')

    elements.append(Paragraph("Sungabha Music Academy", title_style))
    elements.append(Paragraph("Payment Invoice", title_style))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Student: {payment.user.username}", normal_style))
    elements.append(Paragraph(f"Email: {payment.user.email or 'Not provided'}", normal_style))
    elements.append(Spacer(1, 12))

    data = [
        ["Description", "Details"],
        ["Course", payment.course.title],
        ["Level", payment.level.name],
        ["Amount", f"NPR {payment.amount}"],
        ["Transaction ID", payment.transaction_id or 'N/A'],
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
    elements.append(Paragraph("Thank you for choosing Sungabha Music Academy!", normal_style))
    elements.append(Paragraph("Contact us: sungabhamusicacademy@gmail.com | Phone: 9867688829", normal_style))
    doc.build(elements)

    buffer.seek(0)
    pdf = buffer.getvalue()
    buffer.close()
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{payment_id}.pdf"'
    response.write(pdf)
    logger.info(f"Invoice downloaded for payment {payment_id} by {request.user.username}")
    return response

@login_required
def course_content_view(request, course_id):
    user = request.user
    logger.debug(f"Accessing course content: course_id={course_id}, user={user.username}")
    if not hasattr(user, 'profile') or user.profile.role != 'Student':
        logger.warning(f"Redirecting: User {user.username} is not a student")
        return redirect('home')

    course = get_object_or_404(Course, id=course_id)
    payment = Payment.objects.filter(user=user, course=course, status='Completed').first()
    if not payment:
        logger.warning(f"Redirecting: No completed payment for user {user.username} in course {course.title}")
        return redirect('student_dashboard')

    contents = CourseContent.objects.filter(course=course)
    if contents.exists():
        total_contents = contents.count()
        progress, created = Progress.objects.get_or_create(user=user, course=course, defaults={'percentage': 0.0})
        if progress.percentage < 100:
            progress.percentage = min(progress.percentage + (100 / total_contents), 100)
            progress.save()
            logger.info(f"Updated progress for {user.username} in {course.title}: {progress.percentage}%")

    context = {
        'course': course,
        'contents': contents,
        'progress': progress.percentage if 'progress' in locals() else 0.0,
    }
    logger.debug(f"Rendering course content: course={course.title}, contents={contents.count()}")
    return render(request, 'course_content.html', context)

@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    if request.method == 'POST':
        notification.is_read = True
        notification.save()
        logger.info(f"Notification {notification_id} marked as read by {request.user.username}")
        messages.success(request, "Notification marked as read.")
    return redirect('student_dashboard')

def about(request):
    context = {'user': request.user}
    return render(request, 'about.html', context)

def team(request):
    context = {'user': request.user}
    return render(request, 'team.html', context)

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        subject = f'Contact Form Submission from {name}'
        body = f'Name: {name}\nEmail: {email}\nMessage: {message}'
        from_email = email
        recipient_list = ['sungabhamusicacademy@gmail.com']
        try:
            send_mail(subject, body, from_email, recipient_list, fail_silently=False)
            messages.success(request, 'Your message has been sent successfully!')
        except Exception as e:
            messages.error(request, 'Failed to send your message. Please try again later.')
        return redirect('contact')
    return render(request, 'contact.html')

def team(request):
    teachers = Teacher.objects.all()
    return render(request, 'team.html', {'teachers': teachers})