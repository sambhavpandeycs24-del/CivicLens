"""JSON-backed TF-IDF/logistic classifier with no executable model deserialization."""
import json
import math
import os
import re
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.models.complaint import ComplaintCategory

MODEL_FORMAT_VERSION = 1
MAX_MODEL_BYTES = 50 * 1024 * 1024
TOKEN_PATTERN = re.compile(r"(?u)\b\w\w+\b")


def export_model(vectorizer: Any, classifier: Any, metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "format_version": MODEL_FORMAT_VERSION,
        "algorithm": "tfidf_logistic_regression",
        "vocabulary": {term: int(index) for term, index in vectorizer.vocabulary_.items()},
        "idf": vectorizer.idf_.tolist(),
        "sublinear_tf": bool(vectorizer.sublinear_tf),
        "ngram_max": 2,
        "classes": classifier.classes_.tolist(),
        "coefficients": classifier.coef_.tolist(),
        "intercepts": classifier.intercept_.tolist(),
        "metrics": metrics,
    }


def save_model(model: dict[str, Any], path: str | Path) -> None:
    model = _validate_model(model)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=destination.parent, delete=False
        ) as output:
            temporary_path = Path(output.name)
            json.dump(model, output, ensure_ascii=True, allow_nan=False)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary_path, destination)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
    _load_model_cached.cache_clear()


def _validate_model(model: Any) -> dict[str, Any]:
    if not isinstance(model, dict) or model.get("format_version") != MODEL_FORMAT_VERSION:
        raise ValueError("Unsupported or invalid category model format")
    if model.get("algorithm") != "tfidf_logistic_regression":
        raise ValueError("Unsupported category model algorithm")
    vocabulary = model.get("vocabulary")
    idf = model.get("idf")
    classes = model.get("classes")
    coefficients = model.get("coefficients")
    intercepts = model.get("intercepts")
    if not isinstance(vocabulary, dict) or not vocabulary or len(vocabulary) > 200_000:
        raise ValueError("Invalid category model vocabulary")
    if not isinstance(classes, list) or len(classes) < 2:
        raise ValueError("Invalid category model classes")
    allowed_labels = {category.value for category in ComplaintCategory}
    if (
        not all(isinstance(label, str) and label in allowed_labels for label in classes)
        or len(set(classes)) != len(classes)
    ):
        raise ValueError("Invalid category model class labels")
    if type(model.get("sublinear_tf")) is not bool:
        raise ValueError("Invalid category model term-frequency setting")
    ngram_max = model.get("ngram_max", 1)
    if type(ngram_max) is not int or ngram_max not in (1, 2):
        raise ValueError("Invalid category model n-gram setting")
    feature_count = len(vocabulary)
    indices = list(vocabulary.values())
    if not all(type(index) is int and 0 <= index < feature_count for index in indices):
        raise ValueError("Invalid category model feature indices")
    if not all(isinstance(term, str) for term in vocabulary):
        raise ValueError("Invalid category model feature terms")
    if len(set(indices)) != feature_count:
        raise ValueError("Duplicate category model feature indices")
    if not isinstance(idf, list) or len(idf) != feature_count:
        raise ValueError("Invalid category model IDF weights")
    expected_rows = 1 if len(classes) == 2 else len(classes)
    if not isinstance(coefficients, list) or len(coefficients) != expected_rows:
        raise ValueError("Invalid category model coefficients")
    if any(not isinstance(row, list) or len(row) != feature_count for row in coefficients):
        raise ValueError("Invalid category model coefficient dimensions")
    if not isinstance(intercepts, list) or len(intercepts) != expected_rows:
        raise ValueError("Invalid category model intercepts")
    values = idf + intercepts + [weight for row in coefficients for weight in row]
    if not all(
        isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
        for value in values
    ):
        raise ValueError("Category model contains invalid numeric values")
    return model


@lru_cache(maxsize=4)
def _load_model_cached(path: str, modified_ns: int) -> dict[str, Any]:
    del modified_ns
    source = Path(path)
    if source.stat().st_size > MAX_MODEL_BYTES:
        raise ValueError("Category model file exceeds the maximum allowed size")
    with source.open("r", encoding="utf-8") as model_file:
        return _validate_model(json.load(model_file))


def load_model(path: str | Path) -> dict[str, Any] | None:
    source = Path(path)
    if not source.exists():
        return None
    return _load_model_cached(str(source.resolve()), source.stat().st_mtime_ns)


def predict(text: str, model: dict[str, Any]) -> tuple[str, float]:
    model = _validate_model(model)
    vocabulary = model["vocabulary"]
    tokens = TOKEN_PATTERN.findall(text.lower())
    features = list(tokens)
    if model.get("ngram_max", 1) >= 2:
        features.extend(f"{tokens[index]} {tokens[index + 1]}" for index in range(len(tokens) - 1))
    counts: dict[int, int] = {}
    for token in features:
        index = vocabulary.get(token)
        if index is not None:
            counts[index] = counts.get(index, 0) + 1
    vector = {
        index: (1.0 + math.log(count) if model.get("sublinear_tf") else count) * model["idf"][index]
        for index, count in counts.items()
    }
    norm = math.sqrt(sum(value * value for value in vector.values()))
    if not norm:
        return model["classes"][0], 0.0
    vector = {index: value / norm for index, value in vector.items()}

    scores = [
        model["intercepts"][row] + sum(
            vector.get(index, 0.0) * weight
            for index, weight in enumerate(model["coefficients"][row])
        )
        for row in range(len(model["coefficients"]))
    ]
    if len(model["classes"]) == 2:
        positive = 1.0 / (1.0 + math.exp(-max(-700.0, min(700.0, scores[0]))))
        probabilities = [1.0 - positive, positive]
    else:
        maximum = max(scores)
        exponentials = [math.exp(score - maximum) for score in scores]
        total = sum(exponentials)
        probabilities = [value / total for value in exponentials]
    best = max(range(len(probabilities)), key=probabilities.__getitem__)
    return model["classes"][best], round(probabilities[best], 4)
