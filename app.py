import joblib
import numpy as np
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# Load models safely
try:
    model = joblib.load('model.pkl')
    le = joblib.load('label_encoder.pkl')
except Exception as e:
    print(f"Error loading models: {e}")

class CustomerData(BaseModel):
    total_events: float
    unique_products: float
    avg_price: float
    max_price: float
    purchase_count: float
    view_count: float
    cart_count: float
    electronics_pref: float
    unique_sessions: float
    price_range: float
    purchase_ratio: float
    cart_ratio: float
    view_ratio: float
    avg_price_log: float
    is_active_shopper: float

@app.post("/predict")
def predict_recommendation(data: CustomerData):
    try:
        # Create input array
        features = np.array([[
            data.total_events, data.unique_products, data.avg_price, 
            data.max_price, data.purchase_count, data.view_count, 
            data.cart_count, data.electronics_pref, data.unique_sessions, 
            data.price_range, data.purchase_ratio, data.cart_ratio, 
            data.view_ratio, data.avg_price_log, data.is_active_shopper
        ]])
        
        # 1. Get probabilities for all product classes
        probabilities = model.predict_proba(features)[0]
        
        # 2. Get the indices of the top 5 probabilities
        # argsort() sorts indices from low to high probability
        top_5_indices = np.argsort(probabilities)[-5:][::-1]
        
        # 3. Decode indices to original product names
        top_5_products = le.inverse_transform(top_5_indices)
        
        return {
            "status": "success",
            "recommended_products": [str(p) for p in top_5_products]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")