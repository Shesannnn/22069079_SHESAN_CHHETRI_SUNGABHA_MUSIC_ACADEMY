from django.shortcuts import render, redirect
from .models import Course
from django.contrib.auth import (
    authenticate,
    get_user_model,
    login,
    logout
)
from .forms import UserLoginForm, UserRegisterForm

def home(request):
    return render(request, 'home.html')  

def courses_list(request):
    category = request.GET.get('category', 'All')  # Get category from query parameters
    if category == 'All':
        courses = Course.objects.all()
    else:
        courses = Course.objects.filter(category=category)

    categories = ['All', 'Instruments', 'Singing', 'Flute']  # Add all possible categories
    return render(request, 'courses.html', {'courses': courses, 'categories': categories, 'selected_category': category})


def login_view(request):
    next = request.GET.get('next')  # Fix 'GET'
    form = UserLoginForm(request.POST or None)
    
    if form.is_valid():
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        
        if user:
            login(request, user)  # Log the user in
            if next:
                return redirect(next)
            return redirect('home')  # Redirect to home after login
    
    context = {'form': form}
    return render(request, "login.html", context)

def register_view(request):
    next = request.GET.get('next')  # Fix 'GET'
    form = UserRegisterForm(request.POST or None)
    
    if form.is_valid():
        user = form.save(commit=False)
        password = form.cleaned_data.get('password')
        user.set_password(password) 
        user.save()
        new_user = authenticate(username=user.username, password=password)
        login(request, new_user)
        if next:
            return redirect(next)
        return redirect('home')  # Redirect to home after login
    
    context = {'form': form}
    return render(request, "register.html", context)

def logout_view(request):
    logout(request)
    return redirect()