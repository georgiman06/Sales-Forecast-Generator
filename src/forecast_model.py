import pandas as pd
import numpy as np
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder
import json


# ======================================================
# 1️⃣ MAIN FORECAST FUNCTION
# ======================================================
def train_and_forecast(df, date_col, target_col, horizon=30):
    """
    Train a Prophet model on the provided dataframe and forecast into the future.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe with date and target columns.
    date_col : str
        Name of the datetime column.
    target_col : str
        Name of the target variable column.
    horizon : int
        Number of days to forecast forward.

    Returns
    -------
    dict
        {
            "forecast": pd.DataFrame,
            "series": list (for Plotly trace),
            "layout": dict (for Plotly figure layout),
            "metrics": dict (MAE, RMSE, MAPE)
        }
    """
    print("\n🚀 Starting train_and_forecast()")
    print(f"Columns received: {list(df.columns)}")
    print(f"Date column: {date_col} | Target column: {target_col} | Horizon: {horizon}")

    # --- Data prep ---
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col, target_col])
    df = df.sort_values(by=date_col)

    if df.empty:
        raise ValueError("No valid data rows after cleaning date/target columns.")

    prophet_df = df.rename(columns={date_col: "ds", target_col: "y"})
    print(f"✅ Data prepared: {len(prophet_df)} rows")

    # --- Train model ---
    model = Prophet(daily_seasonality=True, yearly_seasonality=True)
    model.fit(prophet_df)
    print("✅ Prophet model training complete")

    # --- Forecast ---
    future = model.make_future_dataframe(periods=horizon)
    forecast = model.predict(future)
    print(f"✅ Forecast generated: {len(forecast)} total rows")

    # --- Evaluation ---
    forecast_merged = forecast.merge(prophet_df, on="ds", how="left", suffixes=("", "_true"))

    if "y_true" in forecast_merged.columns:
        y_true = forecast_merged["y_true"]
    elif "y" in forecast_merged.columns:
        y_true = forecast_merged["y"]
    else:
        print("⚠️ Warning: No ground truth column found for evaluation — skipping metrics.")
        return {
            "forecast": forecast,
            "series": [],
            "layout": {},
            "metrics": {"MAE": np.nan, "RMSE": np.nan, "MAPE": np.nan}
        }

    y_pred = forecast_merged["yhat"]
    mask = y_true.notna()
    y_true = y_true[mask]
    y_pred = y_pred[mask]

    # Compute metrics safely
    try:
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        mape = np.mean(np.abs((y_true - y_pred) / y_true.replace(0, np.nan))) * 100
    except Exception as e:
        print("⚠️ Metric calculation failed:", e)
        mae, rmse, mape = np.nan, np.nan, np.nan

    print(f"✅ Evaluation metrics — MAE: {mae:.2f}, RMSE: {rmse:.2f}, MAPE: {mape:.2f}")

    metrics = {
        "MAE": round(mae, 2),
        "RMSE": round(rmse, 2),
        "MAPE": round(mape, 2)
    }

    # --- Plotly figure data ---
    # Start with traces hidden — user toggles via legend
    # Forecast start point helps visually separate training vs. forecast
    cutoff_date = prophet_df["ds"].max()

    series = [
        go.Scatter(
            x=prophet_df["ds"],
            y=prophet_df["y"],
            name="Actual",
            mode="lines+markers",
            visible="legendonly",
            line=dict(color="lightblue", width=2)
        ),
        go.Scatter(
            x=forecast["ds"],
            y=forecast["yhat"],
            name="Forecast",
            mode="lines",
            visible="legendonly",
            line=dict(color="orange", width=2)
        ),
        go.Scatter(
            x=forecast["ds"],
            y=forecast["yhat_upper"],
            name="Upper Bound",
            mode="lines",
            line=dict(dash="dot", color="green"),
            visible="legendonly"
        ),
        go.Scatter(
            x=forecast["ds"],
            y=forecast["yhat_lower"],
            name="Lower Bound",
            mode="lines",
            line=dict(dash="dot", color="red"),
            visible="legendonly"
        ),
        # Optional vertical line marking forecast start
        go.Scatter(
            x=[cutoff_date, cutoff_date],
            y=[forecast["yhat_lower"].min(), forecast["yhat_upper"].max()],
            mode="lines",
            name="Forecast Start",
            line=dict(color="white", width=1, dash="dash"),
            visible="legendonly"
        )
    ]

    layout = dict(
        title=f"{target_col} Forecast",
        xaxis_title=date_col,
        yaxis_title=target_col,
        template="plotly_dark",
        legend=dict(
            title="Click to toggle series",
            bgcolor="rgba(0,0,0,0)",
            font=dict(color="white")
        ),
        hovermode="x unified"
    )

    print("✅ Returning forecast results")

    # --- Return everything ---
    return {
        "forecast": forecast,
        "series": series,
        "layout": layout,
        "metrics": metrics
    }
