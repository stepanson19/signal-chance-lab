from django.conf import settings
from django.urls import reverse

from signal_lab.models import Lab, LabRun, PracticeAttempt, Topic, TopicProgress
from signal_lab.services.events import log_learning_event


def recompute_topic_progress(session_key, topic):
    if settings.READ_ONLY_DEMO:
        return None
    attempts = PracticeAttempt.objects.filter(
        session_key=session_key,
        exercise__topic=topic,
    ).order_by("-created_at")
    runs = LabRun.objects.filter(
        session_key=session_key,
        lab__topic=topic,
    ).order_by("-created_at")

    previous_progress = TopicProgress.objects.filter(
        session_key=session_key,
        topic=topic,
    ).first()
    previous_score = previous_progress.mastery_score if previous_progress else 0

    exercises_attempted = attempts.count()
    exercises_correct = attempts.filter(is_correct=True).count()
    labs_completed = runs.values("lab_id").distinct().count()
    current_streak = _count_correct_streak(attempts)
    mastery_score = _calculate_mastery_score(
        exercises_attempted=exercises_attempted,
        exercises_correct=exercises_correct,
        labs_completed=labs_completed,
        current_streak=current_streak,
        latest_attempt=attempts.first(),
    )

    progress, _ = TopicProgress.objects.update_or_create(
        session_key=session_key,
        topic=topic,
        defaults={
            "mastery_score": mastery_score,
            "exercises_attempted": exercises_attempted,
            "exercises_correct": exercises_correct,
            "labs_completed": labs_completed,
            "current_streak": current_streak,
        },
    )

    delta = mastery_score - previous_score
    if delta > 0:
        log_learning_event(
            session_key=session_key,
            topic=topic,
            event_type="mastery_up",
            title=f"Тема {topic.title} укрепилась",
            details="Mastery вырос после нового действия в теме.",
            delta=delta,
        )
    return progress


def build_progress_snapshot(session_key):
    attempts = PracticeAttempt.objects.filter(
        session_key=session_key,
    ).select_related("exercise__topic")
    runs = LabRun.objects.filter(session_key=session_key).select_related("lab__topic")

    active_topic_ids = set(
        attempts.values_list("exercise__topic_id", flat=True)
    ) | set(
        runs.values_list("lab__topic_id", flat=True)
    )
    progress_entries = []
    if active_topic_ids:
        topics = Topic.objects.filter(id__in=active_topic_ids)
        progress_entries = [
            recompute_topic_progress(session_key, topic)
            for topic in topics
        ]

    total_attempts = attempts.count()
    correct_attempts = attempts.filter(is_correct=True).count()
    accuracy = 0.0
    if total_attempts:
        accuracy = round((correct_attempts / total_attempts) * 100, 1)

    weakest_topic = None
    strongest_topic = None
    if progress_entries:
        weakest_topic = min(
            progress_entries,
            key=lambda item: (item.mastery_score, item.topic.order),
        ).topic
        strongest_topic = max(
            progress_entries,
            key=lambda item: (item.mastery_score, -item.topic.order),
        ).topic

    recommended_lab = _pick_recommended_lab(weakest_topic)
    if recommended_lab is None:
        recommended_lab = Lab.objects.filter(is_featured=True).select_related("topic").first()
    recommendation = _build_recommendation(
        weakest_topic=weakest_topic,
        progress_entries=progress_entries,
        fallback_lab=recommended_lab,
    )

    achievements = []
    if runs.exists():
        achievements.append("Первый эксперимент")
    if correct_attempts >= 1:
        achievements.append("Первое верное решение")
    if _count_correct_streak(attempts) >= 3:
        achievements.append("Серия из трёх")

    return {
        "total_attempts": total_attempts,
        "correct_attempts": correct_attempts,
        "accuracy": accuracy,
        "recent_runs": runs[:5],
        "weakest_topic": weakest_topic,
        "strongest_topic": strongest_topic,
        "recommended_lab": recommended_lab,
        "recommendation": recommendation,
        "topic_progress": progress_entries,
        "achievements": achievements,
        "streak_length": _count_correct_streak(attempts),
    }


def _count_correct_streak(attempts):
    streak = 0
    for attempt in attempts.order_by("-created_at"):
        if not attempt.is_correct:
            break
        streak += 1
    return streak


def _pick_recommended_lab(topic):
    if topic is None:
        return None
    return (
        topic.labs.filter(is_featured=True).first()
        or topic.labs.first()
    )


def _build_recommendation(*, weakest_topic, progress_entries, fallback_lab):
    if weakest_topic is None:
        if fallback_lab is None:
            return {
                "target_kind": "lab",
                "title": "Начните с любой лаборатории",
                "reason": "Система ещё не собрала достаточно данных о вашем прогрессе.",
                "url": "",
            }
        return {
            "target_kind": "lab",
            "title": fallback_lab.title,
            "reason": "Сначала нужен хотя бы один эксперимент, чтобы построить маршрут.",
            "url": fallback_lab.get_absolute_url(),
        }

    weakest_progress = next(
        (
            item
            for item in progress_entries
            if item.topic_id == weakest_topic.id
        ),
        None,
    )
    if weakest_progress is None:
        return {
            "target_kind": "lab",
            "title": "Откройте лабораторию",
            "reason": "Нужно собрать больше данных по теме.",
            "url": fallback_lab.get_absolute_url() if fallback_lab else "",
        }

    featured_lab = _pick_recommended_lab(weakest_topic)
    if weakest_progress.labs_completed == 0 and featured_lab is not None:
        return {
            "target_kind": "lab",
            "title": featured_lab.title,
            "reason": (
                f"Тема «{weakest_topic.title}» проседает, а лаборатория по ней ещё не была "
                "пройдена. Сначала закрепите интуицию через эксперимент."
            ),
            "url": featured_lab.get_absolute_url(),
        }

    if weakest_progress.exercises_attempted >= 2 and weakest_progress.current_streak == 0:
        return {
            "target_kind": "review",
            "title": f"Повтор по теме «{weakest_topic.title}»",
            "reason": (
                f"По теме «{weakest_topic.title}» накопились ошибки без серии исправлений. "
                "Лучше пройти короткий review-цикл."
            ),
            "url": reverse("signal_lab:review_topic", args=[weakest_topic.slug]),
        }

    next_exercise = weakest_topic.exercises.first()
    if next_exercise is not None:
        return {
            "target_kind": "exercise",
            "title": next_exercise.title,
            "reason": (
                f"У темы «{weakest_topic.title}» низкий mastery. Следующий шаг — короткая "
                "проверка понимания через практику."
            ),
            "url": next_exercise.get_absolute_url(),
        }

    return {
        "target_kind": "lab",
        "title": featured_lab.title if featured_lab else "Следующая лаборатория",
        "reason": f"Тема «{weakest_topic.title}» остаётся самой слабой по текущим данным.",
        "url": featured_lab.get_absolute_url() if featured_lab else "",
    }


def _calculate_mastery_score(
    *,
    exercises_attempted,
    exercises_correct,
    labs_completed,
    current_streak,
    latest_attempt,
):
    if exercises_attempted == 0 and labs_completed == 0:
        return 0

    accuracy_component = 0
    if exercises_attempted:
        accuracy_component = (exercises_correct / exercises_attempted) * 55

    practice_component = min(exercises_attempted * 7, 21)
    lab_component = min(labs_completed * 14, 28)
    streak_component = min(current_streak * 4, 12)
    correction_bonus = 0
    if latest_attempt is not None and latest_attempt.is_correct and exercises_attempted > 1:
        correction_bonus = 8

    return min(
        100,
        round(
            accuracy_component
            + practice_component
            + lab_component
            + streak_component
            + correction_bonus
        ),
    )
