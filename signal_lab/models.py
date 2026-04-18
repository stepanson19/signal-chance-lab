from django.db import models
from django.urls import reverse


class Topic(models.Model):
    title = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    short_description = models.CharField(max_length=255)
    theory_summary = models.TextField()
    intuition_text = models.TextField()
    formula_text = models.CharField(max_length=255)
    common_mistake = models.TextField()
    accent_color = models.CharField(max_length=7, default="#1d4ed8")
    order = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["order", "title"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("signal_lab:topic_detail", args=[self.slug])


class Lab(models.Model):
    class ExperimentType(models.TextChoices):
        COIN = "coin", "Монета"
        DICE = "dice", "Кубик"
        BINOMIAL = "binomial", "Биномиальный эксперимент"
        NORMAL = "normal", "Нормальная выборка"

    class Difficulty(models.TextChoices):
        START = "start", "Старт"
        CORE = "core", "База"
        PLUS = "plus", "Плюс"

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="labs")
    title = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    summary = models.TextField()
    experiment_type = models.CharField(
        max_length=24,
        choices=ExperimentType.choices,
    )
    difficulty = models.CharField(
        max_length=16,
        choices=Difficulty.choices,
        default=Difficulty.START,
    )
    estimated_minutes = models.PositiveSmallIntegerField(default=10)
    theory_hint = models.TextField(blank=True)
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ["topic__order", "title"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("signal_lab:lab_detail", args=[self.slug])


class Exercise(models.Model):
    class AnswerKind(models.TextChoices):
        NUMBER = "number", "Число"
        TEXT = "text", "Текст"

    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name="exercises",
    )
    related_lab = models.ForeignKey(
        Lab,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="exercises",
    )
    title = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    statement = models.TextField()
    difficulty = models.CharField(
        max_length=16,
        choices=Lab.Difficulty.choices,
        default=Lab.Difficulty.START,
    )
    answer_kind = models.CharField(
        max_length=16,
        choices=AnswerKind.choices,
        default=AnswerKind.NUMBER,
    )
    correct_numeric_answer = models.FloatField(null=True, blank=True)
    tolerance = models.FloatField(default=0.01)
    correct_text_answer = models.CharField(max_length=255, blank=True)
    hint = models.TextField()
    explanation = models.TextField()
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ["topic__order", "title"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("signal_lab:exercise_detail", args=[self.slug])


class LabRun(models.Model):
    lab = models.ForeignKey(Lab, on_delete=models.CASCADE, related_name="runs")
    session_key = models.CharField(max_length=40, db_index=True)
    parameters_json = models.JSONField(default=dict)
    observed_value = models.FloatField()
    expected_value = models.FloatField()
    deviation_value = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class PracticeAttempt(models.Model):
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    session_key = models.CharField(max_length=40, db_index=True)
    submitted_answer = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class TopicProgress(models.Model):
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name="progress_entries",
    )
    session_key = models.CharField(max_length=40, db_index=True)
    mastery_score = models.PositiveSmallIntegerField(default=0)
    exercises_attempted = models.PositiveIntegerField(default=0)
    exercises_correct = models.PositiveIntegerField(default=0)
    labs_completed = models.PositiveIntegerField(default=0)
    current_streak = models.PositiveIntegerField(default=0)
    last_activity_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["topic__order", "-last_activity_at"]
        unique_together = ["topic", "session_key"]


class LearningEvent(models.Model):
    class EventType(models.TextChoices):
        LAB_RUN = "lab_run", "Запуск лаборатории"
        WRONG_ANSWER = "wrong_answer", "Неверный ответ"
        CORRECT_ANSWER = "correct_answer", "Верный ответ"
        MASTERY_UP = "mastery_up", "Рост mastery"
        REVIEW_COMPLETED = "review_completed", "Повтор завершен"

    session_key = models.CharField(max_length=40, db_index=True)
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name="learning_events",
    )
    event_type = models.CharField(max_length=32, choices=EventType.choices)
    title = models.CharField(max_length=120)
    details = models.TextField(blank=True)
    delta = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class ReviewSession(models.Model):
    session_key = models.CharField(max_length=40, db_index=True)
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name="review_sessions",
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    exercises_seen = models.PositiveIntegerField(default=0)
    exercises_correct = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-started_at"]
