# Stock Data Scraper - Refactoring and Deployment

## Refactoring

### Code Improvements
The code has been refactored to ensure clarity, maintainability, and scalability. This includes the following:

- **Consistent Naming Scheme**: All variables, classes, and methods follow a consistent naming scheme to improve readability and ease of understanding.
- **Comments and Documentation**: Extensive comments throughout the codebase to describe the purpose of each class and method.
- **No Repeated Code**: Repetitive code segments have been removed or refactored into reusable methods.

### Strategy Pattern for Issuer Code Extraction

One of the most significant changes I made was the introduction of the **Strategy Pattern** in the `IssuerCodeExtractor` class. This class previously had issues when scraping issuer codes from the dropdown menu on the MSE website, as sometimes the dropdown was not available. This caused the scraping algorhitm to fail and broke the code for many users, including myself.

To address this, I refactored the code to use the Strategy Pattern, which allows the algorithm to be changed dynamically based on the availability of the dropdown. This made the code more resilient to changes in the website's structure.

This approach significantly improves the robustness of the program and ensures that it doesn't break when faced with unexpected changes on the MSE website.

#### IssuerCodeExtractor Class

The `IssuerCodeExtractor` class uses the **Strategy Pattern** to switch between strategies. It has a **Single Responsibility** and each strategy has a clear responsibility of its own. This ensures that each class adheres to the **Single Responsibility Principle (SRP)**, making the system easy to extend or modify in the future.

```python
class IssuerCodeExtractor:

    def __init__(self, strategy: IssuerCodeStrategy):
        self._strategy = strategy

    def set_strategy(self, strategy: IssuerCodeStrategy):
        self._strategy = strategy

    def get_issuer_codes(self) -> List[str]:
        """Fetch issuer codes using the current strategy"""
        return self.filter_codes(self._strategy.get_issuer_codes())
```

Here’s an example of a concrete implementation of the class:
```python
import requests
from bs4 import BeautifulSoup
from typing import List

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
```

## Containerization and Deployment

The application is designed to be **lightweight** and **fast**, ensuring that it runs efficiently even on low-resource environments. By using a minimal Python base image (`python:3.12-slim`) for the Docker container, the program benefits from a small footprint, reducing unnecessary overhead.

The container itself is **small and simple**, with only the essential dependencies and files included. This allows for faster build times, quicker deployments, and lower resource consumption. The simplicity of the container ensures that it can be easily maintained and deployed without excessive complexity.

I containerized the application using **Docker Desktop** and deployed it to **Render**. Below is the `Dockerfile` used for containerization:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app/
EXPOSE 5000
ENV FLASK_ENV=production
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
```

## Important Notice

Please note that the **first time loading the website** may take a little while, as the container is stopped if there are no requests for some time. Once the container is running, the website will load normally.

Additionally, there is **no need to click "Scrape Data" or "Run Analysis"**, as those actions are used to invoke backend scripts that fill the database with data. In this case, the database is already full, and all available data can be viewed by selecting an issuer code and clicking the **"Fetch Data"** button.

You can access the application through the link below:

Website Link: https://homework-4-das.onrender.com
