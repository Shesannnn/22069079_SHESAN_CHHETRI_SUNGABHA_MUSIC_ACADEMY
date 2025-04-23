from django.contrib import admin
from .models import Course, Level, HomeCourse, Profile

# Admin for HomeCourse
@admin.register(HomeCourse)
class HomeCourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'order', 'image']
    list_editable = ['order']
    search_fields = ('title',)

# Admin for Level
class LevelAdmin(admin.ModelAdmin):
    list_display = ('name', 'duration', 'description', 'price', 'language', 'format', 'access', 'certificate')  # Display these fields
    search_fields = ('name', 'description')  # Enable search by name and description

# Admin for Course
class CourseAdmin(admin.ModelAdmin):
    fields = ('title', 'category', 'description', 'teacher', 'image', 'students', 'levels')
    list_display = ('title', 'get_levels', 'description', 'image', 'teacher')  # Include teacher
    search_fields = ('title', 'description')
    filter_horizontal = ('levels',)
    list_filter = ('category',)
    list_editable = ('description',)
    list_display_links = ('title',)  # Make title clickable for easy navigation

    def get_levels(self, obj):
        return ", ".join([level.name for level in obj.levels.all()])
    get_levels.short_description = 'Levels'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Make the 'teacher' field required in the admin form
        form.base_fields['teacher'].required = True
        return form

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')  # Display the username and role
    search_fields = ('user__username',)  # Make the username searchable

# Register the models with their respective admin configurations
admin.site.register(Level, LevelAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Profile, ProfileAdmin)

