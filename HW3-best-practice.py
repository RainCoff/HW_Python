import csv
import json
from itertools import islice
from pathlib import Path


# Изменение: путь строится от скрипта и не зависит от рабочей папки запуска.
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


# Изменение: загрузка покупок вынесена в функцию для отдельной проверки.
def load_purchases(path):
    purchases = {}
    with path.open(encoding="utf-8") as input_file:
        # В этом файле первая строка содержит названия полей вместо покупки.
        next(input_file, None)
        for line in input_file:
            # Изменение: пустые строки пропускаются до разбора JSON.
            if not line.strip():
                continue

            # Изменение: имя purchase объясняет, что содержит одна запись.
            purchase = json.loads(line)
            # При повторном user_id последняя категория заменяет предыдущую.
            purchases[purchase["user_id"]] = purchase["category"]

    return purchases


# Изменение: отбор визитов отделён от чтения и записи файлов.
def matching_visits(rows, purchases):
    for row in rows:
        # Изменение: доступ по имени поля вместо позиции row[0].
        user_id = row["user_id"]
        if user_id in purchases:
            # Yield выдаёт одну запись и приостанавливает функцию.
            # Следующая запись появится, когда writerows запросит её.
            # Список всех подходящих визитов в памяти не создаётся.
            yield {
                "user_id": user_id,
                "source": row["source"],
                "category": purchases[user_id],
            }


def write_funnel(visits_path, output_path, purchases):
    # Изменение: файлы и CSV-обработчики имеют разные имена.
    # newline="" оставляет обработку переносов строк модулю csv.
    # utf-8-sig добавляет метку UTF-8 для распознавания кодировки в Excel.
    # Изменение: utf-8-sig удаляет метку UTF-8 из начала входного заголовка.
    with (
        visits_path.open(encoding="utf-8-sig", newline="") as input_file,
        output_path.open(
            "w", encoding="utf-8-sig", newline=""
        ) as output_file,
    ):
        # Изменение: DictReader сам использует первую строку как заголовок.
        # Отдельный next здесь не нужен: он пропустил бы первый визит.
        reader = csv.DictReader(input_file, delimiter=";")

        # Изменение: fieldnames задаёт названия и порядок выходных столбцов.
        writer = csv.DictWriter(
            output_file,
            fieldnames=["user_id", "source", "category"],
            delimiter=",",
        )
        writer.writeheader()

        # Изменение: writerows получает строки генератора по одной.
        # Оба файла остаются открытыми до завершения обработки.
        writer.writerows(matching_visits(reader, purchases))


def main():
    # Задание 1: словарь покупок по условию помещается в память.
    purchases = load_purchases(DATA_DIR / "purchase_log.txt")
    print(dict(islice(purchases.items(), 2)))

    # Задание 2: визиты обрабатываются построчно.
    # Режим w при каждом запуске заменяет содержимое funnel.csv.
    write_funnel(
        DATA_DIR / "visit_log.csv",
        DATA_DIR / "funnel.csv",
        purchases,
    )


# Изменение: импорт файла для проверки не запускает обработку данных.
if __name__ == "__main__":
    main()

