# Generated by Django 5.1.6 on 2025-03-30 12:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('music', '0002_alter_course_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='category',
            field=models.CharField(choices=[('Instruments', 'Instruments'), ('Singing', 'Singing'), ('Dancing', 'Dancing')], default='Instruments', max_length=20),
        ),
    ]
