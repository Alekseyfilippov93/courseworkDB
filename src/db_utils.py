import psycopg2
from typing import Any, Dict, List


def create_database(database_name: str, params: Dict[str, Any]) -> None:
    """Создает новую базу данных PostgreSQL."""
    conn = None
    try:
        # Убираем имя целевой БД для подключения к 'postgres'
        temp_params = {k: v for k, v in params.items() if k != "database"}
        conn = psycopg2.connect(dbname="postgres", **temp_params)
        conn.autocommit = True
        cur = conn.cursor()

        cur.execute(f"DROP DATABASE IF EXISTS {database_name}")
        cur.execute(f"CREATE DATABASE {database_name}")
        print(f"[DB] База данных '{database_name}' создана.")
    except psycopg2.Error as e:
        print(f"[DB Error] Ошибка создания БД: {e}")
    finally:
        if conn:
            conn.close()


def create_tables(conn: psycopg2.connect) -> None:
    """Создает таблицы 'companies' и 'vacancies'."""
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS companies (
                company_id INT PRIMARY KEY,
                company_name VARCHAR(255) NOT NULL
            )
        """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS vacancies (
                vacancy_id INT PRIMARY KEY,
                company_id INT REFERENCES companies(company_id) ON DELETE CASCADE,
                vacancy_title VARCHAR(255) NOT NULL,
                salary_from INT,
                salary_to INT,
                salary_currency VARCHAR(10),
                vacancy_url TEXT NOT NULL
            )
        """
        )
    conn.commit()
    print("[DB] Таблицы созданы.")


def insert_data_to_tables(
    conn: psycopg2.connect, companies_data: List[Dict], vacancies_data: List[Dict]
) -> None:
    """Заполняет таблицы данными о работодателях и их вакансиях."""
    with conn.cursor() as cur:
        # --- Вставка компаний ---
        for company in companies_data:
            cur.execute(
                """
                INSERT INTO companies (company_id, company_name)
                VALUES (%s, %s) ON CONFLICT (company_id) DO NOTHING;
            """,
                (company["id"], company["name"]),
            )

        # --- Вставка вакансий ---
        for vacancy in vacancies_data:
            salary = vacancy.get("salary")

            # Извлекаем данные, используя .get() для безопасного доступа
            salary_from = salary.get("from") if salary else None
            salary_to = salary.get("to") if salary else None
            salary_currency = salary.get("currency") if salary else None

            try:
                cur.execute(
                    """
                    INSERT INTO vacancies (vacancy_id, company_id, vacancy_title, salary_from, salary_to, salary_currency, vacancy_url)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (vacancy_id) DO NOTHING;
                """,
                    (
                        vacancy["id"],
                        vacancy["employer"]["id"],
                        vacancy["name"],
                        salary_from,
                        salary_to,
                        salary_currency,
                        vacancy["alternate_url"],
                    ),
                )
            except psycopg2.Error as e:
                print(
                    f"[DB Error] Ошибка вставки вакансии {vacancy.get('name', 'N/A')}. Пропуск. {e}"
                )

    conn.commit()
    print(
        f"[DB] Вставлено {len(companies_data)} компаний и {len(vacancies_data)} вакансий."
    )
