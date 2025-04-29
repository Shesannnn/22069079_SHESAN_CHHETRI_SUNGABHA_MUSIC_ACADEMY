from django.contrib import admin
from django.contrib.auth.models import User
from .models import Course, Level, Payment, Profile, HomeCourse, Assignment, CourseContent, Certificate, Teacher
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from django.contrib import admin
from .models import CourseContent

@admin.register(CourseContent)
class CourseContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'created_at')
    list_filter = ('course', 'created_at')
    search_fields = ('title', 'text_content')  # Updated to match model fields

    def save_model(self, request, obj, form, change):
        print(f"Saving CourseContent: {obj.title} for course {obj.course.title}")
        try:
            super().save_model(request, obj, form, change)
            print(f"CourseContent saved successfully: {obj.id}")
            # Verify the content exists in the database
            try:
                saved_content = CourseContent.objects.get(id=obj.id)
                print(f"Verified: Content {saved_content.title} (ID: {saved_content.id}) exists in database")
            except CourseContent.DoesNotExist:
                print(f"Error: Content {obj.title} (ID: {obj.id}) was not found in the database after saving")
        except Exception as e:
            print(f"Error saving CourseContent: {str(e)}")
            raise

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ('user', 'course', 'level', 'purchase_order_id', 'amount', 'amount_paisa', 'status', 'created_at', 'updated_at')
    fields = ('user', 'course', 'level', 'amount', 'status', 'created_at', 'updated_at')
    can_delete = False

    def get_queryset(self, request):
        return super().get_queryset(request).filter(status='Completed')

# Course Admin Customization
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'teacher', 'enrolled_students_count')
    list_filter = ('category', 'teacher')
    search_fields = ('title', 'description')
    inlines = [PaymentInline]  # Show enrolled students (completed payments) as an inline table

    def enrolled_students_count(self, obj):
        # Count the number of students who have completed payment for this course
        return Payment.objects.filter(course=obj, status='Completed').count()
    enrolled_students_count.short_description = 'Enrolled Students'

class PaymentInlineForProfile(admin.TabularInline):
    model = Payment
    fk_name = 'user'
    extra = 0
    readonly_fields = ('course', 'level', 'amount', 'status', 'created_at')
    fields = ('course', 'level', 'amount', 'status', 'created_at')
    can_delete = False

    def get_queryset(self, request):
        qs = super().get_queryset(request).filter(status='Completed')
        return qs


# Profile Admin Customization
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'enrolled_courses_count', 'view_payments')
    list_filter = ('role',)
    search_fields = ('user__username',)

    def view_payments(self, obj):
        payments = Payment.objects.filter(user=obj.user, status='Completed')
        if not payments.exists():
            return "No payments"
        
        html = "<ul>"
        for payment in payments:
            html += f"<li>{payment.course.title} - {payment.level.name} - {payment.amount}$ - {payment.status}</li>"
        html += "</ul>"
        return mark_safe(html)
    
    view_payments.short_description = "Payments"

    def enrolled_courses_count(self, obj):
        if obj.role == 'Student':
            return Payment.objects.filter(user=obj.user, status='Completed').count()
        return 0
    enrolled_courses_count.short_description = 'Enrolled Courses'

# Payment Admin Customization
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('purchase_order_id', 'user', 'course', 'level', 'amount', 'status', 'created_at')
    list_filter = ('status', 'course', 'level')
    search_fields = ('user__username', 'course__title', 'purchase_order_id')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')

# Level Admin Customization
@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration', 'enrolled_students_count')
    list_filter = ('name',)
    search_fields = ('name',)

    def enrolled_students_count(self, obj):
        # Count the number of students who have enrolled in this level (completed payments)
        return Payment.objects.filter(level=obj, status='Completed').count()
    enrolled_students_count.short_description = 'Enrolled Students'

# HomeCourse Admin Customization
@admin.register(HomeCourse)
class HomeCourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'order')
    list_filter = ('order',)
    search_fields = ('title',)

# Assignment Admin Customization
@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'due_date')
    list_filter = ('course', 'due_date')
    search_fields = ('title',)

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'issue_date')
    list_filter = ('issue_date', 'course')
    search_fields = ('user__username', 'course__title')
    date_hierarchy = 'issue_date'

    def save_model(self, request, obj, form, change):
        print(f"Issuing certificate for user: {obj.user.username}, course: {obj.course.title}")
        try:
            super().save_model(request, obj, form, change)
            print(f"Certificate issued successfully: {obj.id}")
        except Exception as e:
            print(f"Error issuing certificate: {str(e)}")
            raise

# Jazzmin-specific: Order sections in change form
    jazzmin_section_order = ("General", "Details")
    # Use collapsible form layout
    changeform_format = "collapsible"

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('name', 'role')
    search_fields = ('name', 'role')