import math


FIELD_RANDOMIZATION = {
    "trials": {
        "type": "int",
        "min": 24,
        "max": 720,
        "step": 1,
    },
    "success_probability": {
        "type": "float",
        "min": 0.12,
        "max": 0.88,
        "step": 0.01,
        "decimals": 2,
    },
    "repetitions": {
        "type": "int",
        "min": 40,
        "max": 320,
        "step": 1,
    },
    "sample_size": {
        "type": "int",
        "min": 20,
        "max": 420,
        "step": 1,
    },
    "mean": {
        "type": "float",
        "min": -1.5,
        "max": 7.5,
        "step": 0.1,
        "decimals": 1,
    },
    "standard_deviation": {
        "type": "float",
        "min": 0.3,
        "max": 3.2,
        "step": 0.1,
        "decimals": 1,
    },
}

TYPE_EXPERIENCE = {
    "coin": {
        "story": (
            "Меняйте длину серии и вероятность успеха, чтобы увидеть, как частота "
            "в реальном эксперименте догоняет теорию."
        ),
        "insights": [
            "Короткие серии шумные и легко вводят в заблуждение.",
            "Частота стабилизируется только на длинной дистанции.",
            "Смещенная монета помогает отделить случайность от параметра модели.",
        ],
        "preview_distribution": [
            {"label": "Орел", "count": 13, "ratio": 0.54},
            {"label": "Решка", "count": 11, "ratio": 0.46},
        ],
        "random_fields": ["trials", "success_probability"],
        "presets": [
            {
                "label": "Быстрый старт",
                "summary": "24 броска честной монеты.",
                "values": {
                    "trials": 24,
                    "success_probability": 0.5,
                },
            },
            {
                "label": "Длинная серия",
                "summary": "400 бросков, чтобы увидеть стабилизацию.",
                "values": {
                    "trials": 400,
                    "success_probability": 0.5,
                },
            },
            {
                "label": "Смещенная модель",
                "summary": "Успех заметно чаще 50%.",
                "values": {
                    "trials": 120,
                    "success_probability": 0.72,
                },
            },
        ],
    },
    "dice": {
        "story": (
            "Бросайте кубик или сумму двух кубиков и сравнивайте форму "
            "распределения с теоретическим ожиданием."
        ),
        "insights": [
            "У одного кубика грани равновероятны.",
            "У суммы двух кубиков центральные значения появляются чаще крайних.",
            "Среднее значение выходит на теорию быстрее, чем отдельные частоты.",
        ],
        "preview_distribution": [
            {"label": "2", "count": 1, "ratio": 0.06},
            {"label": "3", "count": 2, "ratio": 0.11},
            {"label": "4", "count": 3, "ratio": 0.17},
            {"label": "5", "count": 4, "ratio": 0.22},
            {"label": "6", "count": 5, "ratio": 0.28},
            {"label": "7", "count": 6, "ratio": 0.33},
        ],
        "random_fields": ["trials"],
        "presets": [
            {
                "label": "Короткая серия",
                "summary": "36 бросков для быстрой проверки.",
                "values": {
                    "trials": 36,
                },
            },
            {
                "label": "Учебная серия",
                "summary": "120 бросков для устойчивой картинки.",
                "values": {
                    "trials": 120,
                },
            },
            {
                "label": "Большая серия",
                "summary": "480 бросков для чистого распределения.",
                "values": {
                    "trials": 480,
                },
            },
        ],
    },
    "binomial": {
        "story": (
            "Сначала задайте вероятность успеха и число испытаний в одном опыте, "
            "потом повторите опыт много раз и посмотрите форму распределения."
        ),
        "insights": [
            "Пик распределения движется вместе с n × p.",
            "Чем больше повторов, тем яснее форма биномиального закона.",
            "Даже заметный шум не ломает общую тенденцию среднего.",
        ],
        "preview_distribution": [
            {"label": "0", "count": 1, "ratio": 0.05},
            {"label": "1", "count": 3, "ratio": 0.15},
            {"label": "2", "count": 6, "ratio": 0.3},
            {"label": "3", "count": 7, "ratio": 0.35},
            {"label": "4", "count": 4, "ratio": 0.2},
            {"label": "5", "count": 2, "ratio": 0.1},
        ],
        "random_fields": ["trials", "repetitions", "success_probability"],
        "presets": [
            {
                "label": "Учебный кейс",
                "summary": "12 испытаний и умеренная вероятность.",
                "values": {
                    "trials": 12,
                    "repetitions": 80,
                    "success_probability": 0.35,
                },
            },
            {
                "label": "Сдвиг вправо",
                "summary": "Больше успехов за счет высокой вероятности.",
                "values": {
                    "trials": 18,
                    "repetitions": 120,
                    "success_probability": 0.65,
                },
            },
            {
                "label": "Много повторов",
                "summary": "Оттачиваем форму распределения.",
                "values": {
                    "trials": 20,
                    "repetitions": 240,
                    "success_probability": 0.45,
                },
            },
        ],
    },
    "normal": {
        "story": (
            "Генерируйте выборки с шумом и наблюдайте, как среднее постепенно "
            "собирается вокруг ожидаемого значения."
        ),
        "insights": [
            "Шум сильнее заметен на малой выборке.",
            "Большая выборка сужает разброс оценки среднего.",
            "Гистограмма показывает форму данных, а линия тренда - стабилизацию.",
        ],
        "preview_distribution": [
            {"label": "0.5–1.0", "count": 2, "ratio": 0.1},
            {"label": "1.0–1.5", "count": 5, "ratio": 0.25},
            {"label": "1.5–2.0", "count": 8, "ratio": 0.4},
            {"label": "2.0–2.5", "count": 7, "ratio": 0.35},
            {"label": "2.5–3.0", "count": 4, "ratio": 0.2},
            {"label": "3.0–3.5", "count": 2, "ratio": 0.1},
        ],
        "random_fields": ["sample_size", "mean", "standard_deviation"],
        "presets": [
            {
                "label": "Небольшая выборка",
                "summary": "30 наблюдений со средним 3.",
                "values": {
                    "sample_size": 30,
                    "mean": 3,
                    "standard_deviation": 1.2,
                },
            },
            {
                "label": "Точная оценка",
                "summary": "Крупная выборка и умеренный шум.",
                "values": {
                    "sample_size": 240,
                    "mean": 3,
                    "standard_deviation": 0.8,
                },
            },
            {
                "label": "Сильный шум",
                "summary": "Высокое отклонение и средняя выборка.",
                "values": {
                    "sample_size": 90,
                    "mean": 4.2,
                    "standard_deviation": 2.2,
                },
            },
        ],
    },
}

LAB_OVERRIDES = {
    "biased-coin-lab": {
        "story": (
            "Это лаборатория про несимметричную модель: здесь особенно полезно "
            "сравнивать честную и смещенную гипотезы."
        ),
        "presets": [
            {
                "label": "Легкий перекос",
                "summary": "Монета лишь немного смещена.",
                "values": {
                    "trials": 80,
                    "success_probability": 0.58,
                },
            },
            {
                "label": "Явная асимметрия",
                "summary": "Частота успеха сильно выше 50%.",
                "values": {
                    "trials": 140,
                    "success_probability": 0.74,
                },
            },
            {
                "label": "Проверка гипотезы",
                "summary": "Длинная серия для уверенного вывода.",
                "values": {
                    "trials": 520,
                    "success_probability": 0.66,
                },
            },
        ],
    },
    "two-dice-sum-lab": {
        "story": (
            "Здесь моделируется сумма двух кубиков, поэтому наиболее частой должна "
            "быть сумма 7, а не крайние значения."
        ),
        "fixed_parameters": {
            "dice_count": 2,
        },
        "insights": [
            "Сумма 7 выигрывает по числу комбинаций.",
            "Распределение симметрично вокруг центра.",
            "Теоретическое среднее суммы двух кубиков равно 7.",
        ],
    },
    "large-numbers-lab": {
        "story": (
            "Главная цель - не поймать красивую серию, а увидеть, как линия частоты "
            "успокаивается по мере роста числа наблюдений."
        ),
        "presets": [
            {
                "label": "Колебания",
                "summary": "Короткая серия с заметным шумом.",
                "values": {
                    "trials": 30,
                    "success_probability": 0.5,
                },
            },
            {
                "label": "Переходный режим",
                "summary": "Средняя серия, где тренд уже выравнивается.",
                "values": {
                    "trials": 180,
                    "success_probability": 0.5,
                },
            },
            {
                "label": "Закон больших чисел",
                "summary": "Длинная серия почти прилипает к теории.",
                "values": {
                    "trials": 800,
                    "success_probability": 0.5,
                },
            },
        ],
    },
    "precision-lab": {
        "story": (
            "Сравнивайте выборки разного размера и наблюдайте, как уменьшается "
            "нестабильность оценки среднего."
        ),
    },
}


def build_lab_experience(lab):
    experience = _merge_dicts(
        TYPE_EXPERIENCE.get(lab.experiment_type, {}),
        LAB_OVERRIDES.get(lab.slug, {}),
    )
    random_fill = {
        field_name: FIELD_RANDOMIZATION[field_name]
        for field_name in experience.get("random_fields", [])
        if field_name in FIELD_RANDOMIZATION
    }
    return {
        "story": experience.get("story", ""),
        "insights": experience.get("insights", []),
        "presets": experience.get("presets", []),
        "random_fill": random_fill,
        "fixed_parameters": experience.get("fixed_parameters", {}),
        "preview_histogram": _build_histogram_chart(
            experience.get("preview_distribution", [])
        ),
        "chart_notes": {
            "trend": "Линия показывает, как наблюдаемое значение движется к теории.",
            "comparison": "Высота колонок помогает быстро сравнить модель и реальный запуск.",
            "distribution": "Гистограмма показывает форму распределения и доминирующие исходы.",
        },
    }


def decorate_lab_result(result):
    distribution = list(result.get("distribution", []))
    comparison = list(result.get("comparison", []))
    trend_series = list(result.get("trend_series", []))
    dominant_bucket = max(distribution, key=lambda bucket: bucket["count"], default=None)
    return {
        **result,
        "comparison_bars": _build_comparison_bars(comparison),
        "trend_chart": _build_trend_chart(trend_series),
        "histogram_chart": _build_histogram_chart(distribution),
        "dominant_bucket": dominant_bucket,
    }


def _build_comparison_bars(comparison):
    if not comparison:
        return []
    max_value = max(abs(item["value"]) for item in comparison) or 1
    return [
        {
            "label": item["label"],
            "value": item["value"],
            "ratio": round(abs(item["value"]) / max_value, 4),
        }
        for item in comparison
    ]


def _build_trend_chart(trend_series):
    if not trend_series:
        return None

    values = []
    for point in trend_series:
        values.extend([point["observed"], point["expected"]])
    minimum = min(values)
    maximum = max(values)
    if math.isclose(minimum, maximum):
        minimum -= 1
        maximum += 1

    padding = (maximum - minimum) * 0.12
    minimum -= padding
    maximum += padding
    chart_height = 80
    chart_width = 88
    baseline_x = 6
    baseline_y = 90
    total_points = max(len(trend_series) - 1, 1)

    observed_points = []
    expected_points = []
    points = []
    for index, point in enumerate(trend_series):
        x_value = baseline_x + ((chart_width * index) / total_points)
        observed_y = _scale_value(
            point["observed"],
            minimum,
            maximum,
            chart_height,
            baseline_y,
        )
        expected_y = _scale_value(
            point["expected"],
            minimum,
            maximum,
            chart_height,
            baseline_y,
        )
        observed_points.append(f"{x_value:.2f},{observed_y:.2f}")
        expected_points.append(f"{x_value:.2f},{expected_y:.2f}")
        points.append(
            {
                "x": round(x_value, 2),
                "observed_y": round(observed_y, 2),
                "step": point["x"],
            }
        )

    return {
        "observed_points": " ".join(observed_points),
        "expected_points": " ".join(expected_points),
        "points": points,
        "min_label": round(minimum, 2),
        "max_label": round(maximum, 2),
        "last_step": trend_series[-1]["x"],
    }


def _build_histogram_chart(distribution):
    if not distribution:
        return None

    bar_width = 10
    gap = 4
    base_x = 8
    max_height = 58
    baseline_y = 72
    max_ratio = max(bucket["ratio"] for bucket in distribution) or 1
    bars = []
    labels = []

    for index, bucket in enumerate(distribution):
        ratio = bucket["ratio"] / max_ratio if max_ratio else 0
        height = max(6, round(max_height * ratio, 2))
        x_value = base_x + (index * (bar_width + gap))
        y_value = baseline_y - height
        bars.append(
            {
                "label": bucket["label"],
                "count": bucket["count"],
                "ratio": bucket["ratio"],
                "x": round(x_value, 2),
                "y": round(y_value, 2),
                "width": bar_width,
                "height": height,
            }
        )
        labels.append(
            {
                "x": round(x_value + (bar_width / 2), 2),
                "label": bucket["label"],
            }
        )

    total_width = base_x + (len(distribution) * (bar_width + gap)) + 2
    return {
        "bars": bars,
        "labels": labels,
        "width": total_width,
        "view_box": f"0 0 {total_width} 84",
        "baseline_y": baseline_y,
    }


def _scale_value(value, minimum, maximum, chart_height, baseline_y):
    ratio = (value - minimum) / (maximum - minimum)
    return baseline_y - (ratio * chart_height)


def _merge_dicts(base, override):
    merged = dict(base)
    for key, value in override.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = _merge_dicts(merged[key], value)
        else:
            merged[key] = value
    return merged
