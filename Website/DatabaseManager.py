from typing import List, Optional, Dict
from datetime import datetime, date, timedelta
import pandas as pd
import sqlite3


class DatabaseManager:
    """Second pipe: Manage SQLite database operations and check data currency."""

    def __init__(self, db_path: str = 'mse_stocks.db'):
        self.db_path = db_path
        # Delete existing database to ensure clean schema (USED ONLY FOR DEBUGGING)
        # if os.path.exists(db_path):
        #     os.remove(db_path)
        self.setup_database()

    def setup_database(self):
        """Create database and tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stock_data (
                    issuer_code TEXT,
                    "Date" DATE,
                    "Last Trade Price" REAL,
                    "Max" REAL,
                    "Min" REAL,
                    "Volume" REAL,
                    "Turnover in BEST (denars)" REAL,
                    PRIMARY KEY (issuer_code, "Date")
                )
            ''')
            conn.commit()

    def get_last_date(self, issuer_code: str) -> Optional[date]:
        """Get the last recorded date for an issuer."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row  # This allows fetching results as dictionaries
            cursor = conn.cursor()
            cursor.execute(
                "SELECT MAX(date) AS max_date FROM stock_data WHERE issuer_code = ?",
                (issuer_code,)
            )
            result = cursor.fetchone()
            if result and result['max_date']:
                return datetime.strptime(result['max_date'], "%Y-%m-%d").date()
            else:
                return None

    def check_data_currency(self, codes: List[str]) -> Dict[str, Optional[date]]:
        """Check which issuers need updating and their start dates for scraping."""
        today = datetime.now().date()  # Use only the date
        ten_years_ago = today - timedelta(days=365 * 10)
        update_info = {}

        for code in codes:
            last_date = self.get_last_date(code)
            if not last_date:
                # No data exists, start from 10 years ago
                update_info[code] = ten_years_ago
            elif last_date < today:
                update_info[code] = last_date + timedelta(days=1)

        return update_info

    def save_data(self, df: pd.DataFrame, issuer_code: str):
        """Save data to SQLite database with proper formatting."""
        try:
            # Create a copy and cleanup data
            save_df = df.copy()
            save_df['issuer_code'] = issuer_code

            # Ensure all columns exist and are in the right order
            required_columns = [
                'issuer_code', 'Date', 'Last Trade Price', 'Max', 'Min',
                'Volume', 'Turnover in BEST (denars)'
            ]

            # Create missing columns if needed
            for col in required_columns:
                if col not in save_df.columns:
                    save_df[col] = None

            # Select and order only the required columns
            save_df = save_df[required_columns]

            # Convert empty strings and 'None' strings to None
            save_df = save_df.replace(['', 'None', 'NULL'], None)

            # Convert numeric columns safely
            numeric_columns = ['Last Trade Price', 'Max', 'Min', 'Volume', 'Turnover in BEST (denars)']
            for col in numeric_columns:
                save_df[col] = pd.to_numeric(save_df[col], errors='coerce')

            # Convert date column
            save_df['Date'] = pd.to_datetime(save_df['Date']).dt.date

            with sqlite3.connect(self.db_path) as conn:
                save_df.to_sql('stock_data', conn, if_exists='append', index=False)

        except Exception as e:
            print(f"Error saving data for {issuer_code}: {str(e)}")
            raise

    def fetch_sample_data(self, issuer_code: Optional[str] = None, limit: int = 100):
        """Fetch a sample of data from the stock_data table, optionally filtered by issuer code."""
        with sqlite3.connect(self.db_path) as conn:
            # Construct the query with an optional WHERE clause
            if issuer_code:
                query = "SELECT * FROM stock_data WHERE issuer_code = ? LIMIT ?" #Show empty rows
                #query = "SELECT * FROM stock_data WHERE issuer_code = ? AND Volume > 0 LIMIT ?" #hide empty rows
                params = (issuer_code, limit)
            else:
                query = "SELECT * FROM stock_data WHERE Volume > 0 LIMIT ?"
                params = (limit,)

            # Execute the query with the provided parameters
            df = pd.read_sql_query(query, conn, params=params)

        # List of columns to format
        columns_to_format = [
            'Last Trade Price', 'Max', 'Min', 'Volume', 'Turnover in BEST (denars)'
        ]

        pd.set_option('display.width', 1000)
        pd.set_option('display.colheader_justify', 'center')
        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)

        # Format the numeric columns with commas and two decimal places
        for col in columns_to_format:
            df[col] = df[col].apply(lambda x: f"{x:,.2f}" if pd.notnull(x) else x)

        return df

