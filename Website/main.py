import IssuerCodeExtractor
from Strategies import *
import DatabaseManager
import DataScraper
import asyncio


async def main():
    try:

        # Strategy can be selected in runtime but for the current requirements there's no need
        strategy = DropdownIssuerCodeStrategy("https://www.mse.mk/en/stats/symbolhistory/ADIN")

        first_pipe = IssuerCodeExtractor.IssuerCodeExtractor(strategy)
        second_pipe = DatabaseManager.DatabaseManager()
        third_pipe = DataScraper.DataScraper(second_pipe)

        print("Getting issuer codes...")
        issuer_codes = first_pipe.get_issuer_codes()
        print(f"Found {len(issuer_codes)} valid issuer codes\n")

        print("Checking data currency...")
        update_info = second_pipe.check_data_currency(issuer_codes)
        print(f"{len(update_info)} issuers need updating\n")

        if update_info:
            print("Starting data update...\n")
            await third_pipe.update_data(update_info=update_info)
            print("\nData update completed\n")
        else:
            print("All data is up to date")


    except Exception as e:
        print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
