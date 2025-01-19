from flask import Flask, render_template, jsonify, request
import sqlite3
import subprocess
import pandas as pd

app = Flask(__name__)

DATABASE_PATH = "mse_stocks.db"

# Home page route
@app.route('/')
def home():
    return render_template('index.html')

# Route to run main.py (filling issuer_codes table)
@app.route('/scrape_data', methods=['POST'])
def scrape_data():
    try:
        subprocess.run(["python", "main.py"], check=True)
        return jsonify({"message": "Data scraped successfully."}), 200
    except subprocess.CalledProcessError as e:
        return jsonify({"message": f"Error running main script: {str(e)}"}), 500

# Route to run TechnicalAnalysis.py
@app.route('/run_analysis', methods=['POST'])
def run_analysis():
    try:
        subprocess.run(["python", "TechnicalAnalysis.py"], check=True)
        return jsonify({"message": "Technical analysis completed successfully."}), 200
    except subprocess.CalledProcessError as e:
        return jsonify({"message": f"Error running technical analysis script: {str(e)}"}), 500

# Route to fetch issuer codes (for dropdown)
@app.route('/get_issuer_codes', methods=['GET'])
def get_issuer_codes():
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        query = "SELECT DISTINCT issuer_code FROM stock_data ORDER BY issuer_code"
        issuer_codes = pd.read_sql_query(query, conn)['issuer_code'].tolist()
        conn.close()
        return jsonify(issuer_codes), 200
    except Exception as e:
        return jsonify({"message": f"Error fetching issuer codes: {str(e)}"}), 500

@app.route('/fetch_latest_analysis', methods=['GET'])
def fetch_latest_analysis():
    try:
        issuer_code = request.args.get('issuer_code')
        time_period = request.args.get('time_period')

        if not all([issuer_code, time_period]):
            return jsonify({"message": "Missing required parameters."}), 400

        # Validate time period
        valid_periods = ['daily', 'weekly', 'monthly']
        if time_period not in valid_periods:
            return jsonify({"message": "Invalid time period selected."}), 400

        query = """
            SELECT * FROM technical_indicators 
            WHERE issuer_code = ? AND time_period = ? 
            ORDER BY Date DESC LIMIT 1
        """

        conn = sqlite3.connect(DATABASE_PATH)
        df = pd.read_sql_query(query, conn, params=(issuer_code, time_period))
        conn.close()

        if df.empty:
            return jsonify({"message": "No data available for the selected criteria."}), 404

        # Replace NaN/NULL with "No Data"
        df = df.fillna("No Data")

        return jsonify(df.to_dict(orient='records')), 200
    except Exception as e:
        return jsonify({"message": f"Error fetching latest analysis data: {str(e)}"}), 500

@app.route('/fetch_historical_analysis', methods=['GET'])
def fetch_historical_analysis():
    try:
        issuer_code = request.args.get('issuer_code')
        time_period = request.args.get('time_period')

        if not all([issuer_code, time_period]):
            return jsonify({"message": "Missing required parameters."}), 400

        # Validate time period
        valid_periods = ['daily', 'weekly', 'monthly']
        if time_period not in valid_periods:
            return jsonify({"message": "Invalid time period selected."}), 400

        query = """
            SELECT * FROM technical_indicators 
            WHERE issuer_code = ? AND time_period = ? 
            ORDER BY Date DESC LIMIT 100
        """

        conn = sqlite3.connect(DATABASE_PATH)
        df = pd.read_sql_query(query, conn, params=(issuer_code, time_period))
        conn.close()

        if df.empty:
            return jsonify({"message": "No data available for the selected criteria."}), 404

        # Replace NaN/NULL with "No Data"
        df = df.fillna("No Data")

        return jsonify(df.to_dict(orient='records')), 200
    except Exception as e:
        return jsonify({"message": f"Error fetching historical analysis data: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)