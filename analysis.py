import pandas as pd
import pickle
import os

# Loading Excel file (Dataset)
df = pd.read_excel("carsusedexel.xlsx") 

# Load model if it exists
_model = None
_feature_info = None

def _load_model():
    """Load the trained model if available."""
    global _model, _feature_info
    if _model is None and os.path.exists("car_model.pkl"):
        try:
            with open("car_model.pkl", "rb") as f:
                _model = pickle.load(f)
            with open("model_features.pkl", "rb") as f:
                _feature_info = pickle.load(f)
        except Exception as e:
            print(f"Error loading model: {e}")
    return _model, _feature_info

def get_columns():
    """Return the list of column names for the UI dropdown."""
    return list(df.columns)

def summarize_column(col_name):
    """Return basic stats for a selected column."""
    col = df[col_name].dropna()

    return {
        "mean": round(col.mean(), 3),
        "std": round(col.std(), 3),
        "min": round(col.min(), 3),
        "max": round(col.max(), 3),
    }

def filter_by_value(col_name, min_value):
    """Return filtered rows (first 20 only for display)."""
    filtered = df[df[col_name] >= min_value]
    return filtered.head(20)

def get_best_cars_in_price_range(min_price, max_price, top_n=20):
    """
    Get the best cars in a given price range based on value score.
    
    Args:
        min_price: Minimum price
        max_price: Maximum price
        top_n: Number of top cars to return
    
    Returns:
        DataFrame with top cars sorted by value score
    """
    # Filter by price range (handle NaN prices)
    price_filtered = df[
        (df["price"].notna()) & 
        (df["price"] >= min_price) & 
        (df["price"] <= max_price)
    ].copy()
    
    if len(price_filtered) == 0:
        return pd.DataFrame()
    
    # Load model
    model, feature_info = _load_model()
    
    if model is None:
        # If no model, use simple heuristics
        price_filtered = price_filtered.copy()
        
        # Simple scoring without model
        if "year" in price_filtered.columns:
            year_clean = price_filtered["year"].dropna()
            if len(year_clean) > 0:
                max_year = year_clean.max()
                min_year = year_clean.min()
                if max_year > min_year and pd.notna(price_filtered["year"]).any():
                    price_filtered["year_score"] = (price_filtered["year"] - min_year) / (max_year - min_year)
                    price_filtered["year_score"] = price_filtered["year_score"].fillna(0.5)
                else:
                    price_filtered["year_score"] = 0.5
            else:
                price_filtered["year_score"] = 0.5
        else:
            price_filtered["year_score"] = 0.5
        
        if "odometer" in price_filtered.columns:
            odo_clean = price_filtered["odometer"].dropna()
            if len(odo_clean) > 0:
                max_odo = odo_clean.max()
                min_odo = odo_clean.min()
                if max_odo > min_odo and pd.notna(price_filtered["odometer"]).any():
                    price_filtered["odometer_score"] = 1 - (price_filtered["odometer"] - min_odo) / (max_odo - min_odo)
                    price_filtered["odometer_score"] = price_filtered["odometer_score"].fillna(0.5)
                else:
                    price_filtered["odometer_score"] = 0.5
            else:
                price_filtered["odometer_score"] = 0.5
        else:
            price_filtered["odometer_score"] = 0.5
        
        condition_map = {
            "excellent": 1.0, "good": 0.75, "fair": 0.5,
            "like new": 1.0, "new": 1.0, "salvage": 0.25,
            "nan": 0.5, "none": 0.5, "": 0.5
        }
        if "condition" in price_filtered.columns:
            price_filtered["condition_score"] = (
                price_filtered["condition"]
                .fillna("nan")
                .astype(str)
                .str.lower()
                .map(condition_map)
                .fillna(0.5)
            )
        else:
            price_filtered["condition_score"] = 0.5
        
        price_filtered["value_score"] = (
            0.4 * price_filtered["year_score"] +
            0.3 * price_filtered["odometer_score"] +
            0.3 * price_filtered["condition_score"]
        )
    else:
        # Use trained model to predict value scores
        # Prepare features same way as training
        X = price_filtered.drop(columns=["price"], errors="ignore")
        
        # Ensure all required columns exist
        for col in feature_info["all_columns"]:
            if col not in X.columns:
                if col in feature_info["numeric_features"]:
                    X[col] = 0
                else:
                    X[col] = "nan"
        
        # Select only the columns used in training
        X = X[feature_info["all_columns"]]
        
        # Predict value scores
        try:
            value_scores = model.predict(X)
            price_filtered["value_score"] = value_scores
        except Exception as e:
            print(f"Error predicting: {e}")
            # Fallback to simple scoring
            price_filtered["value_score"] = 0.5
    
    # Sort by value score (descending) and return top N
    result = price_filtered.sort_values("value_score", ascending=False).head(top_n)
    
    # Select relevant columns for display
    display_cols = ["manufacturer", "model", "year", "price", "odometer", 
                   "condition", "fuel", "transmission", "type", "value_score"]
    available_cols = [col for col in display_cols if col in result.columns]
    
    return result[available_cols]
