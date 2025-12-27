from flask import Flask, render_template, request
from analysis import get_columns, summarize_column, filter_by_value, get_best_cars_in_price_range
import pandas as pd

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    columns = get_columns()
    stats = None
    rows = None
    selected_col = None
    min_value = None
    recommendations = None
    min_price = None
    max_price = None
    error_message = None

    if request.method == "POST":
        # Check if this is a price range search
        min_price_raw = request.form.get("min_price")
        max_price_raw = request.form.get("max_price")
        
        if min_price_raw and max_price_raw:
            # Price range search
            try:
                min_price = float(min_price_raw)
                max_price = float(max_price_raw)
                
                if min_price < 0 or max_price < 0:
                    error_message = "Prices must be positive numbers."
                elif min_price > max_price:
                    error_message = "Minimum price cannot be greater than maximum price."
                else:
                    recommendations_df = get_best_cars_in_price_range(min_price, max_price, top_n=20)
                    if len(recommendations_df) > 0:
                        recommendations = recommendations_df.to_dict(orient="records")
                    else:
                        error_message = f"No cars found in the price range ${min_price:,.0f} - ${max_price:,.0f}"
            except ValueError:
                error_message = "Please enter valid numbers for price range."
        else:
            # Original column analysis functionality
            selected_col = request.form.get("column")
            min_value_raw = request.form.get("min_value")

            if selected_col:
                stats = summarize_column(selected_col)

            if selected_col and min_value_raw:
                try:
                    min_value = float(min_value_raw)
                    filtered = filter_by_value(selected_col, min_value)
                    rows = filtered.to_dict(orient="records")
                except ValueError:
                    min_value = None

    return render_template(
        "index.html",
        columns=columns,
        stats=stats,
        rows=rows,
        selected_col=selected_col,
        min_value=min_value,
        recommendations=recommendations,
        min_price=min_price,
        max_price=max_price,
        error_message=error_message,
    )

if __name__ == "__main__":
    app.run(debug=True)
