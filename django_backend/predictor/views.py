from __future__ import annotations

import csv
import json
from functools import lru_cache
from collections import Counter
from pathlib import Path

import joblib
import numpy as np
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from shared.validation import MODEL_FEATURE_COLUMNS, ValidationError, validate_prediction_payload


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = PROJECT_ROOT / "model.pkl"
LABEL_ENCODER_PATH = PROJECT_ROOT / "label_encoder.pkl"
DATA_PATH = PROJECT_ROOT / "data.csv"
COLD_START_THRESHOLD = 5


def index(request):
    return render(request, "predictor/home.html")


@lru_cache(maxsize=1)
def load_artifacts():
    model = joblib.load(MODEL_PATH)
    label_encoder = joblib.load(LABEL_ENCODER_PATH)
    return model, label_encoder


@lru_cache(maxsize=1)
def load_popular_products():
    product_counts: Counter[str] = Counter()

    with DATA_PATH.open(newline="", encoding="utf-8") as data_file:
        reader = csv.DictReader(data_file)
        for row in reader:
            product_id = row.get("product_id")
            if product_id:
                product_counts[str(product_id)] += 1

    top_products = product_counts.most_common(5)
    total_count = sum(product_counts.values()) or 1

    return [
        {
            "product_id": product_id,
            "confidence": round(count / total_count, 4),
        }
        for product_id, count in top_products
    ]


def is_cold_start(cleaned_payload):
    return float(cleaned_payload["total_events"]) < COLD_START_THRESHOLD


@csrf_exempt
def predict(request):
    if request.method == "GET":
        return render(request, "predictor/predict.html", {"feature_columns": MODEL_FEATURE_COLUMNS})

    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Only POST is allowed"}, status=405)

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON payload"}, status=400)

    try:
        cleaned_payload = validate_prediction_payload(payload)
    except ValidationError as exc:
        return JsonResponse({"status": "error", "message": "Validation failed", "errors": exc.errors}, status=400)

    try:
        if is_cold_start(cleaned_payload):
            recommendations = load_popular_products()
            prediction_mode = "cold_start"
            message = "No customer history yet, so we are showing popular products."
        else:
            model, label_encoder = load_artifacts()
            features = np.array([[cleaned_payload[field] for field in MODEL_FEATURE_COLUMNS]], dtype=float)
            probabilities = model.predict_proba(features)[0]
            top_5_indices = np.argsort(probabilities)[-5:][::-1]
            top_5_products = label_encoder.inverse_transform(top_5_indices)

            recommendations = []
            for index, product_id in enumerate(top_5_products):
                confidence = float(probabilities[top_5_indices[index]])
                recommendations.append(
                    {
                        "product_id": str(product_id),
                        "confidence": round(confidence, 4),
                    }
                )
            prediction_mode = "model"
            message = "Recommendations generated from customer activity."
    except Exception as exc:  # noqa: BLE001
        return JsonResponse({"status": "error", "message": f"Prediction failed: {exc}"}, status=500)

    return JsonResponse(
        {
            "status": "success",
            "prediction_mode": prediction_mode,
            "message": message,
            "recommended_products": recommendations,
        }
    )
