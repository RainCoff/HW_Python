import json
from itertools import islice
import csv
#               Задание 1
# Переведите содержимое файла purchase_log.txt в словарь purchases вида:
#  {'1840e0b9d4': 'Продукты', ...}
# Пример работы программы при выводе первых двух элементов словаря purchases:
# 1840e0b9d4 ‘Продукты‘
# 4e4f90fcfb ‘Электроника‘

purchases = {}
with open('../data/purchase_log.txt', 'r', encoding='utf-8') as file:
    next(file, None)
    for line in file:
        newitem=json.loads(line.strip())
        purchases[newitem['user_id']] = newitem['category']

print(dict(islice(purchases.items(), 2)))
#                Задание 2
# Для каждого user_id в файле visit_log.csv определите третий столбец с категорией покупки. Если покупка была, сам файл visit_log.csv изменять не надо.
# Запишите в файл funnel.csv визиты из файла visit_log.csv, в которых были покупки с указанием категории.
# Учтите условия для данных:
# содержимое purchase_log.txt помещается в оперативную память компьютера;
# содержимое visit_log.csv — нет, используйте только построчную обработку этого файла.
# Примеры работы программы при выводе первых трёх строк файла funnel.csv:
# user_id, source,category
# 1840e0b9d4,other, Продукты
# 4e4f90fcfb,context, Электроника
with open('../data/visit_log.csv', 'r', encoding='utf-8',newline="") as reader,open('../data/funnel.csv', 'w', encoding='utf-8-sig',newline="") as writer:
    next(reader, None)
    reader = csv.reader(reader,delimiter=';')
    writer = csv.writer(writer,delimiter=',')
    writer.writerow(['user_id', 'source','category'])
    for row in reader:
        if row[0] in purchases:
            writer.writerow([row[0],row[1],purchases[row[0]]])