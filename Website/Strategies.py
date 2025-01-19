from abc import abstractmethod, ABC
from bs4 import BeautifulSoup
from typing import List
import requests


# Abstract Base Class for Strategy
class IssuerCodeStrategy(ABC):
    @abstractmethod
    def get_issuer_codes(self) -> List[str]:
        """Fetch issuer codes"""
        pass


# Concrete Strategy: Fetch codes from a dropdown
class DropdownIssuerCodeStrategy(IssuerCodeStrategy):
    def __init__(self, url: str):
        self.url = url

    def get_issuer_codes(self) -> List[str]:
        response = requests.get(self.url)
        soup = BeautifulSoup(response.content, 'html.parser')

        dropdown = soup.find('select', {'id': 'Code'})
        options = dropdown.find_all('option')
        codes = [option['value'] for option in options if option['value']]

        return codes


# Concrete Strategy: Fetch codes from a table
class TableIssuerCodeStrategy(IssuerCodeStrategy):
    def __init__(self, urls: List[str]):
        self.urls = urls

    def get_issuer_codes(self) -> List[str]:
        all_codes = []
        for url in self.urls:
            try:
                response = requests.get(url)
                response.raise_for_status()  # Raise an exception for bad status codes
                soup = BeautifulSoup(response.content, 'html.parser')

                table = soup.find('table', {'id': 'otherlisting-table'})
                if table:
                    rows = table.find_all('tr')
                    for row in rows:
                        columns = row.find_all('td')
                        if columns:  # Make sure row has columns
                            symbol = columns[0].get_text(strip=True)
                            if symbol:
                                all_codes.append(symbol)
            except requests.RequestException as e:
                print(f"Error fetching data from {url}: {e}")

        # Remove duplicates while preserving order
        unique_codes = list(dict.fromkeys(all_codes))
        return unique_codes
