from django.shortcuts import render
from .models import Course

def home(request):
    return render(request, 'home.html')  

def courses_list(request):
    courses = Course.objects.all()  # Fetch all courses
    return render(request, 'courses.html', {'courses': courses})  # Make sure 'courses.html' exists
