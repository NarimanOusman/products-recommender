from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from shared.validation import MODEL_FEATURE_COLUMNS, ValidationError, validate_prediction_payload


PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODEL_PATH = PROJECT_ROOT / "model.pkl"
LABEL_ENCODER_PATH = PROJECT_ROOT / "label_encoder.pkl"


def index(request):
    return render(request, "predictor/predict.html", {"feature_columns": MODEL_FEATURE_COLUMNS})


@lru_cache(maxsize=1)
def load_artifacts():
    model = joblib.load(MODEL_PATH)
    label_encoder = joblib.load(LABEL_ENCODER_PATH)
    return model, label_encoder


@csrf_exempt
def predict(request):
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
        model, label_encoder = load_artifacts()
        features = np.array([[cleaned_payload[field] for field in MODEL_FEATURE_COLUMNS]], dtype=float)
        probabilities = model.predict_proba(features)[0]
        top_5_indices = np.argsort(probabilities)[-5:][::-1]
        top_5_products = label_encoder.inverse_transform(top_5_indices)
    except Exception as exc:  # noqa: BLE001
        return JsonResponse({"status": "error", "message": f"Prediction failed: {exc}"}, status=500)

    return JsonResponse(
        {
            "status": "success",
            "recommended_products": [str(product) for product in top_5_products],
        }
    )
