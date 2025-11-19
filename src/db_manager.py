import psycopg2
from typing import Any, Dict, List, Optional


class DBManager:
    """
    Класс для управления и выполнения SQL-запросов к БД.
    Реализует методы, требуемые техническим заданием.
    """

    def __init__(self, database_name: str, params: Dict[str, Any]):
        """Инициализирует менеджер с параметрами подключения."""
        self.database_name = database_name
        self.params = params

    def _execute_query(self, query: str, data: Optional[tuple] = None) -> List[tuple]:
        """Приватный метод для выполнения SQL-запроса."""
        results = []
        conn = None
        try:
            # Используем контекстный менеджер для автоматического закрытия
            conn = psycopg2.connect(dbname=self.database_name, **self.params)
            with conn.cursor() as cur:
                cur.execute(query, data)
                if cur.description:
                    results = cur.fetchall()
        except psycopg2.Error as e:
            print(f"[DB Manager Error] Ошибка выполнения запроса: {e}")
        finally:
            if conn:
                conn.close()
        return results

    def get_companies_and_vacancies_count(self) -> List[tuple]:
        """Получает список всех компаний и количество вакансий."""
        query = """
            SELECT c.company_name, COUNT(v.vacancy_id)
            FROM companies c
            LEFT JOIN vacancies v ON c.company_id = v.company_id
            GROUP BY c.company_name
            ORDER BY COUNT(v.vacancy_id) DESC;
        """
        return self._execute_query(query)

    def get_all_vacancies(self) -> List[tuple]:
        """Получает список всех вакансий (компания, название, зарплата, ссылка)."""
        query = """
            SELECT c.company_name, v.vacancy_title,
                   COALESCE(CONCAT(v.salary_from, ' - ', v.salary_to, ' ', v.salary_currency), 'Зарплата не указана'),
                   v.vacancy_url
            FROM vacancies v
            JOIN companies c ON v.company_id = c.company_id;
        """
        return self._execute_query(query)

    def get_avg_salary(self) -> Optional[float]:
        """Получает среднюю зарплату 'от' по вакансиям."""
        query = "SELECT AVG(salary_from) FROM vacancies WHERE salary_from IS NOT NULL;"
        result = self._execute_query(query)
        # Упрощаем возврат: None, если нет данных
        return result[0][0] if result and result[0][0] else None

    def get_vacancies_with_higher_salary(self) -> List[tuple]:
        """Получает список вакансий, у которых зарплата 'от' выше средней."""
        query = """
            SELECT c.company_name, v.vacancy_title, v.salary_from, v.vacancy_url
            FROM vacancies v
            JOIN companies c ON v.company_id = c.company_id
            WHERE v.salary_from > (
                SELECT AVG(salary_from) FROM vacancies WHERE salary_from IS NOT NULL
            )
            ORDER BY v.salary_from DESC;
        """
        return self._execute_query(query)

    def get_vacancies_with_keyword(self, keyword: str) -> List[tuple]:
        """Получает список вакансий, в названии которых содержится ключевое слово."""
        lower_keyword = keyword.lower()

        query = """
            SELECT c.company_name, v.vacancy_title, v.salary_from, v.vacancy_url
            FROM vacancies v
            JOIN companies c ON v.company_id = c.company_id
            WHERE v.vacancy_title ILIKE %s;
            -- ILIKE %s уже нечувствителен к регистру, но приводим его к нижнему регистру для надежности
            WHERE v.vacancy_title ILIKE %s;
        """
        return self._execute_query(query, (f"%{keyword}%",))
