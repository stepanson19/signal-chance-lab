from django.core.management.base import BaseCommand

from signal_lab.models import Exercise, Lab, Topic


TOPICS = [
    {
        "slug": "random-events",
        "title": "Случайные события",
        "short_description": "Базовая интуиция вероятности, монета и дерево исходов.",
        "theory_summary": (
            "Вероятность помогает оценить, как часто событие будет происходить "
            "в длинной серии испытаний."
        ),
        "intuition_text": (
            "Один бросок может удивить, но длинная серия постепенно стабилизирует "
            "доли исходов."
        ),
        "formula_text": "P(A) = m / n",
        "common_mistake": (
            "Студенты часто думают, что после серии решек обязательно выпадет орел."
        ),
        "accent_color": "#2563eb",
        "order": 1,
    },
    {
        "slug": "discrete-distributions",
        "title": "Дискретные распределения",
        "short_description": "Биномиальные схемы и дискретные вероятностные модели.",
        "theory_summary": (
            "Дискретные распределения описывают случайные величины с конечным "
            "или счетным набором значений."
        ),
        "intuition_text": (
            "Если повторять один и тот же опыт с одинаковой вероятностью успеха, "
            "можно предсказать форму распределения результата."
        ),
        "formula_text": "P(X=k)=C(n,k)p^k(1-p)^(n-k)",
        "common_mistake": (
            "Путают вероятность одного исхода с математическим ожиданием."
        ),
        "accent_color": "#0f766e",
        "order": 2,
    },
    {
        "slug": "sampling-and-noise",
        "title": "Выборка и шум",
        "short_description": "Средние значения, нормальное распределение и шум измерений.",
        "theory_summary": (
            "При работе с выборкой важны не только отдельные значения, но и форма "
            "распределения и устойчивость среднего."
        ),
        "intuition_text": (
            "Шум выглядит хаотично на малом объеме данных, но крупная выборка "
            "делает картину стабильнее."
        ),
        "formula_text": "z = (x - μ) / σ",
        "common_mistake": (
            "Малую выборку принимают за окончательное доказательство тренда."
        ),
        "accent_color": "#c2410c",
        "order": 3,
    },
    {
        "slug": "conditional-probability",
        "title": "Условная вероятность",
        "short_description": "Вероятность события при известной дополнительной информации.",
        "theory_summary": (
            "Условная вероятность помогает пересчитать шансы события, если часть "
            "пространства исходов уже исключена."
        ),
        "intuition_text": (
            "Мы сужаем множество исходов и заново оцениваем долю благоприятных."
        ),
        "formula_text": "P(A|B)=P(A∩B)/P(B)",
        "common_mistake": (
            "Независимость путают с условной вероятностью и симметрией событий."
        ),
        "accent_color": "#8b5cf6",
        "order": 4,
    },
    {
        "slug": "large-numbers",
        "title": "Закон больших чисел",
        "short_description": "Почему средние и частоты стабилизируются на длинной дистанции.",
        "theory_summary": (
            "Закон больших чисел объясняет, почему среднее и относительные частоты "
            "приближаются к теоретическим значениям при росте числа наблюдений."
        ),
        "intuition_text": (
            "Разовые колебания сильны, но длинная серия сглаживает случайный шум."
        ),
        "formula_text": "X̄ₙ → E(X)",
        "common_mistake": (
            "Ожидают, что стабилизация должна происходить быстро уже на первых шагах."
        ),
        "accent_color": "#db2777",
        "order": 5,
    },
    {
        "slug": "estimation",
        "title": "Оценивание и интервалы",
        "short_description": "Как размер выборки влияет на точность оценки среднего.",
        "theory_summary": (
            "Оценивание связывает выборочные данные с неизвестными параметрами "
            "генеральной совокупности."
        ),
        "intuition_text": (
            "Чем больше и стабильнее выборка, тем уже разброс возможных оценок."
        ),
        "formula_text": "SE = σ / √n",
        "common_mistake": (
            "Путают сам параметр и выборочную оценку, считая их одинаковыми."
        ),
        "accent_color": "#0f766e",
        "order": 6,
    },
]

LABS = [
    {
        "topic_slug": "random-events",
        "slug": "coin-lab",
        "title": "Лаборатория монеты",
        "summary": "Сравните теоретическую вероятность орла с результатами серии бросков.",
        "experiment_type": Lab.ExperimentType.COIN,
        "difficulty": Lab.Difficulty.START,
        "estimated_minutes": 8,
        "theory_hint": "Чем больше бросков, тем стабильнее доля орлов.",
        "is_featured": True,
    },
    {
        "topic_slug": "random-events",
        "slug": "dice-lab",
        "title": "Лаборатория кубика",
        "summary": "Изучите частоты граней и сравните их с равномерным распределением.",
        "experiment_type": Lab.ExperimentType.DICE,
        "difficulty": Lab.Difficulty.START,
        "estimated_minutes": 10,
        "theory_hint": "У честного кубика каждая грань стремится к доле 1/6.",
        "is_featured": False,
    },
    {
        "topic_slug": "discrete-distributions",
        "slug": "binomial-lab",
        "title": "Биномиальная мастерская",
        "summary": "Проверьте, как число успехов зависит от количества опытов и вероятности.",
        "experiment_type": Lab.ExperimentType.BINOMIAL,
        "difficulty": Lab.Difficulty.CORE,
        "estimated_minutes": 12,
        "theory_hint": "Распределение сдвигается при изменении вероятности успеха.",
        "is_featured": True,
    },
    {
        "topic_slug": "sampling-and-noise",
        "slug": "normal-sample-lab",
        "title": "Шум и нормальная выборка",
        "summary": "Посмотрите, как ведет себя выборка из нормального распределения.",
        "experiment_type": Lab.ExperimentType.NORMAL,
        "difficulty": Lab.Difficulty.PLUS,
        "estimated_minutes": 14,
        "theory_hint": "Среднее значение стабилизируется быстрее, чем отдельные наблюдения.",
        "is_featured": True,
    },
    {
        "topic_slug": "conditional-probability",
        "slug": "biased-coin-lab",
        "title": "Смещённая монета",
        "summary": (
            "Посмотрите, как меняется частота успеха, если вероятность орла "
            "не равна 0.5."
        ),
        "experiment_type": Lab.ExperimentType.COIN,
        "difficulty": Lab.Difficulty.CORE,
        "estimated_minutes": 9,
        "theory_hint": (
            "Смещённая монета помогает почувствовать разницу между честной и "
            "условной моделью."
        ),
        "is_featured": True,
    },
    {
        "topic_slug": "random-events",
        "slug": "two-dice-sum-lab",
        "title": "Сумма двух кубиков",
        "summary": "Исследуйте, почему не все суммы при броске двух кубиков равновероятны.",
        "experiment_type": Lab.ExperimentType.DICE,
        "difficulty": Lab.Difficulty.CORE,
        "estimated_minutes": 11,
        "theory_hint": "Количество комбинаций для суммы 7 больше, чем для суммы 2 или 12.",
        "is_featured": True,
    },
    {
        "topic_slug": "large-numbers",
        "slug": "large-numbers-lab",
        "title": "Стабилизация частоты",
        "summary": (
            "Наблюдайте, как относительная частота приближается к "
            "теоретической вероятности."
        ),
        "experiment_type": Lab.ExperimentType.COIN,
        "difficulty": Lab.Difficulty.CORE,
        "estimated_minutes": 12,
        "theory_hint": (
            "С увеличением числа испытаний случайные колебания становятся "
            "менее заметны."
        ),
        "is_featured": True,
    },
    {
        "topic_slug": "estimation",
        "slug": "precision-lab",
        "title": "Точность оценки среднего",
        "summary": "Сравните, как размер выборки влияет на устойчивость среднего значения.",
        "experiment_type": Lab.ExperimentType.NORMAL,
        "difficulty": Lab.Difficulty.PLUS,
        "estimated_minutes": 15,
        "theory_hint": "Малые выборки шумнее, а большие дают более узкий коридор оценок.",
        "is_featured": True,
    },
]

EXERCISES = [
    {
        "topic_slug": "random-events",
        "lab_slug": "coin-lab",
        "slug": "coin-probability-50",
        "title": "Вероятность орла",
        "statement": "Какова вероятность выпадения орла у честной монеты?",
        "difficulty": Lab.Difficulty.START,
        "answer_kind": Exercise.AnswerKind.NUMBER,
        "correct_numeric_answer": 0.5,
        "tolerance": 0.001,
        "correct_text_answer": "",
        "hint": "У честной монеты два равновозможных исхода.",
        "explanation": "Вероятность орла равна 1/2, то есть 0.5.",
        "is_featured": True,
    },
    {
        "topic_slug": "random-events",
        "lab_slug": "dice-lab",
        "slug": "dice-expected-value",
        "title": "Среднее значение кубика",
        "statement": "Найдите математическое ожидание результата честного броска кубика.",
        "difficulty": Lab.Difficulty.CORE,
        "answer_kind": Exercise.AnswerKind.NUMBER,
        "correct_numeric_answer": 3.5,
        "tolerance": 0.001,
        "correct_text_answer": "",
        "hint": "Сложите числа от 1 до 6 и разделите на 6.",
        "explanation": "Среднее значение честного кубика равно (1+2+3+4+5+6)/6 = 3.5.",
        "is_featured": False,
    },
    {
        "topic_slug": "discrete-distributions",
        "lab_slug": "binomial-lab",
        "slug": "binomial-expected-successes",
        "title": "Ожидаемое число успехов",
        "statement": (
            "Сколько успехов в среднем ожидается в 20 испытаниях при вероятности "
            "успеха 0.3?"
        ),
        "difficulty": Lab.Difficulty.CORE,
        "answer_kind": Exercise.AnswerKind.NUMBER,
        "correct_numeric_answer": 6.0,
        "tolerance": 0.001,
        "correct_text_answer": "",
        "hint": "Для биномиальной величины ожидание равно n × p.",
        "explanation": "Математическое ожидание биномиальной величины: 20 × 0.3 = 6.",
        "is_featured": True,
    },
    {
        "topic_slug": "sampling-and-noise",
        "lab_slug": "normal-sample-lab",
        "slug": "normal-distribution-shape",
        "title": "Форма нормального распределения",
        "statement": "Как одним словом обычно описывают форму нормального распределения?",
        "difficulty": Lab.Difficulty.START,
        "answer_kind": Exercise.AnswerKind.TEXT,
        "correct_numeric_answer": None,
        "tolerance": 0.0,
        "correct_text_answer": "колокол",
        "hint": "Подумайте о самом частом визуальном описании этой кривой.",
        "explanation": (
            "Нормальное распределение часто описывают как колоколообразное."
        ),
        "is_featured": False,
    },
    {
        "topic_slug": "sampling-and-noise",
        "lab_slug": "normal-sample-lab",
        "slug": "sample-size-stability",
        "title": "Почему растет стабильность",
        "statement": (
            "Что обычно происходит со средним выборки при увеличении числа наблюдений?"
        ),
        "difficulty": Lab.Difficulty.PLUS,
        "answer_kind": Exercise.AnswerKind.TEXT,
        "correct_numeric_answer": None,
        "tolerance": 0.0,
        "correct_text_answer": "стабилизируется",
        "hint": "Сравните маленькую и большую выборку.",
        "explanation": (
            "При увеличении объема выборки среднее становится устойчивее и меньше "
            "колеблется."
        ),
        "is_featured": True,
    },
    {
        "topic_slug": "conditional-probability",
        "lab_slug": "biased-coin-lab",
        "slug": "biased-coin-most-likely",
        "title": "Смещённая монета и частота",
        "statement": (
            "Если вероятность орла равна 0.8, будет ли доля орлов в длинной "
            "серии ближе к 0.8, чем к 0.5?"
        ),
        "difficulty": Lab.Difficulty.START,
        "answer_kind": Exercise.AnswerKind.TEXT,
        "correct_numeric_answer": None,
        "tolerance": 0.0,
        "correct_text_answer": "да",
        "hint": "Сравните теоретическую вероятность и ожидаемую частоту.",
        "explanation": "При большом числе бросков доля орлов стремится к 0.8, а не к 0.5.",
        "is_featured": True,
    },
    {
        "topic_slug": "conditional-probability",
        "lab_slug": "biased-coin-lab",
        "slug": "conditional-probability-value",
        "title": "Числовая условная вероятность",
        "statement": "Если P(A∩B)=0.2 и P(B)=0.5, чему равна P(A|B)?",
        "difficulty": Lab.Difficulty.CORE,
        "answer_kind": Exercise.AnswerKind.NUMBER,
        "correct_numeric_answer": 0.4,
        "tolerance": 0.001,
        "correct_text_answer": "",
        "hint": "Подставьте значения в формулу условной вероятности.",
        "explanation": "P(A|B)=0.2/0.5=0.4.",
        "is_featured": True,
    },
    {
        "topic_slug": "random-events",
        "lab_slug": "two-dice-sum-lab",
        "slug": "two-dice-most-common-sum",
        "title": "Самая частая сумма",
        "statement": "Какая сумма двух честных кубиков встречается чаще всего?",
        "difficulty": Lab.Difficulty.CORE,
        "answer_kind": Exercise.AnswerKind.NUMBER,
        "correct_numeric_answer": 7,
        "tolerance": 0.001,
        "correct_text_answer": "",
        "hint": "Сравните число комбинаций для каждой суммы.",
        "explanation": (
            "Сумма 7 имеет максимальное число комбинаций: 1+6, 2+5, 3+4 и "
            "наоборот."
        ),
        "is_featured": True,
    },
    {
        "topic_slug": "large-numbers",
        "lab_slug": "large-numbers-lab",
        "slug": "large-numbers-main-idea",
        "title": "Смысл закона больших чисел",
        "statement": "Что происходит с относительной частотой события при росте числа испытаний?",
        "difficulty": Lab.Difficulty.START,
        "answer_kind": Exercise.AnswerKind.TEXT,
        "correct_numeric_answer": None,
        "tolerance": 0.0,
        "correct_text_answer": "стабилизируется",
        "hint": "Подумайте о длинной серии однотипных экспериментов.",
        "explanation": (
            "При большом числе испытаний относительная частота стабилизируется "
            "около теоретической вероятности."
        ),
        "is_featured": True,
    },
    {
        "topic_slug": "large-numbers",
        "lab_slug": "large-numbers-lab",
        "slug": "large-numbers-better-estimate",
        "title": "Когда оценка надёжнее",
        "statement": (
            "Какая серия обычно даёт более устойчивую оценку вероятности: "
            "20 испытаний или 2000?"
        ),
        "difficulty": Lab.Difficulty.START,
        "answer_kind": Exercise.AnswerKind.NUMBER,
        "correct_numeric_answer": 2000,
        "tolerance": 0.001,
        "correct_text_answer": "",
        "hint": "Сравните длинную и короткую серию.",
        "explanation": (
            "Чем длиннее серия, тем устойчивее относительная частота и тем "
            "надёжнее оценка."
        ),
        "is_featured": False,
    },
    {
        "topic_slug": "estimation",
        "lab_slug": "precision-lab",
        "slug": "estimation-standard-error",
        "title": "Стандартная ошибка",
        "statement": (
            "Что происходит со стандартной ошибкой среднего при увеличении "
            "размера выборки?"
        ),
        "difficulty": Lab.Difficulty.CORE,
        "answer_kind": Exercise.AnswerKind.TEXT,
        "correct_numeric_answer": None,
        "tolerance": 0.0,
        "correct_text_answer": "уменьшается",
        "hint": "Посмотрите на формулу SE = σ / √n.",
        "explanation": "При росте n знаменатель растёт, а стандартная ошибка уменьшается.",
        "is_featured": True,
    },
    {
        "topic_slug": "estimation",
        "lab_slug": "precision-lab",
        "slug": "estimation-sample-size",
        "title": "Размер выборки и точность",
        "statement": (
            "Если увеличить размер выборки в 4 раза, как изменится "
            "стандартная ошибка при прочих равных?"
        ),
        "difficulty": Lab.Difficulty.PLUS,
        "answer_kind": Exercise.AnswerKind.NUMBER,
        "correct_numeric_answer": 2,
        "tolerance": 0.001,
        "correct_text_answer": "",
        "hint": "Стандартная ошибка связана с корнем из n.",
        "explanation": (
            "При увеличении n в 4 раза корень из n растёт в 2 раза, значит "
            "стандартная ошибка уменьшается в 2 раза."
        ),
        "is_featured": True,
    },
]


class Command(BaseCommand):
    help = "Seeds the Signal & Chance Lab educational content."

    def handle(self, *args, **options):
        topics = {}
        labs = {}

        for topic_payload in TOPICS:
            topic, _ = Topic.objects.update_or_create(
                slug=topic_payload["slug"],
                defaults=topic_payload,
            )
            topics[topic.slug] = topic

        for lab_payload in LABS:
            topic = topics[lab_payload["topic_slug"]]
            defaults = {
                key: value
                for key, value in lab_payload.items()
                if key != "topic_slug"
            }
            defaults["topic"] = topic
            lab, _ = Lab.objects.update_or_create(
                slug=lab_payload["slug"],
                defaults=defaults,
            )
            labs[lab.slug] = lab

        for exercise_payload in EXERCISES:
            topic = topics[exercise_payload["topic_slug"]]
            related_lab = labs[exercise_payload["lab_slug"]]
            defaults = {
                key: value
                for key, value in exercise_payload.items()
                if key not in {"topic_slug", "lab_slug"}
            }
            defaults["topic"] = topic
            defaults["related_lab"] = related_lab
            Exercise.objects.update_or_create(
                slug=exercise_payload["slug"],
                defaults=defaults,
            )

        self.stdout.write(
            self.style.SUCCESS("Signal & Chance Lab content has been seeded.")
        )
