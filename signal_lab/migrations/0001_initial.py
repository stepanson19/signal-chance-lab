from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Exercise',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=120)),
                ('slug', models.SlugField(unique=True)),
                ('statement', models.TextField()),
                ('difficulty', models.CharField(choices=[('start', 'Старт'), ('core', 'База'), ('plus', 'Плюс')], default='start', max_length=16)),
                ('answer_kind', models.CharField(choices=[('number', 'Число'), ('text', 'Текст')], default='number', max_length=16)),
                ('correct_numeric_answer', models.FloatField(blank=True, null=True)),
                ('tolerance', models.FloatField(default=0.01)),
                ('correct_text_answer', models.CharField(blank=True, max_length=255)),
                ('hint', models.TextField()),
                ('explanation', models.TextField()),
                ('is_featured', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['topic__order', 'title'],
            },
        ),
        migrations.CreateModel(
            name='Lab',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=120)),
                ('slug', models.SlugField(unique=True)),
                ('summary', models.TextField()),
                ('experiment_type', models.CharField(choices=[('coin', 'Монета'), ('dice', 'Кубик'), ('binomial', 'Биномиальный эксперимент'), ('normal', 'Нормальная выборка')], max_length=24)),
                ('difficulty', models.CharField(choices=[('start', 'Старт'), ('core', 'База'), ('plus', 'Плюс')], default='start', max_length=16)),
                ('estimated_minutes', models.PositiveSmallIntegerField(default=10)),
                ('theory_hint', models.TextField(blank=True)),
                ('is_featured', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['topic__order', 'title'],
            },
        ),
        migrations.CreateModel(
            name='Topic',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=120)),
                ('slug', models.SlugField(unique=True)),
                ('short_description', models.CharField(max_length=255)),
                ('theory_summary', models.TextField()),
                ('intuition_text', models.TextField()),
                ('formula_text', models.CharField(max_length=255)),
                ('common_mistake', models.TextField()),
                ('accent_color', models.CharField(default='#1d4ed8', max_length=7)),
                ('order', models.PositiveSmallIntegerField(default=1)),
            ],
            options={
                'ordering': ['order', 'title'],
            },
        ),
        migrations.CreateModel(
            name='PracticeAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_key', models.CharField(db_index=True, max_length=40)),
                ('submitted_answer', models.CharField(max_length=255)),
                ('is_correct', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('exercise', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attempts', to='signal_lab.exercise')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='LabRun',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_key', models.CharField(db_index=True, max_length=40)),
                ('parameters_json', models.JSONField(default=dict)),
                ('observed_value', models.FloatField()),
                ('expected_value', models.FloatField()),
                ('deviation_value', models.FloatField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('lab', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='runs', to='signal_lab.lab')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddField(
            model_name='lab',
            name='topic',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='labs', to='signal_lab.topic'),
        ),
        migrations.AddField(
            model_name='exercise',
            name='related_lab',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='exercises', to='signal_lab.lab'),
        ),
        migrations.AddField(
            model_name='exercise',
            name='topic',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exercises', to='signal_lab.topic'),
        ),
    ]
