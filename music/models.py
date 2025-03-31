from django.db import models

class Course(models.Model):
    CATEGORY_CHOICES = [
        ('Instruments', 'Instruments'),
        ('Singing', 'Singing'),
        ('Flute', 'Flute'),  # Add more categories if needed
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(default="No description available")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='course_images/', blank=True, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='Instruments')  # Add Category field

    def __str__(self):
        return self.title
