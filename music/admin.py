from django.contrib import admin
from .models import Course

class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'price')  # Display fields in admin
    list_filter = ('category',)  # Filter courses by category

admin.site.register(Course, CourseAdmin)


