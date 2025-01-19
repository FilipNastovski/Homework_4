import asyncio
from datetime import datetime, date
from typing import Optional, Dict
from queue import Queue, Empty
import DatabaseManager
import MSEStockScraper
import pandas as pd


class DataScraper:
    """Third pipe: Scrape and store missing data."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.queue = Queue()
        self.error_lock = asyncio.Lock()  # Use asyncio Lock for async context
        self.errors = []

    async def scrape_issuer(self, issuer_code: str, start_date: Optional[date] = None):
        """Scrape data for a single issuer from a specified start date."""
        try:
            scraper = MSEStockScraper.MSEStockScraper(issuer_code)
            today = datetime.now().date()

            # If no start_date was specified, default to fetching 10 years of data
            if not start_date:
                start_date = today - pd.Timedelta(days=365 * 10)

            # Fetch data from the specified start_date to today
            data = await scraper.scrape_historical_data(start_date, today)

            if data is not None and not data.empty:
                # Clean the DataFrame
                for col in data.columns:
                    if col != 'Date':  # Skip date column
                        data[col] = data[col].apply(MSEStockScraper.clean_numeric)

                # Save the data to the database
                self.db_manager.save_data(data, issuer_code)
            else:
                async with self.error_lock:
                    self.errors.append(f"No data retrieved for {issuer_code}")

        except Exception as e:
            async with self.error_lock:
                self.errors.append(f"Error scraping {issuer_code}: {str(e)}")

    async def process_queue(self):
        """Process items from the queue asynchronously."""
        while True:
            try:
                issuer_code, start_date = self.queue.get_nowait()
                await self.scrape_issuer(issuer_code, start_date)
                self.queue.task_done()
            except Empty:
                break
            except Exception as e:
                async with self.error_lock:
                    self.errors.append(f"Queue processing error: {str(e)}")
                self.queue.task_done()

    async def update_data(self, update_info: Dict[str, Optional[datetime]], max_concurrent_tasks: int = 200):
        """Update data for all issuers that need updating."""
        # Clear previous errors
        self.errors = []

        # Fill queue with work items
        for issuer_code, last_date in update_info.items():
            self.queue.put((issuer_code, last_date))

        # Create and start worker tasks
        tasks = [self.process_queue() for _ in range(min(max_concurrent_tasks, len(update_info)))]

        # Run tasks concurrently
        await asyncio.gather(*tasks)

        # Report any errors that occurred
        if self.errors:
            print("\nErrors encountered during scraping:")
            for error in self.errors:
                print(error)
