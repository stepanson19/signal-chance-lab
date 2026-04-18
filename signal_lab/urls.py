from django.urls import path

from . import views

app_name = "signal_lab"

urlpatterns = [
    path("", views.home, name="home"),
    path("labs/", views.lab_list, name="lab_list"),
    path("labs/<slug:slug>/", views.lab_detail, name="lab_detail"),
    path("exercises/", views.exercise_list, name="exercise_list"),
    path(
        "exercises/<slug:slug>/",
        views.exercise_detail,
        name="exercise_detail",
    ),
    path("topics/<slug:slug>/", views.topic_detail, name="topic_detail"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("history/", views.history, name="history"),
    path("review/", views.review_home, name="review_home"),
    path("review/<slug:slug>/", views.review_topic, name="review_topic"),
    path("content/", views.content_manage, name="content_manage"),
    path("content/topics/new/", views.topic_create, name="topic_create"),
    path(
        "content/topics/<slug:slug>/edit/",
        views.topic_update,
        name="topic_update",
    ),
    path("content/exercises/new/", views.exercise_create, name="exercise_create"),
    path(
        "content/exercises/<slug:slug>/edit/",
        views.exercise_update,
        name="exercise_update",
    ),
]
