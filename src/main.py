import psycopg2
from typing import Dict, List, Any

from config.config import config
from src.db_utils import create_database, create_tables, insert_data_to_tables
from src.api_HH import HHClient
from src.db_manager import DBManager

# 10 выбранных компаний
COMPANY_NAMES = [
    "Skyeng",
    "Яндекс Крауд",
    "Яндекс",
    "РУСАЛ",
    "ООО РН-Ванкор",
    "ООО ВИРАЖ",
    "IT-Компания АБС",
    "Банк ВТБ (ПАО)",
    "Planeta.ru",
    "ООО Сбербанк-Сервис",
]

# Глобальная переменная для имени БД (будет установлена в main)
DB_NAME: str = ""


def collect_and_save_data(client: HHClient, db_params: Dict[str, Any]) -> None:
    """
    Основная функция сбора данных с HH.ru, создания БД/таблиц и сохранения данных.
    """
    global DB_NAME  # Используем глобальную переменную

    all_companies_data: List[Dict[str, str]] = []
    all_vacancies_data: List[Dict[str, Any]] = []

    print("--- 1. Сбор данных о компаниях и вакансиях с HH.ru ---")

    # ... (логика сбора данных)
    for name in COMPANY_NAMES:
        employer_id = client.get_employer_id(name)

        if employer_id:
            print(
                f"Найдена компания '{name}' (ID: {employer_id}). Собираем вакансии..."
            )
            all_companies_data.append({"id": employer_id, "name": name})

            vacancies = client.get_vacancies_by_employer(employer_id)
            all_vacancies_data.extend(vacancies)
            print(f"  > Собрано {len(vacancies)} вакансий.")
        else:
            print(f"!!! Не удалось найти ID для компании '{name}'. Пропускаем.")

    if not all_vacancies_data:
        print("Сбор данных не удался. Проверьте названия компаний или API-клиент.")
        return

    # --- Создание БД, Таблиц и Вставка Данных ---
    print("\n--- 2. Создание БД и Таблиц ---")

    # 2.1 Создаем базу данных
    create_database(DB_NAME, db_params)

    conn = None
    try:
        # 2.2 Подключаемся к целевой БД и создаем таблицы
        # db_params теперь не содержит 'database', так как он удален в main()
        conn = psycopg2.connect(dbname=DB_NAME, **db_params)
        create_tables(conn)

        # 2.3 Заполнение Таблиц
        print("\n--- 3. Заполнение Таблиц данными ---")
        insert_data_to_tables(conn, all_companies_data, all_vacancies_data)

    except psycopg2.Error as e:
        print(f"Критическая ошибка подключения/работы с БД: {e}")
    finally:
        if conn:
            conn.close()


def user_interaction(manager: DBManager) -> None:
    """
    Интерфейс для взаимодействия с пользователем, выводящий результаты запросов.
    """
    print("\n" + "=" * 60)
    print("= МЕНЕДЖЕР АНАЛИЗА ВАКАНСИЙ (HH.ru) - РЕЗУЛЬТАТЫ ЗАПРОСОВ =")
    print("=" * 60)

    # ... (логика вывода запросов)

    # 1. Список компаний и количество вакансий
    print("\n1. Компании и количество вакансий:")
    companies_count = manager.get_companies_and_vacancies_count()
    for name, count in companies_count:
        print(f"  - {name}: {count} вакансий")

    # 2. Средняя зарплата
    avg_salary = manager.get_avg_salary()
    if avg_salary:
        print(f"\n2. Средняя зарплата 'от' по всем вакансиям: {avg_salary:,.0f} руб.")

    # 3. Вакансии с зарплатой выше средней
    print("\n3. Вакансии, зарплата которых выше средней:")
    higher_salary_vacancies = manager.get_vacancies_with_higher_salary()
    if higher_salary_vacancies:
        for company, title, salary, url in higher_salary_vacancies[:5]:
            print(f"  - {title} ({company}): ЗП: {salary:,} руб.")
        if len(higher_salary_vacancies) > 5:
            print(f"  ... и еще {len(higher_salary_vacancies) - 5} вакансий.")
    else:
        print("   Нет вакансий с зарплатой выше средней (или данные отсутствуют).")

    # 4. Поиск по ключевому слову
    keyword = input(
        "\n4. Введите ключевое слово для поиска вакансий (например, Java, Junior): "
    ).strip()
    if keyword:
        keyword_vacancies = manager.get_vacancies_with_keyword(keyword)
        print(f"Результаты поиска по '{keyword}' ({len(keyword_vacancies)} найдено):")
        if keyword_vacancies:
            # Проверьте, что здесь 4 переменных: company, title, salary, url
            for company, title, salary, url in keyword_vacancies[:5]:
                print(f"  - {title} ({company}): ЗП: {salary} -> {url}")
        else:
            print("   Вакансии с таким ключевым словом не найдены.")


def main():
    """Точка входа в программу, инициализирует процесс."""
    global DB_NAME

    db_params = config("db")

    # !!! КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Используем .pop() для удаления 'database' из словаря !!!
    # Это решает TypeError: you can't specify both 'database' and 'dbname'
    DB_NAME = db_params.pop("database")

    hh_client = HHClient()

    # 1. Сбор и сохранение данных
    collect_and_save_data(hh_client, db_params)

    # 2. Анализ данных
    try:
        db_manager = DBManager(DB_NAME, db_params)
        user_interaction(db_manager)
    except Exception as e:
        print(
            f"\nОшибка при инициализации DBManager или выполнении запросов. Проверьте лог. Ошибка: {e}"
        )


if __name__ == "__main__":
    main()
