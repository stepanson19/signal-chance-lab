#!/usr/bin/env python3
"""Reproducible classical-ML experiment for the RosNOU entrance abstract.

The script downloads the official RuSentiTweet train/test split, audits it,
filters the three polarity classes, tunes six TF-IDF/classifier combinations
on the training split only, evaluates them once on the published test split,
and exports tables, figures and anonymised error examples.
"""
from __future__ import annotations

import json
import math
import re
import shutil
import sys
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from joblib import Memory
from sklearn.base import clone
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
    precision_score,
    recall_score,
)
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

RANDOM_STATE = 42
LABELS = ["negative", "neutral", "positive"]
BASE_URL = "https://raw.githubusercontent.com/sismetanin/rusentitweet/main"
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "outputs"
CACHE_DIR = ROOT / ".cache"

URL_RE = re.compile(r"(?i)\b(?:https?://|www\.)\S+")
MENTION_RE = re.compile(r"(?<!\w)@[\w_]+", re.UNICODE)
SPACE_RE = re.compile(r"\s+")


def ensure_dirs() -> None:
    for path in (DATA_DIR, OUT_DIR, CACHE_DIR):
        path.mkdir(parents=True, exist_ok=True)


def download(url: str, destination: Path) -> None:
    if destination.exists() and destination.stat().st_size > 100:
        return
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=120) as response, destination.open("wb") as fh:
        shutil.copyfileobj(response, fh)
    if destination.stat().st_size <= 100:
        raise RuntimeError(f"Downloaded file is unexpectedly small: {destination}")


def preprocess_text(value: Any) -> str:
    text = "" if pd.isna(value) else str(value)
    text = text.lower()
    text = URL_RE.sub("<URL>", text)
    text = MENTION_RE.sub("<USER>", text)
    text = SPACE_RE.sub(" ", text).strip()
    return text


def audit_split(df: pd.DataFrame, name: str) -> dict[str, Any]:
    return {
        "split": name,
        "rows": int(len(df)),
        "columns": list(df.columns),
        "missing_text": int(df["text"].isna().sum()),
        "missing_label": int(df["label"].isna().sum()),
        "exact_duplicate_rows": int(df.duplicated().sum()),
        "duplicate_text_rows": int(df.duplicated(subset=["text"], keep=False).sum()),
        "label_counts": {str(k): int(v) for k, v in df["label"].value_counts(dropna=False).items()},
    }


def metric_row(y_true: pd.Series, y_pred: np.ndarray, *, model: str, representation: str,
               cv_mean: float | None, cv_std: float | None, best_param: str) -> dict[str, Any]:
    return {
        "model": model,
        "representation": representation,
        "cv_macro_f1_mean": cv_mean,
        "cv_macro_f1_std": cv_std,
        "best_parameter": best_param,
        "test_accuracy": accuracy_score(y_true, y_pred),
        "test_macro_precision": precision_score(y_true, y_pred, average="macro", zero_division=0),
        "test_macro_recall": recall_score(y_true, y_pred, average="macro", zero_division=0),
        "test_macro_f1": f1_score(y_true, y_pred, average="macro", zero_division=0),
    }


def choose_error_category(text: str) -> str:
    """Deterministic first-pass coding; exported rows remain available for manual review."""
    low = text.lower()
    positive = ("люб", "спасиб", "крут", "красив", "хорош", "мил", "рад", "счаст", "❤", "🥰", "😍", "👍")
    negative = ("ненав", "ужас", "плох", "боль", "злю", "бесит", "сдох", "сука", "блять", "нахуй", "😔", "😭", "💀")
    has_pos = any(token in low for token in positive)
    has_neg = any(token in low for token in negative)
    if re.search(r"\b(?:не|нет|ни|никогда|нельзя|без)\b", low):
        return "отрицание"
    if has_pos and has_neg:
        return "смешанная тональность"
    if any(token in low for token in ("сарказ", "ирони", "ага", "ну да", "конечно", "лол", "ахах", "хаха", ")))", "🙃")):
        return "ирония или сарказм"
    if any(token in low for token in ("бля", "сука", "нахуй", "пизд", "аху", "кринж", "рофл", "лол", "камон")):
        return "сленг и экспрессивная лексика"
    if re.search(r"(.)\1{2,}", low) or (sum(ch.isupper() for ch in text) >= 8):
        return "нестандартная орфография"
    if "<USER>" in text or "<URL>" in text:
        return "зависимость от внешнего контекста"
    if len(text.split()) <= 4:
        return "недостаточная информация"
    return "неоднозначность или спорная разметка"


def balanced_error_sample(frame: pd.DataFrame, n: int = 60) -> pd.DataFrame:
    errors = frame.loc[frame["true_label"] != frame["predicted_label"]].copy()
    errors["pair"] = errors["true_label"] + " → " + errors["predicted_label"]
    parts: list[pd.DataFrame] = []
    groups = list(errors.groupby("pair", sort=True))
    if not groups:
        return errors
    quota = max(1, math.ceil(n / len(groups)))
    for _, group in groups:
        parts.append(group.sample(n=min(quota, len(group)), random_state=RANDOM_STATE))
    sampled = pd.concat(parts, ignore_index=True)
    if len(sampled) < n:
        remainder = errors.loc[~errors.index.isin(sampled.get("source_index", pd.Series(dtype=int)))]
        if len(remainder):
            sampled = pd.concat(
                [sampled, remainder.sample(n=min(n - len(sampled), len(remainder)), random_state=RANDOM_STATE)],
                ignore_index=True,
            )
    sampled = sampled.head(n).copy()
    sampled["error_category_initial"] = sampled["text_anonymized"].map(choose_error_category)
    return sampled.drop(columns=["pair"], errors="ignore")


def main() -> int:
    ensure_dirs()
    train_path = DATA_DIR / "rusentitweet_train.csv"
    test_path = DATA_DIR / "rusentitweet_test.csv"
    download(f"{BASE_URL}/rusentitweet_train.csv", train_path)
    download(f"{BASE_URL}/rusentitweet_test.csv", test_path)

    train_raw = pd.read_csv(train_path)
    test_raw = pd.read_csv(test_path)
    required = {"text", "label", "id"}
    for split_name, frame in (("train", train_raw), ("test", test_raw)):
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(f"{split_name}: missing required columns {sorted(missing)}")

    audit = {
        "raw": [audit_split(train_raw, "train"), audit_split(test_raw, "test")],
        "raw_exact_text_overlap_count": int(len(set(train_raw["text"].dropna()) & set(test_raw["text"].dropna()))),
    }

    train = train_raw.loc[train_raw["label"].isin(LABELS), ["text", "label", "id"]].copy()
    test = test_raw.loc[test_raw["label"].isin(LABELS), ["text", "label", "id"]].copy()
    train["text_processed"] = train["text"].map(preprocess_text)
    test["text_processed"] = test["text"].map(preprocess_text)

    empty_train = int((train["text_processed"] == "").sum())
    empty_test = int((test["text_processed"] == "").sum())
    train = train.loc[train["text_processed"] != ""].copy()
    test = test.loc[test["text_processed"] != ""].copy()

    normalized_overlap = set(train["text_processed"]) & set(test["text_processed"])
    audit["filtered"] = {
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "train_label_counts": {k: int(v) for k, v in train["label"].value_counts().items()},
        "test_label_counts": {k: int(v) for k, v in test["label"].value_counts().items()},
        "empty_processed_train_removed": empty_train,
        "empty_processed_test_removed": empty_test,
        "normalized_text_overlap_count": int(len(normalized_overlap)),
        "train_exact_duplicate_rows_retained": int(train.duplicated(subset=["text", "label", "id"]).sum()),
        "test_exact_duplicate_rows_retained": int(test.duplicated(subset=["text", "label", "id"]).sum()),
    }

    # Prevent cross-split leakage without altering the published test set.
    if normalized_overlap:
        train_model = train.loc[~train["text_processed"].isin(normalized_overlap)].copy()
    else:
        train_model = train.copy()
    test_model = test.copy()
    audit["filtered"]["training_rows_after_overlap_exclusion"] = int(len(train_model))

    pd.DataFrame(audit["raw"]).to_csv(OUT_DIR / "audit_raw_splits.csv", index=False)
    with (OUT_DIR / "audit_summary.json").open("w", encoding="utf-8") as fh:
        json.dump(audit, fh, ensure_ascii=False, indent=2)

    distribution = pd.concat([
        train_model["label"].value_counts().rename("count").rename_axis("label").reset_index().assign(split="train"),
        test_model["label"].value_counts().rename("count").rename_axis("label").reset_index().assign(split="test"),
    ], ignore_index=True)
    distribution = distribution[["split", "label", "count"]]
    distribution.to_csv(OUT_DIR / "class_distribution.csv", index=False)

    fig, ax = plt.subplots(figsize=(8, 4.8))
    pivot = distribution.pivot(index="label", columns="split", values="count").reindex(LABELS)
    pivot.plot(kind="bar", ax=ax)
    ax.set_xlabel("Класс")
    ax.set_ylabel("Количество сообщений")
    ax.set_title("Распределение классов в исследуемой выборке")
    ax.tick_params(axis="x", rotation=0)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "class_distribution.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    X_train = train_model["text_processed"]
    y_train = train_model["label"]
    X_test = test_model["text_processed"]
    y_test = test_model["label"]

    rows: list[dict[str, Any]] = []
    per_class_rows: list[dict[str, Any]] = []
    all_cv_rows: list[dict[str, Any]] = []
    fitted: dict[str, Pipeline] = {}
    predictions: dict[str, np.ndarray] = {}

    dummy = DummyClassifier(strategy="most_frequent")
    dummy.fit(np.zeros((len(y_train), 1)), y_train)
    dummy_pred = dummy.predict(np.zeros((len(y_test), 1)))
    rows.append(metric_row(y_test, dummy_pred, model="MostFrequent", representation="без признаков",
                           cv_mean=None, cv_std=None, best_param="—"))

    representations = {
        "word_1_2": TfidfVectorizer(
            analyzer="word", ngram_range=(1, 2), lowercase=False, min_df=2,
            max_df=0.98, sublinear_tf=True, max_features=120_000,
        ),
        "char_wb_3_5": TfidfVectorizer(
            analyzer="char_wb", ngram_range=(3, 5), lowercase=False, min_df=2,
            sublinear_tf=True, max_features=150_000,
        ),
    }
    models = {
        "MultinomialNB": (MultinomialNB(), {"clf__alpha": [0.1, 0.5, 1.0]}),
        "LogisticRegression": (
            LogisticRegression(max_iter=2000, random_state=RANDOM_STATE, solver="liblinear"),
            {"clf__C": [0.5, 1.0, 2.0]},
        ),
        "LinearSVC": (LinearSVC(random_state=RANDOM_STATE), {"clf__C": [0.5, 1.0, 2.0]}),
    }
    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_STATE)
    memory = Memory(location=str(CACHE_DIR), verbose=0)

    for rep_name, vectorizer in representations.items():
        for model_name, (classifier, grid) in models.items():
            key = f"{rep_name}__{model_name}"
            print(f"Training {key}", flush=True)
            pipeline = Pipeline(
                [("tfidf", clone(vectorizer)), ("clf", clone(classifier))],
                memory=memory,
            )
            search = GridSearchCV(
                pipeline,
                param_grid=grid,
                scoring="f1_macro",
                cv=cv,
                n_jobs=-1,
                refit=True,
                return_train_score=False,
            )
            search.fit(X_train, y_train)
            best_index = int(search.best_index_)
            cv_mean = float(search.cv_results_["mean_test_score"][best_index])
            cv_std = float(search.cv_results_["std_test_score"][best_index])
            pred = search.best_estimator_.predict(X_test)
            fitted[key] = search.best_estimator_
            predictions[key] = pred
            best_parameter = "; ".join(f"{k.replace('clf__', '')}={v}" for k, v in search.best_params_.items())
            rows.append(metric_row(
                y_test, pred, model=model_name, representation=rep_name,
                cv_mean=cv_mean, cv_std=cv_std, best_param=best_parameter,
            ))
            report = classification_report(y_test, pred, labels=LABELS, output_dict=True, zero_division=0)
            for label in LABELS:
                per_class_rows.append({
                    "model": model_name,
                    "representation": rep_name,
                    "label": label,
                    "precision": report[label]["precision"],
                    "recall": report[label]["recall"],
                    "f1": report[label]["f1-score"],
                    "support": int(report[label]["support"]),
                })
            for idx, params in enumerate(search.cv_results_["params"]):
                all_cv_rows.append({
                    "model": model_name,
                    "representation": rep_name,
                    "parameters": json.dumps(params, ensure_ascii=False, sort_keys=True),
                    "mean_macro_f1": float(search.cv_results_["mean_test_score"][idx]),
                    "std_macro_f1": float(search.cv_results_["std_test_score"][idx]),
                    "rank": int(search.cv_results_["rank_test_score"][idx]),
                })

    metrics = pd.DataFrame(rows)
    metrics.to_csv(OUT_DIR / "model_metrics.csv", index=False, float_format="%.6f")
    pd.DataFrame(per_class_rows).to_csv(OUT_DIR / "per_class_metrics.csv", index=False, float_format="%.6f")
    pd.DataFrame(all_cv_rows).sort_values(["representation", "model", "rank"]).to_csv(
        OUT_DIR / "cross_validation_all.csv", index=False, float_format="%.6f"
    )

    candidates = metrics.loc[metrics["model"] != "MostFrequent"].copy()
    primary_row = candidates.sort_values(
        ["cv_macro_f1_mean", "cv_macro_f1_std"], ascending=[False, True]
    ).iloc[0]
    primary_key = f"{primary_row['representation']}__{primary_row['model']}"
    primary_pred = predictions[primary_key]

    cm = confusion_matrix(y_test, primary_pred, labels=LABELS)
    pd.DataFrame(cm, index=LABELS, columns=LABELS).to_csv(OUT_DIR / "confusion_matrix.csv")
    fig, ax = plt.subplots(figsize=(6.8, 6.0))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=LABELS)
    disp.plot(ax=ax, values_format="d")
    ax.set_title(f"Матрица ошибок: {primary_row['model']} + {primary_row['representation']}")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "confusion_matrix.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    error_frame = pd.DataFrame({
        "source_index": test_model.index.to_numpy(),
        "id": test_model["id"].astype(str).to_numpy(),
        "text_anonymized": X_test.to_numpy(),
        "true_label": y_test.to_numpy(),
        "predicted_label": primary_pred,
    })
    errors = balanced_error_sample(error_frame, n=60)
    errors.to_csv(OUT_DIR / "error_sample_60.csv", index=False)
    errors["error_category_initial"].value_counts().rename_axis("category").reset_index(name="count").to_csv(
        OUT_DIR / "error_category_counts_initial.csv", index=False
    )

    summary = {
        "dataset_source": "https://github.com/sismetanin/rusentitweet",
        "random_state": RANDOM_STATE,
        "labels": LABELS,
        "primary_model_selected_by_training_cv": {
            "model": str(primary_row["model"]),
            "representation": str(primary_row["representation"]),
            "best_parameter": str(primary_row["best_parameter"]),
            "cv_macro_f1_mean": float(primary_row["cv_macro_f1_mean"]),
            "cv_macro_f1_std": float(primary_row["cv_macro_f1_std"]),
            "test_macro_f1": float(primary_row["test_macro_f1"]),
            "test_accuracy": float(primary_row["test_accuracy"]),
        },
        "audit": audit,
    }
    with (OUT_DIR / "experiment_summary.json").open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)

    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
