from django.shortcuts import render, redirect
from .models import Course
from django.contrib.auth import (
    authenticate,
    get_user_model,
    login,
    logout
)
from .forms import UserLoginForm, UserRegisterForm
from django.shortcuts import get_object_or_404
from .models import HomeCourse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Level, Assignment


def home(request):
    home_courses = HomeCourse.objects.all()
    return render(request, 'home.html', {'home_courses': home_courses})

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

def login_view(request):
    form = UserLoginForm(request.POST or None)
    if form.is_valid():
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            return redirect('home')  # <<<<==== Redirect to homepage after login
    return render(request, 'login.html', {'form': form})



from .models import Profile  # import it

def register_view(request):
    next = request.GET.get('next')
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
        if next:
            return redirect(next)
        return redirect('home')
    
    return render(request, "register.html", {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')

def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    return render(request, 'course_detail.html', {'course': course})

def course_detail_payment(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    return render(request, 'course_detail_payment.html', {'course': course})



def teacher_dashboard_view(request):
    user = request.user

    # Check if the user is logged in and has a "Teacher" role
    if not user.is_authenticated:
        return redirect('login')  # Redirect to login if the user isn't logged in

    # Check if the user has a profile and if their role is "Teacher"
    if not hasattr(user, 'profile') or user.profile.role != 'Teacher':
        return redirect('home')  # Redirect if the user isn't a teacher

    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)  # in case you have file uploads
        if form.is_valid():
            course = form.save(commit=False)
            course.teacher = user  # assign the logged-in teacher
            course.save()
            form.save_m2m()  # Important if your form has ManyToMany fields
            return redirect('teacher_dashboard')
    else:
        form = CourseForm()

    # Filter courses taught by the logged-in teacher
    courses = Course.objects.filter(teacher=user)

    # Get students for each course
    course_students = {course.id: course.students.all() for course in courses}

    # Get assignments related to each course
    course_assignments = {course.id: Assignment.objects.filter(course=course) for course in courses}

    # Get all levels (or you can customize if needed)
    levels = Level.objects.all()

    context = {
        'courses': courses,
        'course_students': course_students,
        'course_assignments': course_assignments,
        'form': form,
        'levels': levels,
    }
    return render(request, 'teacher_dashboard.html', context)

@login_required
def student_dashboard_view(request):
    return render(request, 'student_dashboard.html')

@login_required
def user_dashboard(request):
    role = request.user.profile.role
    if role == 'Teacher':
        return redirect('teacher_dashboard')
    elif role == 'Student':
        return redirect('student_dashboard')
    else:
        return redirect('home')

from .forms import CourseForm




