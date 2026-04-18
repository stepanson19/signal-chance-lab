import secrets

from django.conf import settings
from django.db.models import Count
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render

from signal_lab.forms import (
    ExerciseAnswerForm,
    ExerciseForm,
    LabSimulationForm,
    TopicForm,
)
from signal_lab.models import Exercise, Lab, LabRun, LearningEvent, PracticeAttempt, Topic
from signal_lab.services.events import log_learning_event
from signal_lab.services.lab_experience import build_lab_experience, decorate_lab_result
from signal_lab.services.progress import build_progress_snapshot, recompute_topic_progress
from signal_lab.services.review import build_review_session, complete_review_session
from signal_lab.services.simulation import run_simulation


def _get_session_key(request):
    if settings.READ_ONLY_DEMO:
        session_key = request.session.get("demo_session_key")
        if not session_key:
            session_key = secrets.token_hex(16)
            request.session["demo_session_key"] = session_key
            request.session.modified = True
        return session_key
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def home(request):
    session_key = _get_session_key(request)
    featured_labs = Lab.objects.filter(is_featured=True).select_related("topic")[:3]
    topics = Topic.objects.annotate(
        lab_count=Count("labs", distinct=True),
        exercise_count=Count("exercises", distinct=True),
    )
    snapshot = build_progress_snapshot(session_key)
    context = {
        "featured_labs": featured_labs,
        "topics": topics,
        "snapshot": snapshot,
        "history_preview": _history_preview(session_key),
    }
    return render(request, "signal_lab/home.html", context)


def lab_list(request):
    labs = Lab.objects.select_related("topic").all()
    selected_topic = request.GET.get("topic", "")
    selected_difficulty = request.GET.get("difficulty", "")
    if selected_topic:
        labs = labs.filter(topic__slug=selected_topic)
    if selected_difficulty:
        labs = labs.filter(difficulty=selected_difficulty)
    context = {
        "labs": labs,
        "topics": Topic.objects.all(),
        "difficulty_choices": Lab.Difficulty.choices,
        "selected_topic": selected_topic,
        "selected_difficulty": selected_difficulty,
    }
    return render(request, "signal_lab/lab_list.html", context)


def lab_detail(request, slug):
    lab = get_object_or_404(Lab.objects.select_related("topic"), slug=slug)
    experience = build_lab_experience(lab)
    result = None
    next_step = None
    form = LabSimulationForm(request.POST or None, lab=lab)
    if request.method == "POST" and form.is_valid():
        session_key = _get_session_key(request)
        parameters = {
            **form.cleaned_parameters(),
            **experience["fixed_parameters"],
        }
        result = decorate_lab_result(run_simulation(lab.experiment_type, parameters))
        if not settings.READ_ONLY_DEMO:
            LabRun.objects.create(
                lab=lab,
                session_key=session_key,
                parameters_json=parameters,
                observed_value=result["observed_value"],
                expected_value=result["expected_value"],
                deviation_value=result["deviation"],
            )
            log_learning_event(
                session_key=session_key,
                topic=lab.topic,
                event_type=LearningEvent.EventType.LAB_RUN,
                title=f"Эксперимент «{lab.title}» завершён",
                details="Результат добавлен в учебную историю.",
            )
            recompute_topic_progress(session_key, lab.topic)
        next_step = _build_topic_next_step(session_key, lab.topic)

    context = {
        "lab": lab,
        "experience": experience,
        "form": form,
        "result": result,
        "next_step": next_step,
    }
    return render(request, "signal_lab/lab_detail.html", context)


def exercise_list(request):
    exercises = Exercise.objects.select_related("topic", "related_lab").all()
    selected_topic = request.GET.get("topic", "")
    selected_difficulty = request.GET.get("difficulty", "")
    if selected_topic:
        exercises = exercises.filter(topic__slug=selected_topic)
    if selected_difficulty:
        exercises = exercises.filter(difficulty=selected_difficulty)
    return render(
        request,
        "signal_lab/exercise_list.html",
        {
            "exercises": exercises,
            "topics": Topic.objects.all(),
            "difficulty_choices": Lab.Difficulty.choices,
            "selected_topic": selected_topic,
            "selected_difficulty": selected_difficulty,
        },
    )


def exercise_detail(request, slug):
    exercise = get_object_or_404(
        Exercise.objects.select_related("topic", "related_lab"),
        slug=slug,
    )
    verdict = None
    form = ExerciseAnswerForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        session_key = _get_session_key(request)
        answer = form.cleaned_data["answer"]
        is_correct = _check_exercise_answer(exercise, answer)
        if not settings.READ_ONLY_DEMO:
            PracticeAttempt.objects.create(
                exercise=exercise,
                session_key=session_key,
                submitted_answer=answer,
                is_correct=is_correct,
            )
            log_learning_event(
                session_key=session_key,
                topic=exercise.topic,
                event_type=(
                    LearningEvent.EventType.CORRECT_ANSWER
                    if is_correct
                    else LearningEvent.EventType.WRONG_ANSWER
                ),
                title=(
                    f"Верный ответ по теме {exercise.topic.title}"
                    if is_correct
                    else f"Ошибка в теме {exercise.topic.title}"
                ),
                details="Результат задачи сохранён в истории.",
            )
            recompute_topic_progress(session_key, exercise.topic)
        verdict = {
            "title": "Верно" if is_correct else "Пока мимо",
            "message": exercise.explanation if is_correct else exercise.hint,
            "is_correct": is_correct,
        }

    context = {
        "exercise": exercise,
        "form": form,
        "verdict": verdict,
        "next_step": _build_topic_next_step(_get_session_key(request), exercise.topic),
    }
    return render(request, "signal_lab/exercise_detail.html", context)


def topic_detail(request, slug):
    topic = get_object_or_404(
        Topic.objects.prefetch_related("labs", "exercises"),
        slug=slug,
    )
    return render(request, "signal_lab/topic_detail.html", {"topic": topic})


def dashboard(request):
    snapshot = build_progress_snapshot(_get_session_key(request))
    context = {
        "snapshot": snapshot,
        "history_preview": _history_preview(_get_session_key(request)),
    }
    return render(request, "signal_lab/dashboard.html", context)


def history(request):
    session_key = _get_session_key(request)
    events = (
        LearningEvent.objects.filter(session_key=session_key)
        .select_related("topic")
        .order_by("-created_at")
    )
    return render(request, "signal_lab/history.html", {"events": events})


def review_home(request):
    session_key = _get_session_key(request)
    snapshot = build_progress_snapshot(session_key)
    return render(
        request,
        "signal_lab/review_home.html",
        {
            "snapshot": snapshot,
            "history_preview": _history_preview(session_key),
        },
    )


def review_topic(request, slug):
    payload = build_review_session(_get_session_key(request), topic_slug=slug)
    summary = None
    if request.method == "POST":
        total_answers = len(payload["exercises"])
        correct_answers = total_answers
        if settings.READ_ONLY_DEMO:
            summary = {
                "mastery_delta": 0,
                "topic": payload["topic"],
                "correct_answers": correct_answers,
                "total_answers": total_answers,
            }
        else:
            summary = complete_review_session(
                review_session=payload["review_session"],
                correct_answers=correct_answers,
                total_answers=total_answers,
            )
    return render(
        request,
        "signal_lab/review_detail.html",
        {
            "payload": payload,
            "summary": summary,
        },
    )


def content_manage(request):
    context = {
        "topics": Topic.objects.all(),
        "exercises": Exercise.objects.select_related("topic")[:10],
    }
    return render(request, "signal_lab/content_manage.html", context)


def topic_create(request):
    if settings.READ_ONLY_DEMO and request.method == "POST":
        return HttpResponse("Демо-режим не сохраняет изменения.", status=403)
    form = TopicForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        topic = form.save()
        return HttpResponseRedirect(topic.get_absolute_url())
    return render(
        request,
        "signal_lab/topic_form.html",
        {"form": form, "form_title": "Новая тема"},
    )


def topic_update(request, slug):
    topic = get_object_or_404(Topic, slug=slug)
    if settings.READ_ONLY_DEMO and request.method == "POST":
        return HttpResponse("Демо-режим не сохраняет изменения.", status=403)
    form = TopicForm(request.POST or None, instance=topic)
    if request.method == "POST" and form.is_valid():
        topic = form.save()
        return HttpResponseRedirect(topic.get_absolute_url())
    return render(
        request,
        "signal_lab/topic_form.html",
        {
            "form": form,
            "form_title": f"Редактирование темы: {topic.title}",
            "topic": topic,
        },
    )


def exercise_create(request):
    if settings.READ_ONLY_DEMO and request.method == "POST":
        return HttpResponse("Демо-режим не сохраняет изменения.", status=403)
    form = ExerciseForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        exercise = form.save()
        return HttpResponseRedirect(exercise.get_absolute_url())
    return render(
        request,
        "signal_lab/exercise_form.html",
        {"form": form, "form_title": "Новая задача"},
    )


def exercise_update(request, slug):
    exercise = get_object_or_404(Exercise, slug=slug)
    if settings.READ_ONLY_DEMO and request.method == "POST":
        return HttpResponse("Демо-режим не сохраняет изменения.", status=403)
    form = ExerciseForm(request.POST or None, instance=exercise)
    if request.method == "POST" and form.is_valid():
        exercise = form.save()
        return HttpResponseRedirect(exercise.get_absolute_url())
    return render(
        request,
        "signal_lab/exercise_form.html",
        {
            "form": form,
            "form_title": f"Редактирование задачи: {exercise.title}",
            "exercise": exercise,
        },
    )


def _check_exercise_answer(exercise, answer):
    if exercise.answer_kind == Exercise.AnswerKind.NUMBER:
        try:
            numeric_answer = float(answer.replace(",", "."))
        except ValueError:
            return False
        return abs(numeric_answer - exercise.correct_numeric_answer) <= exercise.tolerance
    normalized_answer = answer.strip().lower()
    expected = exercise.correct_text_answer.strip().lower()
    return normalized_answer == expected


def _history_preview(session_key):
    return list(
        LearningEvent.objects.filter(session_key=session_key)
        .select_related("topic")
        .order_by("-created_at")[:5]
    )


def _build_topic_next_step(session_key, topic):
    snapshot = build_progress_snapshot(session_key)
    recommendation = snapshot["recommendation"]
    if topic != snapshot["weakest_topic"]:
        return {
            "title": recommendation["title"],
            "reason": recommendation["reason"],
            "url": recommendation["url"],
        }
    return {
        "title": recommendation["title"],
        "reason": recommendation["reason"],
        "url": recommendation["url"],
    }
