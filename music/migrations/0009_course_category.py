# Generated by Django 5.1.6 on 2025-04-06 21:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('music', '0008_course_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='category',
            field=models.CharField(choices=[('Instruments', 'Instruments'), ('Singing', 'Singing'), ('Flute', 'Flute')], default='Instruments', max_length=50),
        ),
    ]
