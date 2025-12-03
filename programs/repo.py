import csv
import json
import os


from models import (
    Currency,
    Coords,
    BankOrg,
    BankBranch,
    ExchangeRate
)


# CRUD - Create Update Read Delete

class DataRepo:
    def __init__(self, filename: str = "branches.csv"):
        self.filename = filename

    def _check_file(self):
        """Создаёт CSV с заголовками, если он отсутствует."""
        if not os.path.exists(self.filename):
            with open(self.filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["id", "bank_org", "address", "coords", "exchange_rates"])

    def set_bank_branch(self, bank_branch: BankBranch) -> BankBranch:
        """
        Сохранение объекта класса в csv
        """
        self._check_file()

        # Проверяем, есть ли отделение с таким id
        existing = self.get_bank_branch(bank_branch.id)

        if existing is not None:
            # Если отделение есть — обновляем только курсы
            return self.update_bank_branche_rates(bank_branch.id, bank_branch.exchange_rates)

        # Если нет — создаём новую запись
        row = [
            bank_branch.id,
            bank_branch.bank_org.name,
            bank_branch.address,
            f"{bank_branch.coords.lon},{bank_branch.coords.lat}",
            json.dumps([
                {
                    "curr_from": r.curr_from.value,
                    "curr_to": r.curr_to.value,
                    "rate": r.rate,
                }
                for r in bank_branch.exchange_rates
            ])
        ]

        with open(self.filename, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(row)

        return bank_branch

    def get_bank_branch(self, id: int) -> BankBranch | None:
        """BankBranch по id, вернет None если файл не найден"""
        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                for row in reader:
                    if str(id) != row["id"]:
                        continue

                    lon, lat = map(float, row["coords"].split(","))

                    # JSON ->  ExchangeRate
                    rates_data = json.loads(row["exchange_rates"])
                    exchange_rates = [
                        ExchangeRate(
                            curr_from=Currency(r["curr_from"]),
                            curr_to=Currency(r["curr_to"]),
                            rate=float(r["rate"])
                        )
                        for r in rates_data
                    ]

                    # восстановление объекта
                    return BankBranch(
                        bank_org=BankOrg(row["bank_org"]),
                        address=row["address"],
                        coords=Coords(lon, lat),
                        exchange_rates=exchange_rates
                    )

        except FileNotFoundError:
            return None

    #фильтр 
    def list_bank_branches(
        self,
        curr_from: Currency | None = None,
        curr_to: Currency | None = None
    ) -> list[BankBranch]:
        '''Возращает список подходящих отделений которые соответсвуют требованиям по курсру'''
        #TODO
        #Потом можно добавить ограничения по курсу

        branches = []

        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                for row in reader:
                    branch_id = int(row["id"])
                    branch = self.get_bank_branch(branch_id)
                    if branch is None: #заглушка
                        continue

                    #фильтрация
                    match_from = (
                        curr_from is None or
                        any(r.curr_from == curr_from for r in branch.exchange_rates)
                    )

                    match_to = (
                        curr_to is None or
                        any(r.curr_to == curr_to for r in branch.exchange_rates)
                    )

                    if match_from and match_to:
                        branches.append(branch)

        except FileNotFoundError:
            return []

        return branches
        

    #замена
    def update_bank_branche_rates(
        self,
        id: int,
        rates: list[ExchangeRate]
    ) -> BankBranch:
        """
        Обновляет курсы отделения.
        Если отделение с таким id отсутствует — выбрасывает ValueError.
        """

        # Проверяем существование
        branch = self.get_bank_branch(id)
        if branch is None:
            raise ValueError(f"BankBranch with id={id} not found")

        # Читаем CSV
        try:
            rows = []
            with open(self.filename, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rows.append(row)

        except:
            raise ValueError(f"BankBranch with id={id} not found (inconsistent CSV)")   

        # Обновляем курс
        for row in rows:
            if row["id"] == str(id):
                row["exchange_rates"] = json.dumps([
                    {
                        "curr_from": r.curr_from.value,
                        "curr_to": r.curr_to.value,
                        "rate": r.rate,
                    }
                    for r in rates
                ])
                break

        # Перезаписываем CSV
        with open(self.filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["id", "bank_org", "address", "coords", "exchange_rates"]
            )
            writer.writeheader()
            writer.writerows(rows)

        # Возвращаем обновлённый объект
        return self.get_bank_branch(id)

    
    def delete_bank_branch(
            self,
            id: int
    ):
        ...




def main():
    repo = DataRepo()
    ans = repo.list_bank_branches()
    for i in ans:
        print(str(i))

if __name__ == '__main__':
    main()