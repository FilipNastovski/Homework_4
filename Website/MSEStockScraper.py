from datetime import timedelta

import aiohttp
import pandas as pd
from bs4 import BeautifulSoup
import warnings

# no_table_codes = []

warnings.filterwarnings("ignore", category=FutureWarning, message="Passing literal html to 'read_html' is deprecated")


def clean_numeric(value):
    """Clean numeric values, handling both string and numeric inputs"""
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return float(value.replace(',', '').replace(' ', ''))
    return None


class MSEStockScraper:
    def __init__(self, issuer_code):
        self.url = f"https://www.mse.mk/en/stats/symbolhistory/{issuer_code}"
        self.symbol = issuer_code
        self.data = []
        # Column names in order as they appear
        self.column_names = [
            "Date",
            "Last Trade Price",
            "Max",
            "Min",
            "Avg. Price",
            "%chg.",
            "Volume",
            "Turnover in BEST (denars)",
            "Total turnover (denars)"
        ]
        self.columns_to_keep = [
            "Date",
            "Last Trade Price",
            "Max",
            "Min",
            "Volume",
            "Turnover in BEST (denars)"
        ]

    # async def scrape_table(self, start_date, end_date):
    #     """Scrape the data table for the entire date range and return as a DataFrame."""
    #     try:
    #         # Convert start_date and end_date to strings in "YYYY-MM-DD" format
    #         params = {
    #             "FromDate": start_date.strftime("%Y-%m-%d"),
    #             "ToDate": end_date.strftime("%Y-%m-%d")
    #         }
    #         all_data = []
    #
    #         async with aiohttp.ClientSession() as session:
    #             async with session.get(self.url, params=params) as response:
    #                 # print(f"Response Status: {response.status}")
    #                 html = await response.text()
    #                 soup = BeautifulSoup(html, "html.parser")
    #
    #                 table = soup.find("table", id="resultsTable")
    #                 if table:
    #                     # Read table without headers
    #                     df = pd.read_html(str(table), header=None)[0]
    #                     df.columns = self.column_names
    #
    #                     # Keep only the desired columns
    #                     df = df[self.columns_to_keep]
    #
    #                     # Convert numeric columns
    #                     numeric_columns = ['Last Trade Price', 'Max', 'Min', 'Volume', 'Turnover in BEST (denars)']
    #                     for col in numeric_columns:
    #                         if col in df.columns:
    #                             df[col] = df[col].apply(clean_numeric)
    #
    #                     # Convert date column to datetime
    #                     df['Date'] = pd.to_datetime(df['Date']).dt.date
    #
    #                     all_data.append(df)
    #                 else:
    #                     print(f"No table found for {self.symbol}")
    #                     # no_table_codes.append(self.symbol)
    #
    #         if all_data:
    #             final_data = pd.concat(all_data, ignore_index=True)
    #             final_data = final_data.drop_duplicates()
    #             return final_data
    #         else:
    #             print(f"No data retrieved for {self.symbol}")
    #             return None
    #
    #     except Exception as e:
    #         print(f"Error scraping table: {self.symbol} - {str(e)}")
    #         return None

    async def scrape_table(self, start_date, end_date):
        """Scrape the data table for the entire date range and return as a DataFrame."""
        try:
            # Convert start_date and end_date to strings in "YYYY-MM-DD" format
            params = {
                "FromDate": start_date.strftime("%Y-%m-%d"),
                "ToDate": end_date.strftime("%Y-%m-%d")
            }
            all_data = []

            async with aiohttp.ClientSession() as session:
                async with session.get(self.url, params=params) as response:
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")

                    table = soup.find("table", id="resultsTable")
                    if table:
                        # Read table without headers
                        df = pd.read_html(str(table), header=None)[0]
                        df.columns = self.column_names

                        # Keep only the desired columns
                        df = df[self.columns_to_keep]

                        # Convert numeric columns
                        numeric_columns = ['Last Trade Price', 'Max', 'Min', 'Volume', 'Turnover in BEST (denars)']
                        for col in numeric_columns:
                            if col in df.columns:
                                df[col] = df[col].apply(clean_numeric)

                        # Convert date column to datetime
                        df['Date'] = pd.to_datetime(df['Date']).dt.date

                        # Drop rows with missing important data (Last Trade Price, Max, Min)
                        df = df.dropna(subset=['Last Trade Price', 'Max', 'Min'])

                        # Optional: If you prefer to fill missing values instead of dropping them
                        # df['Last Trade Price'].fillna(method='ffill', inplace=True)
                        # df['Max'].fillna(method='ffill', inplace=True)
                        # df['Min'].fillna(method='ffill', inplace=True)

                        all_data.append(df)
                    else:
                        print(f"No table found for {self.symbol}")

            if all_data:
                final_data = pd.concat(all_data, ignore_index=True)
                final_data = final_data.drop_duplicates()
                return final_data
            else:
                print(f"No data retrieved for {self.symbol}")
                return None

        except Exception as e:
            print(f"Error scraping table: {self.symbol} - {str(e)}")
            return None

    async def scrape_historical_data(self, start_date, end_date):
        """Scrape data for the specified date range in yearly increments."""
        try:
            print(f"Scraping data for code: {self.symbol}")
            all_data = []  # To store the combined data from each yearly scrape

            current_start = start_date
            while current_start < end_date:
                # Calculate the end of the current one-year period
                current_end = min(current_start + timedelta(days=365), end_date)

                # Scrape data for the current year range
                data = await self.scrape_table(current_start, current_end)
                if data is not None and not data.empty:
                    all_data.append(data)
                    print(f"Scraped {len(data)} rows from {current_start} to {current_end} for {self.symbol}")
                else:
                    print(f"No data found from {current_start} to {current_end}")

                # Move to the next year
                current_start = current_end + timedelta(days=1)

            # Combine all data into a single DataFrame if any data was found
            if all_data:
                final_data = pd.concat(all_data, ignore_index=True)
                print(f"Successfully scraped {len(final_data)} rows in total for code: {self.symbol}")
                return final_data
            else:
                print(f"Scraping data for code: {self.symbol} error: NO DATA")
                return None

        except Exception as e:
            print(f"Error scraping historical data for code: {self.symbol} - {str(e)}")
            return None
