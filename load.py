import csv
from cs50 import SQL

db = SQL("sqlite:///symbols.db")

with open("csv/companylist.csv") as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for row in csv_reader:
        name = row['Name']
        symbol = row['Symbol']
        db.execute("INSERT INTO symbols (name, symbol) VALUES (:name, :symbol)", name=name, symbol=symbol)
with open("csv/companylist (1).csv") as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for row in csv_reader:
        name = row['Name']
        symbol = row['Symbol']
        db.execute("INSERT INTO symbols (name, symbol) VALUES (:name, :symbol)", name=name, symbol=symbol)
with open("csv/companylist (2).csv") as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for row in csv_reader:
        name = row['Name']
        symbol = row['Symbol']
        db.execute("INSERT INTO symbols (name, symbol) VALUES (:name, :symbol)", name=name, symbol=symbol)