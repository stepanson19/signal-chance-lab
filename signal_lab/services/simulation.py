import math
import random
from collections import Counter


def run_simulation(experiment_type, parameters):
    handlers = {
        "coin": _simulate_coin,
        "dice": _simulate_dice,
        "binomial": _simulate_binomial,
        "normal": _simulate_normal,
    }
    if experiment_type not in handlers:
        raise ValueError("Неизвестный тип эксперимента.")
    return handlers[experiment_type](parameters)


def _simulate_coin(parameters):
    trials = _require_positive_int(parameters, "trials")
    probability = _require_probability(parameters, "success_probability")
    rng = random.Random(parameters.get("seed"))

    outcomes = [1 if rng.random() < probability else 0 for _ in range(trials)]
    heads = sum(outcomes)
    tails = trials - heads
    observed = heads / trials
    distribution = [
        _bucket("Орел", heads, trials),
        _bucket("Решка", tails, trials),
    ]
    trend_values = []
    running_heads = 0
    for trial, outcome in enumerate(outcomes, start=1):
        running_heads += outcome
        trend_values.append(running_heads / trial)
    return _result(
        {
            "expected_value": probability,
            "observed_value": round(observed, 4),
            "distribution": distribution,
            "summary": "Доля успехов постепенно приближается к теоретической вероятности.",
            "trend_series": _sample_trend(trend_values, expected=probability),
            "summary_metrics": [
                _metric("Частота успеха", round(observed, 4)),
                _metric("Теоретическая вероятность", round(probability, 4)),
                _metric("Количество испытаний", trials),
            ],
        }
    )


def _simulate_dice(parameters):
    trials = _require_positive_int(parameters, "trials")
    dice_count = int(parameters.get("dice_count", 1))
    if dice_count <= 0:
        raise ValueError("Количество кубиков должно быть положительным.")
    rng = random.Random(parameters.get("seed"))
    rolls = [
        sum(rng.randint(1, 6) for _ in range(dice_count))
        for _ in range(trials)
    ]
    counter = Counter(rolls)
    min_face = dice_count
    max_face = 6 * dice_count
    distribution = [
        _bucket(str(face), counter.get(face, 0), trials)
        for face in range(min_face, max_face + 1)
    ]
    observed = sum(rolls) / trials
    expected = dice_count * 3.5
    running_means = []
    total = 0
    for index, roll in enumerate(rolls, start=1):
        total += roll
        running_means.append(total / index)
    return _result(
        {
            "expected_value": expected,
            "observed_value": round(observed, 4),
            "distribution": distribution,
            "summary": "Среднее значение честного кубика стремится к 3.5.",
            "trend_series": _sample_trend(running_means, expected=expected),
            "summary_metrics": [
                _metric("Среднее значение", round(observed, 4)),
                _metric("Теория", round(expected, 4)),
                _metric("Кубиков в серии", dice_count),
            ],
        }
    )


def _simulate_binomial(parameters):
    repetitions = _require_positive_int(parameters, "repetitions")
    trials = _require_positive_int(parameters, "trials")
    probability = _require_probability(parameters, "success_probability")
    rng = random.Random(parameters.get("seed"))

    outcomes = []
    for _ in range(repetitions):
        successes = sum(1 for _ in range(trials) if rng.random() < probability)
        outcomes.append(successes)
    counter = Counter(outcomes)
    distribution = [
        _bucket(str(successes), counter.get(successes, 0), repetitions)
        for successes in range(0, trials + 1)
        if counter.get(successes, 0) or successes <= min(6, trials)
    ]
    observed = sum(outcomes) / repetitions
    running_means = []
    total = 0
    for index, outcome in enumerate(outcomes, start=1):
        total += outcome
        running_means.append(total / index)
    expected = round(trials * probability, 4)
    return _result(
        {
            "expected_value": expected,
            "observed_value": round(observed, 4),
            "distribution": distribution,
            "summary": "Среднее число успехов тяготеет к n × p.",
            "trend_series": _sample_trend(running_means, expected=expected),
            "summary_metrics": [
                _metric("Среднее число успехов", round(observed, 4)),
                _metric("Теория", expected),
                _metric("Количество симуляций", repetitions),
            ],
        }
    )


def _simulate_normal(parameters):
    sample_size = _require_positive_int(parameters, "sample_size")
    mean = float(parameters.get("mean", 0))
    standard_deviation = float(parameters.get("standard_deviation", 1))
    if standard_deviation <= 0:
        raise ValueError("Стандартное отклонение должно быть положительным.")

    rng = random.Random(parameters.get("seed"))
    values = [rng.gauss(mean, standard_deviation) for _ in range(sample_size)]
    observed = sum(values) / sample_size
    distribution = _build_histogram(values, bins=6)
    running_means = []
    total = 0
    for index, value in enumerate(values, start=1):
        total += value
        running_means.append(total / index)
    return _result(
        {
            "expected_value": round(mean, 4),
            "observed_value": round(observed, 4),
            "distribution": distribution,
            "summary": "Даже шумная выборка постепенно стабилизируется вокруг среднего.",
            "trend_series": _sample_trend(running_means, expected=mean),
            "summary_metrics": [
                _metric("Выборочное среднее", round(observed, 4)),
                _metric("Ожидаемое среднее", round(mean, 4)),
                _metric("Размер выборки", sample_size),
            ],
        }
    )


def _build_histogram(values, bins):
    minimum = min(values)
    maximum = max(values)
    if math.isclose(minimum, maximum):
        return [_bucket(f"{minimum:.2f}", len(values), len(values))]

    step = (maximum - minimum) / bins
    counts = [0] * bins
    labels = []
    for index in range(bins):
        start = minimum + (step * index)
        end = maximum if index == bins - 1 else minimum + (step * (index + 1))
        labels.append(f"{start:.2f}–{end:.2f}")

    for value in values:
        raw_index = int((value - minimum) / step)
        bucket_index = min(raw_index, bins - 1)
        counts[bucket_index] += 1

    total = len(values)
    return [
        _bucket(label, count, total)
        for label, count in zip(labels, counts)
    ]


def _result(payload):
    expected_value = payload["expected_value"]
    observed_value = payload["observed_value"]
    deviation = round(abs(observed_value - expected_value), 4)
    return {
        "expected_value": expected_value,
        "observed_value": observed_value,
        "deviation": deviation,
        "distribution": payload["distribution"],
        "summary": payload["summary"],
        "trend_series": payload.get("trend_series", []),
        "summary_metrics": payload.get("summary_metrics", []),
        "comparison": [
            {"label": "Теория", "value": round(expected_value, 4)},
            {"label": "Эксперимент", "value": round(observed_value, 4)},
        ],
    }


def _bucket(label, count, total):
    ratio = 0
    if total:
        ratio = round(count / total, 4)
    return {
        "label": label,
        "count": count,
        "ratio": ratio,
    }


def _metric(label, value):
    return {
        "label": label,
        "value": value,
    }


def _sample_trend(values, expected):
    if not values:
        return []
    max_points = 24
    if len(values) <= max_points:
        points = values
    else:
        step = max(1, len(values) // max_points)
        points = values[::step]
        if points[-1] != values[-1]:
            points.append(values[-1])
    return [
        {
            "x": index + 1,
            "observed": round(value, 4),
            "expected": round(expected, 4),
        }
        for index, value in enumerate(points)
    ]


def _require_positive_int(parameters, key):
    value = int(parameters.get(key, 0))
    if value <= 0:
        raise ValueError("Количество испытаний должно быть положительным.")
    return value


def _require_probability(parameters, key):
    value = float(parameters.get(key, 0))
    if value < 0 or value > 1:
        raise ValueError("Вероятность должна быть в диапазоне от 0 до 1.")
    return value
