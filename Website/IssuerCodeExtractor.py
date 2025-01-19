from bs4 import BeautifulSoup
from typing import List
import requests

from Strategies import IssuerCodeStrategy


class IssuerCodeExtractor:

    def __init__(self, strategy: IssuerCodeStrategy):
        self._strategy = strategy

    def set_strategy(self, strategy: IssuerCodeStrategy):
        self._strategy = strategy

    def get_issuer_codes(self) -> List[str]:
        """Fetch issuer codes using the current strategy"""
        return self.filter_codes(self._strategy.get_issuer_codes())

    def filter_codes(self, codes: List[str]) -> List[str]:
        return [code for code in codes if
                not any(char.isdigit() for char in code)]