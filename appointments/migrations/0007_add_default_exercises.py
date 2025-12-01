from django.db import migrations

def create_exercises(apps, schema_editor):
    Exercise = apps.get_model('appointments', 'Exercise')
    exercises = [
        {
            'name': 'Chest Workout',
            'category': 'strength',
            'description': 'Exercises targeting chest muscles including bench press, push-ups, and flyes.'
        },
        {
            'name': 'Shoulder Workout',
            'category': 'strength',
            'description': 'Exercises targeting shoulder muscles including military press, lateral raises, and front raises.'
        },
        {
            'name': 'Back Workout',
            'category': 'strength',
            'description': 'Exercises targeting back muscles including pull-ups, rows, and lat pulldowns.'
        },
        {
            'name': 'Biceps and Triceps Workout',
            'category': 'strength',
            'description': 'Exercises targeting arm muscles including curls and extensions.'
        },
        {
            'name': 'Whole Body Workout',
            'category': 'strength',
            'description': 'Full body workout combining exercises for all major muscle groups.'
        },
        {
            'name': 'Legs Workout',
            'category': 'strength',
            'description': 'Exercises targeting leg muscles including squats, lunges, and leg press.'
        },
    ]
    
    for exercise_data in exercises:
        Exercise.objects.create(**exercise_data)

def remove_exercises(apps, schema_editor):
    Exercise = apps.get_model('appointments', 'Exercise')
    Exercise.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('appointments', '0006_userprogress_personalbest'),
    ]

    operations = [
        migrations.RunPython(create_exercises, remove_exercises),
    ]
