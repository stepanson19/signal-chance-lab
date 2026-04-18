from django.urls import reverse
from django.utils import timezone

from signal_lab.models import Exercise, LearningEvent, PracticeAttempt, ReviewSession, Topic
from signal_lab.services.events import log_learning_event
from signal_lab.services.progress import build_progress_snapshot, recompute_topic_progress


def build_review_session(session_key, topic_slug=None):
    snapshot = build_progress_snapshot(session_key)
    topic = _resolve_topic(snapshot=snapshot, topic_slug=topic_slug)

    open_session = ReviewSession.objects.filter(
        session_key=session_key,
        topic=topic,
        completed_at__isnull=True,
    ).first()
    if open_session is None:
        open_session = ReviewSession.objects.create(
            session_key=session_key,
            topic=topic,
        )

    exercises = _pick_review_exercises(session_key, topic)
    return {
        "topic": topic,
        "exercises": exercises,
        "review_session": open_session,
        "history_url": reverse("signal_lab:history"),
    }


def complete_review_session(*, review_session, correct_answers, total_answers):
    previous_progress = recompute_topic_progress(
        review_session.session_key,
        review_session.topic,
    )
    before_score = previous_progress.mastery_score

    review_session.exercises_seen = total_answers
    review_session.exercises_correct = correct_answers
    review_session.completed_at = timezone.now()
    review_session.save(
        update_fields=[
            "exercises_seen",
            "exercises_correct",
            "completed_at",
        ]
    )

    after_progress = recompute_topic_progress(
        review_session.session_key,
        review_session.topic,
    )
    mastery_delta = after_progress.mastery_score - before_score
    log_learning_event(
        session_key=review_session.session_key,
        topic=review_session.topic,
        event_type=LearningEvent.EventType.REVIEW_COMPLETED,
        title=f"Повтор по теме {review_session.topic.title} завершён",
        details="Короткий review-цикл сохранён в истории обучения.",
        delta=mastery_delta,
    )
    return {
        "mastery_delta": mastery_delta,
        "topic": review_session.topic,
        "correct_answers": correct_answers,
        "total_answers": total_answers,
    }


def _resolve_topic(*, snapshot, topic_slug):
    if topic_slug:
        return Topic.objects.get(slug=topic_slug)
    if snapshot["weakest_topic"] is not None:
        return snapshot["weakest_topic"]
    return Topic.objects.order_by("order").first()


def _pick_review_exercises(session_key, topic):
    failed_ids = list(
        PracticeAttempt.objects.filter(
            session_key=session_key,
            exercise__topic=topic,
            is_correct=False,
        )
        .values_list("exercise_id", flat=True)
        .distinct()
    )
    failed_exercises = list(
        Exercise.objects.filter(id__in=failed_ids).select_related("topic")[:3]
    )
    if failed_exercises:
        return failed_exercises
    return list(
        topic.exercises.all()[:3]
    )
