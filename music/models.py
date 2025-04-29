from django.db import models
from django.contrib.auth.models import User
import uuid

# Profile model to handle user roles (Student, Teacher)
class Profile(models.Model):
    ROLE_CHOICES = (
        ('Student', 'Student'),
        ('Teacher', 'Teacher'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone_number = models.CharField(max_length=15, blank=True, null=True)  # Phone number

    def __str__(self):
        return f"{self.user.username} - {self.role}"

# HomeCourse model (Featured courses for the homepage)
class HomeCourse(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='home_courses/')
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['order']

# Level model (Represents difficulty levels for courses)
class Level(models.Model):
    LEVEL_CHOICES = [
        ('Foundation', 'Foundation'),
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    ]
    
    name = models.CharField(max_length=100, choices=LEVEL_CHOICES)
    description = models.TextField(default="No description available")
    duration = models.IntegerField(default=0, help_text="Duration in months")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, help_text="Price in Rs")
    language = models.CharField(max_length=50, default="English")
    format = models.CharField(max_length=100, default="1:1 lesson with Teacher")
    access = models.CharField(max_length=100, default="Mobile & Desktop Access")
    certificate = models.CharField(max_length=100, default="On completion")
    highlights = models.TextField(default="", blank=True)

    def __str__(self):
        return self.name

# Course model (Represents different courses)
class Course(models.Model):
    CATEGORY_CHOICES = [
        ('Instruments', 'Instruments'),
        ('Singing', 'Singing'),
        ('Flute', 'Flute'),
    ]

    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Instruments')
    description = models.TextField(default="No description available")
    image = models.ImageField(upload_to='course_images/', blank=True, null=True)
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='taught_courses',
        limit_choices_to={'profile__role': 'Teacher'},
    )
    students = models.ManyToManyField(
        User,
        related_name='enrolled_courses',
        blank=True,
        limit_choices_to={'profile__role': 'Student'},
    )
    levels = models.ManyToManyField(Level, related_name='courses', blank=True)

    def __str__(self):
        return self.title

class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateField()

    def __str__(self):
        return self.title

# New model for assignment submissions
class AssignmentSubmission(models.Model):
    STATUS_CHOICES = (
        ('Not Started', 'Not Started'),
        ('In Progress', 'In Progress'),
        ('Submitted', 'Submitted'),
        ('Completed', 'Completed'),
    )

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='assignment_submissions',
        limit_choices_to={'profile__role': 'Student'},
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Not Started')
    submission_file = models.FileField(upload_to='assignment_submissions/', blank=True, null=True)
    submission_text = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('assignment', 'student')  # Ensure one submission per student per assignment

    def __str__(self):
        return f"{self.student.username} - {self.assignment.title} - {self.status}"

# Payment model (For handling course payments)
class Payment(models.Model):
    STATUS_CHOICES = (
        ('Initiated', 'Initiated'),
        ('Completed', 'Completed'),
        ('Pending', 'Pending'),
        ('User canceled', 'User canceled'),
        ('Expired', 'Expired'),
        ('Refunded', 'Refunded'),
        ('Partially Refunded', 'Partially Refunded'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payments',
        limit_choices_to={'profile__role': 'Student'},
        default=1
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='payments')
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name='payments')
    purchase_order_id = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    purchase_order_name = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount in Rs")
    amount_paisa = models.IntegerField(help_text="Amount in paisa (for Khalti)")
    pidx = models.CharField(max_length=100, null=True, blank=True)
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Initiated')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.purchase_order_id} - {self.status}"

from django.db import models
from django.contrib.auth.models import User

class CourseContent(models.Model):
    CONTENT_TYPES = (
        ('video', 'Video'),
        ('document', 'Document'),
        ('text', 'Text'),
    )

    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='contents')
    title = models.CharField(max_length=200)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    file = models.FileField(upload_to='course_content/', blank=True, null=True)
    text_content = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.content_type}) for {self.course.title}"


class Certificate(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='certificates',
        limit_choices_to={'profile__role': 'Student'}
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='certificates'
    )
    issue_date = models.DateField(auto_now_add=True)
    certificate_file = models.FileField(
        upload_to='certificates/',
        blank=True,
        null=True,
        help_text="Upload a PDF certificate (optional)."
    )

    def __str__(self):
        return f"Certificate for {self.user.username} - {self.course.title}"

class Progress(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='progress',
        limit_choices_to={'profile__role': 'Student'}
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='progress'
    )
    percentage = models.FloatField(default=0.0, help_text="Progress percentage (0-100)")
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.course.title} - {self.percentage}%"

class Notification(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message}"

class Teacher(models.Model):
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=100)  # e.g., Vocal Coach, Guitar Instructor
    bio = models.TextField()
    picture = models.ImageField(upload_to='teachers/', blank=True, null=True)  # Stores the teacher’s picture

    def __str__(self):
        return self.name