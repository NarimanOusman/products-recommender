from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Any, Mapping
from uuid import UUID


RAW_EVENT_COLUMNS = [
    "event_time",
    "event_type",
    "product_id",
    "category_id",
    "category_code",
    "brand",
    "price",
    "user_id",
    "user_session",
]

MODEL_FEATURE_COLUMNS = [
    "total_events",
    "unique_products",
    "avg_price",
    "max_price",
    "purchase_count",
    "view_count",
    "cart_count",
    "electronics_pref",
    "unique_sessions",
    "price_range",
    "purchase_ratio",
    "cart_ratio",
    "view_ratio",
    "avg_price_log",
    "is_active_shopper",
]

VALID_EVENT_TYPES = {"view", "cart", "purchase"}


class ValidationError(ValueError):
    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


def _to_int(value: Any, field_name: str, errors: list[str]) -> int | None:
    try:
        number = int(value)
    except (TypeError, ValueError):
        errors.append(f"{field_name} must be an integer")
        return None

    if number < 0:
        errors.append(f"{field_name} must be non-negative")
        return None

    return number


def _to_float(value: Any, field_name: str, errors: list[str]) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        errors.append(f"{field_name} must be numeric")
        return None


def _to_datetime(value: Any, field_name: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field_name} must be a non-empty datetime string")
        return None

    cleaned_value = value.strip()
    formats = [
        "%Y-%m-%d %H:%M:%S UTC",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
    ]

    for date_format in formats:
        try:
            return datetime.strptime(cleaned_value, date_format)
        except ValueError:
            continue

    errors.append(f"{field_name} must be a valid datetime")
    return None


def _to_uuid(value: Any, field_name: str, errors: list[str]) -> str | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field_name} must be a non-empty UUID string")
        return None

    try:
        return str(UUID(value.strip()))
    except (TypeError, ValueError):
        errors.append(f"{field_name} must be a valid UUID")
        return None


def validate_raw_event_row(row: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    cleaned: dict[str, Any] = {}

    missing = [column for column in RAW_EVENT_COLUMNS if column not in row]
    if missing:
        errors.append(f"Missing required columns: {', '.join(missing)}")

    event_time = _to_datetime(row.get("event_time"), "event_time", errors)
    if event_time is not None:
        cleaned["event_time"] = event_time

    event_type = row.get("event_type")
    if not isinstance(event_type, str) or event_type.strip().lower() not in VALID_EVENT_TYPES:
        errors.append("event_type must be one of: view, cart, purchase")
    else:
        cleaned["event_type"] = event_type.strip().lower()

    product_id = _to_int(row.get("product_id"), "product_id", errors)
    if product_id is not None:
        cleaned["product_id"] = product_id

    category_id = _to_int(row.get("category_id"), "category_id", errors)
    if category_id is not None:
        cleaned["category_id"] = category_id

    category_code = row.get("category_code", "")
    if category_code is None:
        category_code = ""
    if not isinstance(category_code, str):
        errors.append("category_code must be a string")
    else:
        cleaned["category_code"] = category_code.strip()

    brand = row.get("brand")
    if not isinstance(brand, str) or not brand.strip():
        errors.append("brand must be a non-empty string")
    else:
        cleaned["brand"] = brand.strip()

    price = _to_float(row.get("price"), "price", errors)
    if price is not None:
        if price < 0:
            errors.append("price must be non-negative")
        else:
            cleaned["price"] = price

    user_id = _to_int(row.get("user_id"), "user_id", errors)
    if user_id is not None:
        cleaned["user_id"] = user_id

    user_session = _to_uuid(row.get("user_session"), "user_session", errors)
    if user_session is not None:
        cleaned["user_session"] = user_session

    if errors:
        raise ValidationError(errors)

    return cleaned


def validate_raw_event_csv(csv_text: str) -> dict[str, Any]:
    reader = csv.DictReader(io.StringIO(csv_text))
    if reader.fieldnames is None:
        raise ValidationError(["CSV file is empty or missing a header row"])

    normalized_headers = [header.strip() for header in reader.fieldnames]
    if normalized_headers != RAW_EVENT_COLUMNS:
        raise ValidationError([
            f"Expected columns {RAW_EVENT_COLUMNS}, received {normalized_headers}"
        ])

    first_row = next(reader, None)
    if first_row is None:
        raise ValidationError(["CSV file must contain at least one data row"])

    return validate_raw_event_row(first_row)


def validate_prediction_payload(payload: Mapping[str, Any]) -> dict[str, float]:
    errors: list[str] = []
    cleaned: dict[str, float] = {}

    missing = [field for field in MODEL_FEATURE_COLUMNS if field not in payload]
    if missing:
        errors.append(f"Missing required fields: {', '.join(missing)}")

    for field in MODEL_FEATURE_COLUMNS:
        if field not in payload:
            continue
        value = _to_float(payload.get(field), field, errors)
        if value is not None:
            cleaned[field] = value

    if errors:
        raise ValidationError(errors)

    return cleaned
