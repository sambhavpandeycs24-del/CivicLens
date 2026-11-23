"""Train/evaluate a category model using only labeled complaints in the database."""
import json
from collections import Counter
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.complaint import Complaint
from app.services.ml_classifier import export_model, save_model

MIN_TOTAL_EXAMPLES = 30
MIN_EXAMPLES_PER_CLASS = 4


def train_category_model(db: Session, output_path: str | Path) -> dict[str, Any]:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, classification_report
    from sklearn.model_selection import train_test_split

    complaints = list(db.scalars(select(Complaint).order_by(Complaint.created_at)))
    texts = [f"{item.title} {item.description}" for item in complaints]
    labels = [item.category.value for item in complaints]
    counts = Counter(labels)
    eligible = len(texts) >= MIN_TOTAL_EXAMPLES and len(counts) >= 2 and min(counts.values(), default=0) >= MIN_EXAMPLES_PER_CLASS
    if not eligible:
        return {
            "trained": False,
            "examples": len(texts),
            "class_counts": dict(sorted(counts.items())),
            "minimum_examples": MIN_TOTAL_EXAMPLES,
            "minimum_per_class": MIN_EXAMPLES_PER_CLASS,
            "message": "Insufficient labeled complaint data; no model was trained or written.",
        }

    train_texts, validation_texts, train_labels, validation_labels = train_test_split(
        texts,
        labels,
        test_size=max(0.2, len(counts) / len(texts)),
        random_state=42,
        stratify=labels,
    )
    validation_vectorizer = TfidfVectorizer(
        ngram_range=(1, 2), max_features=20_000, sublinear_tf=True
    )
    train_vectors = validation_vectorizer.fit_transform(train_texts)
    validation_vectors = validation_vectorizer.transform(validation_texts)
    validation_classifier = LogisticRegression(
        solver="saga", max_iter=2000, tol=1e-3, random_state=42
    )
    validation_classifier.fit(train_vectors, train_labels)
    validation_predictions = validation_classifier.predict(validation_vectors)
    metrics = {
        "validation_examples": len(validation_labels),
        "accuracy": round(float(accuracy_score(validation_labels, validation_predictions)), 4),
        "classification_report": classification_report(
            validation_labels, validation_predictions, output_dict=True, zero_division=0
        ),
    }

    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2), max_features=20_000, sublinear_tf=True
    )
    vectors = vectorizer.fit_transform(texts)
    classifier = LogisticRegression(solver="saga", max_iter=2000, tol=1e-3, random_state=42)
    classifier.fit(vectors, labels)
    model = export_model(vectorizer, classifier, metrics)
    save_model(model, output_path)
    return {
        "trained": True,
        "examples": len(texts),
        "class_counts": dict(sorted(counts.items())),
        "metrics": metrics,
        "model_path": str(output_path),
    }


def main() -> None:
    from app.db.session import SessionLocal

    with SessionLocal() as db:
        result = train_category_model(db, settings.category_model_path)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
