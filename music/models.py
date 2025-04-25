from django.db import models
from django.contrib.auth.models import User

# Profile model to handle user roles (Student, Teacher)
class Profile(models.Model):
    ROLE_CHOICES = (
        ('Student', 'Student'),
        ('Teacher', 'Teacher'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return self.user.username

# HomeCourse model (This seems to be featured courses for the homepage)
class HomeCourse(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='home_courses/')
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['order']



def get_default_course():
    # Fetch the first available course
    default_course = Course.objects.first()  # or use another criteria to pick a default
    return default_course if default_course else None  # In case no courses are available

class Level(models.Model):
    LEVEL_CHOICES = [
        ('Foundation', 'Foundation'),
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    ]
    
    name = models.CharField(max_length=100, choices=LEVEL_CHOICES)
    description = models.TextField(default="No description available")
    duration = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    language = models.CharField(max_length=50, default="English")
    format = models.CharField(max_length=100, default="1:1 lesson with Teacher")
    access = models.CharField(max_length=100, default="Mobile & Desktop Access")
    certificate = models.CharField(max_length=100, default="On completion")
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='course_levels', null=True, blank=True)

    highlights = models.TextField(default="")

    def __str__(self):
        return self.name


    
# Course model (Represents different courses)
class Course(models.Model):
    CATEGORY_CHOICES = [
        ('Instruments', 'Instruments'),
        ('Singing', 'Singing'),
        ('Flute', 'Flute'),  # Add more categories if needed
    ]

    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Instruments')
    description = models.TextField(default="No description available")
    image = models.ImageField(upload_to='course_images/', blank=True, null=True)
    
    # ForeignKey to User as the teacher of the course
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='courses')  
    
    # Many-to-many relationship between students and courses
    students = models.ManyToManyField(User, related_name='enrolled_courses')

    # Many-to-many relationship between courses and levels
    levels = models.ManyToManyField(Level, related_name='courses', blank=True)
    
    def __str__(self):
        return self.title

    
# Assignment model (For course-related assignments)
class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateField()

    def __str__(self):
        return self.title

