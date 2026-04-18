from signal_lab.models import LearningEvent


def log_learning_event(
    *,
    session_key,
    topic,
    event_type,
    title,
    details="",
    delta=0,
):
    return LearningEvent.objects.create(
        session_key=session_key,
        topic=topic,
        event_type=event_type,
        title=title,
        details=details,
        delta=delta,
    )
