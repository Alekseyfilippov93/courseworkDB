import requests
from typing import Dict, List, Optional, Any
from config.config import config  # Используем config из подпапки


class HHClient:
    """Класс для взаимодействия с API HeadHunter.
    Использует библиотеку requests для получения данных о компаниях и вакансиях.
    """

    def __init__(self):
        """Инициализирует клиент, загружая URL и заголовки из конфигурации."""
        api_config = config("api")
        self.base_url = api_config.get("base_url", "https://api.hh.ru")
        self.headers = api_config.get("headers", {})
        self.max_per_page = 100  # Максимальное количество вакансий на странице

    def _make_request(
            self, url: str, params: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Приватный метод для выполнения GET-запроса с обработкой ошибок."""
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[API Error] Ошибка запроса к {url}: {e}")
            return None

    def get_employer_id(self, company_name: str) -> Optional[str]:
        """Ищет ID работодателя по его названию. Сompany_name: Название компании для поиска."""
        url = f"{self.base_url}/employers"
        params = {"text": company_name, "per_page": 1}

        data = self._make_request(url, params)

        if data and data.get("found", 0) > 0 and data.get("items"):
            return data["items"][0]["id"]

        return None

    def _fetch_all_pages(
            self, url: str, initial_params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Приватный метод для сбора данных с учетом пагинации."""
        all_items: List[Dict[str, Any]] = []
        page = 0
        total_pages = 1  # Начинаем с 1 для первого запроса

        while page < total_pages:
            params = initial_params.copy()
            params["page"] = page

            data = self._make_request(url, params)

            if not data:
                break

            items = data.get("items", [])
            all_items.extend(items)

            # Обновляем общее количество страниц только после первого запроса
            if page == 0:
                total_pages = data.get("pages", 1)

            page += 1

        return all_items

    def get_vacancies_by_employer(self, employer_id: str) -> List[Dict[str, Any]]:
        """Собирает все вакансии указанного работодателя (с пагинацией).
        employer_id: ID работодателя.
        результат  Список словарей с данными о вакансиях.
        """
        url = f"{self.base_url}/vacancies"

        initial_params = {
            "employer_id": employer_id,
            "per_page": self.max_per_page,
            "only_with_salary": True,  # Фильтр для ТЗ
        }

        return self._fetch_all_pages(url, initial_params)
