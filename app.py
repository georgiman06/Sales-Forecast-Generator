from flask import Flask, render_template, request, jsonify, redirect, url_for
import pandas as pd
from io import StringIO
import uuid
import sys, os, json
from datetime import datetime

# ---------------------------------------------------------
# Import your forecasting model
# ---------------------------------------------------------
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from forecast_model import train_and_forecast

# ---------------------------------------------------------
# Flask setup
# ---------------------------------------------------------
app = Flask(__name__)

# ---------------------------------------------------------
# Persistent storage setup
# ---------------------------------------------------------
JOBS_FILE = "jobs_cache.json"
JOBS = {}  # in-memory reference to forecasts


def save_jobs():
    """Save minimal forecast metadata persistently to disk."""
    try:
        serializable = {}
        for job_id, job in JOBS.items():
            # Only save what’s JSON-safe
            serializable[job_id] = {
                "timestamp": datetime.now().isoformat(),
                "metrics": job.get("metrics", {}),
            }
        with open(JOBS_FILE, "w") as f:
            json.dump(serializable, f)
        print(f"💾 Saved {len(JOBS)} job(s) to {JOBS_FILE}")
    except Exception as e:
        print("⚠️ Failed to save jobs:", e)


def load_jobs():
    """Reload saved jobs metadata from disk."""
    global JOBS
    if os.path.exists(JOBS_FILE):
        try:
            with open(JOBS_FILE, "r") as f:
                saved = json.load(f)
                JOBS.update(saved)
            print(f"🔁 Loaded {len(JOBS)} previous job(s) from {JOBS_FILE}")
        except Exception as e:
            print("⚠️ Failed to load jobs:", e)
    else:
        print("ℹ️ No saved job cache found — starting fresh.")


# Load any saved jobs at startup
load_jobs()


# ---------------------------------------------------------
# Pages
# ---------------------------------------------------------
@app.route("/")
def index():
    """Landing page"""
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    """Upload and configuration page"""
    return render_template("dashboard.html")


@app.route("/results")
def results():
    job_id = request.args.get("job_id")
    if not job_id:
        return "Missing job_id in URL", 400
    return render_template("results.html", job_id=job_id)


# ---------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------
@app.route("/api/preview", methods=["POST"])
def api_preview():
    """Preview first few rows of uploaded CSV"""
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "No file uploaded"}), 400

    df = pd.read_csv(f)
    headers = df.columns.tolist()
    preview_rows = df.head(200)
    return jsonify({
        "headers": headers,
        "rows": preview_rows.astype(str).values.tolist()
    })


@app.route("/api/upload", methods=["POST"])
def api_upload():
    """Train forecast model and store result persistently"""
    f = request.files.get("file")
    date_col = request.form.get("date_col")
    target_col = request.form.get("target_col")
    horizon = int(request.form.get("horizon", 30))

    if not f or not date_col or not target_col:
        return jsonify({"error": "file, date_col, and target_col are required"}), 400

    df = pd.read_csv(f)
    print("\n=== /api/upload CALLED ===")
    print("Date Column:", date_col)
    print("Target Column:", target_col)
    print("Rows in uploaded CSV:", len(df))

    try:
        result = train_and_forecast(df, date_col, target_col, horizon)
    except Exception as e:
        print("❌ Forecast error:", e)
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    job_id = uuid.uuid4().hex
    JOBS[job_id] = {
        "forecast": result["forecast"],
        "series": result["series"],
        "layout": result["layout"],
        "metrics": result["metrics"]
    }

    # Save persistent job info
    save_jobs()

    print(f"✅ Job stored successfully with ID: {job_id}")
    return jsonify({"job_id": job_id, "redirect_url": f"/results?job_id={job_id}"})


from plotly.utils import PlotlyJSONEncoder
import json

from plotly.utils import PlotlyJSONEncoder
import json
from flask import make_response

@app.route("/api/result")
def api_result():
    job_id = request.args.get("job_id")
    print("\n=== /api/result CALLED ===")
    print("Requested Job ID:", job_id)

    job = JOBS.get(job_id)
    if not job:
        print("ERROR: Job not found in JOBS dict.")
        return jsonify({"error": "Invalid or expired job_id"}), 404

    fc = job.get("forecast")
    if fc is None:
        print("ERROR: Forecast missing from job.")
        return jsonify({"error": "Forecast missing"}), 500

    print("Returning forecast rows:", len(fc))

    # ✅ Use PlotlyJSONEncoder for safe serialization
    response = {
        "forecast": fc.to_dict(orient="records"),
        "series": job["series"],
        "layout": job["layout"],
        "metrics": job.get("metrics", {})
    }

    # ✅ This block replaces the old "return jsonify(...)"
    resp = make_response(json.dumps(response, cls=PlotlyJSONEncoder))
    resp.headers["Content-Type"] = "application/json"
    resp.headers["Content-Encoding"] = "utf-8"
    return resp



# ---------------------------------------------------------
# Run App
# ---------------------------------------------------------
if __name__ == "__main__":
    # debug=True is fine now, since we persist jobs
    app.run(debug=True, use_reloader=True)

import webbrowser
from threading import Timer

if __name__ == "__main__":
    # Automatically open intro page after server starts
    def open_browser():
        webbrowser.open_new("http://127.0.0.1:5000/index/")

    Timer(1.5, open_browser).start()  # wait 1.5s for Flask to start
    app.run(debug=True, port=5000)
