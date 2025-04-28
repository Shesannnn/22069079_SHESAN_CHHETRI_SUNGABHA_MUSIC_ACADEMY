from django import forms
from django.contrib.auth import ( 
    authenticate, get_user_model 
) 
from .models import Course
from .models import CourseContent

User = get_user_model()

REGISTER_ROLE_CHOICES = (
    ('student', 'Student'),
    ('teacher', 'Teacher'),
)

class UserLoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self, *args, **kwargs):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise forms.ValidationError("This user does not exist")
            if not user.check_password(password):
                raise forms.ValidationError('Incorrect Password')
            if not user.is_active:
                raise forms.ValidationError("This user is not active")
        return super(UserLoginForm, self).clean(*args, **kwargs)
    
class UserRegisterForm(forms.ModelForm):
    email = forms.EmailField(label='Email Address')
    email2 = forms.EmailField(label='Confirm Email')
    password = forms.CharField(widget=forms.PasswordInput)
    role = forms.ChoiceField(choices=REGISTER_ROLE_CHOICES, required=True)  # <-- Only Teacher and Student

    class Meta:
        model = User
        fields = ['username', 'email', 'email2', 'password', 'role']

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        email2 = cleaned_data.get('email2')

        if email and email2 and email.strip().lower() != email2.strip().lower():
            raise forms.ValidationError("Emails must match")

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already being used")

        return cleaned_data

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'category', 'description', 'image']  # Include the fields you need

class CourseContentForm(forms.ModelForm):
    class Meta:
        model = CourseContent
        fields = ['title', 'content_type', 'file', 'text_content']

    def clean(self):
        cleaned_data = super().clean()
        content_type = cleaned_data.get('content_type')
        file = cleaned_data.get('file')
        text_content = cleaned_data.get('text_content')

        if content_type in ['video', 'document'] and not file:
            raise forms.ValidationError(f"A file is required for {content_type} content.")
        if content_type == 'text' and not text_content:
            raise forms.ValidationError("Text content is required for text type.")
        if content_type in ['video', 'document'] and text_content:
            raise forms.ValidationError(f"Text content should be empty for {content_type} type.")
        if content_type == 'text' and file:
            raise forms.ValidationError("File should be empty for text type.")
        return cleaned_data