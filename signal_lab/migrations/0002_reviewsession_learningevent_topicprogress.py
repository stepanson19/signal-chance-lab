from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('signal_lab', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReviewSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_key', models.CharField(db_index=True, max_length=40)),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('exercises_seen', models.PositiveIntegerField(default=0)),
                ('exercises_correct', models.PositiveIntegerField(default=0)),
                ('topic', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='review_sessions', to='signal_lab.topic')),
            ],
            options={
                'ordering': ['-started_at'],
            },
        ),
        migrations.CreateModel(
            name='LearningEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_key', models.CharField(db_index=True, max_length=40)),
                ('event_type', models.CharField(choices=[('lab_run', 'Запуск лаборатории'), ('wrong_answer', 'Неверный ответ'), ('correct_answer', 'Верный ответ'), ('mastery_up', 'Рост mastery'), ('review_completed', 'Повтор завершен')], max_length=32)),
                ('title', models.CharField(max_length=120)),
                ('details', models.TextField(blank=True)),
                ('delta', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('topic', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='learning_events', to='signal_lab.topic')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='TopicProgress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_key', models.CharField(db_index=True, max_length=40)),
                ('mastery_score', models.PositiveSmallIntegerField(default=0)),
                ('exercises_attempted', models.PositiveIntegerField(default=0)),
                ('exercises_correct', models.PositiveIntegerField(default=0)),
                ('labs_completed', models.PositiveIntegerField(default=0)),
                ('current_streak', models.PositiveIntegerField(default=0)),
                ('last_activity_at', models.DateTimeField(auto_now=True)),
                ('topic', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='progress_entries', to='signal_lab.topic')),
            ],
            options={
                'ordering': ['topic__order', '-last_activity_at'],
                'unique_together': {('topic', 'session_key')},
            },
        ),
    ]
