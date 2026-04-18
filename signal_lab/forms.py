from django import forms

from signal_lab.models import Exercise, Lab, Topic


class LabSimulationForm(forms.Form):
    trials = forms.IntegerField(
        min_value=1,
        max_value=5000,
        required=False,
        label="Количество испытаний",
    )
    success_probability = forms.FloatField(
        min_value=0,
        max_value=1,
        required=False,
        label="Вероятность успеха",
    )
    repetitions = forms.IntegerField(
        min_value=1,
        max_value=3000,
        required=False,
        label="Количество симуляций",
    )
    sample_size = forms.IntegerField(
        min_value=1,
        max_value=5000,
        required=False,
        label="Размер выборки",
    )
    mean = forms.FloatField(required=False, label="Ожидаемое среднее")
    standard_deviation = forms.FloatField(
        min_value=0.001,
        required=False,
        label="Стандартное отклонение",
    )

    def __init__(self, *args, **kwargs):
        self.lab = kwargs.pop("lab")
        super().__init__(*args, **kwargs)
        self.required_fields = self._required_fields_for_lab()

    def clean(self):
        cleaned_data = super().clean()
        for field_name in self.required_fields:
            if cleaned_data.get(field_name) in {None, ""}:
                self.add_error(
                    field_name,
                    "Заполните это поле, чтобы запустить эксперимент.",
                )
        return cleaned_data

    def cleaned_parameters(self):
        allowed = {field_name: self.cleaned_data[field_name] for field_name in self.required_fields}
        allowed["seed"] = 17
        return allowed

    def _required_fields_for_lab(self):
        mapping = {
            Lab.ExperimentType.COIN: ["trials", "success_probability"],
            Lab.ExperimentType.DICE: ["trials"],
            Lab.ExperimentType.BINOMIAL: [
                "trials",
                "repetitions",
                "success_probability",
            ],
            Lab.ExperimentType.NORMAL: [
                "sample_size",
                "mean",
                "standard_deviation",
            ],
        }
        return mapping[self.lab.experiment_type]


class ExerciseAnswerForm(forms.Form):
    answer = forms.CharField(
        max_length=255,
        strip=True,
        label="Ваш ответ",
        error_messages={
            "required": "Введите ответ перед отправкой.",
        },
    )


class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = [
            "title",
            "slug",
            "short_description",
            "theory_summary",
            "intuition_text",
            "formula_text",
            "common_mistake",
            "accent_color",
            "order",
        ]


class ExerciseForm(forms.ModelForm):
    class Meta:
        model = Exercise
        fields = [
            "topic",
            "related_lab",
            "title",
            "slug",
            "statement",
            "difficulty",
            "answer_kind",
            "correct_numeric_answer",
            "tolerance",
            "correct_text_answer",
            "hint",
            "explanation",
            "is_featured",
        ]

    def clean(self):
        cleaned_data = super().clean()
        answer_kind = cleaned_data.get("answer_kind")
        numeric_answer = cleaned_data.get("correct_numeric_answer")
        text_answer = cleaned_data.get("correct_text_answer")

        if answer_kind == Exercise.AnswerKind.NUMBER and numeric_answer is None:
            self.add_error(
                "correct_numeric_answer",
                "Для числового задания укажите правильный ответ.",
            )
        if answer_kind == Exercise.AnswerKind.TEXT and not text_answer:
            self.add_error(
                "correct_text_answer",
                "Для текстового задания укажите эталонный ответ.",
            )
        return cleaned_data
