# Generated by Django 5.1.6 on 2025-04-06 20:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('music', '0005_remove_course_category_remove_course_description_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='CourseLevel',
        ),
    ]
