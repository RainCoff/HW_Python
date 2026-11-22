from datetime import datetime
from math import isfinite

from tabulate import tabulate


class Account:
    # Нулевой баланс допустим, отрицательный — только у кредитного счёта.
    def __init__(self, account_holder: str, balance: float = 0):
        if not isinstance(account_holder, str):
            raise TypeError("Имя владельца счёта должно быть строкой.")
        if not isfinite(balance) or balance < 0:
            raise ValueError(
                "Баланс должен быть конечным числом не меньше нуля."
            )
        self.holder = account_holder
        self.account_holder = account_holder
        self._balance = balance
        self.operations_history = []

    def add_operation(
        self, operation_type, balance_before, amount, balance_after, status
    ):
        self.operations_history.append({
            "type": operation_type,
            "timestamp": datetime.now(),
            "balance_before": balance_before,
            "amount": amount,
            "balance_after": balance_after,
            "status": status,
        })

    def get_balance(self):
        return self._balance

    def get_available_balance(self):
        # Доступная сумма зависит от правил конкретного счёта.
        return self._balance

    def get_history(self):
        # Изменение результата не должно менять внутреннюю историю.
        return [operation.copy() for operation in self.operations_history]

    def get_operations(self, from_date=None, to_date=None):
        # None позволяет не задавать границы периода.
        headers = (
            "Операция", "Дата и время", "До", "Сумма", "После",
            "Статус", "Кредит",
        )
        rows = []
        for operation in self.get_history():
            if from_date is not None and operation["timestamp"] < from_date:
                continue
            if to_date is not None and operation["timestamp"] > to_date:
                continue
            rows.append((
                operation["type"],
                operation["timestamp"].strftime("%d.%m.%Y %H:%M:%S"),
                f"{operation['balance_before']:.2f}",
                f"{operation['amount']:.2f}",
                f"{operation['balance_after']:.2f}",
                operation["status"],
                "Да" if operation.get("used_credit", False) else "Нет",
            ))

        # Сохраняем два знака после точки в уже подготовленных суммах.
        print(tabulate(
            rows,
            headers=headers,
            tablefmt="grid",
            disable_numparse=True,
            colalign=(
                "left", "left", "right", "right", "right", "left", "left"
            ),
        ))
        if not rows:
            print("Операций за указанный период нет.")

    def deposit(self, amount: float):
        # NaN и бесконечность тоже нельзя использовать в качестве суммы.
        if not isfinite(amount) or amount <= 0:
            self.add_operation(
                "deposit", self._balance, amount, self._balance, "fail"
            )
            raise ValueError(
                "Сумма должна быть конечным числом больше нуля."
            )
        previous_balance = self._balance
        self._balance += amount
        self.add_operation(
            "deposit", previous_balance, amount, self._balance, "success"
        )

    def withdraw(self, amount: float):
        if not isfinite(amount) or amount <= 0:
            self.add_operation(
                "withdraw", self._balance, amount, self._balance, "fail"
            )
            raise ValueError(
                "Сумма должна быть конечным числом больше нуля."
            )
        if amount > self.get_available_balance():
            # Отказ сохраняем в истории, но баланс не меняем.
            self.add_operation(
                "withdraw", self._balance, amount, self._balance, "fail"
            )
            return
        previous_balance = self._balance
        self._balance -= amount
        self.add_operation(
            "withdraw", previous_balance, amount, self._balance, "success"
        )


class CreditAccount(Account):
    def __init__(
        self, account_holder: str, balance: float = 0, credit_limit: float = 0
    ):
        if not isfinite(credit_limit) or credit_limit < 0:
            raise ValueError(
                "Кредитный лимит должен быть конечным числом не меньше нуля."
            )
        if not isfinite(balance) or balance < -credit_limit:
            raise ValueError(
                "Баланс должен быть конечным числом. "
                "Долг не должен превышать кредитный лимит."
            )
        # Родителю передаём баланс без долга, затем задаём проверенный долг.
        super().__init__(account_holder, max(balance, 0))
        self._balance = balance
        self.credit_limit = credit_limit

    def get_available_balance(self):
        return self._balance + self.credit_limit

    def add_operation(
        self, operation_type, balance_before, amount, balance_after, status
    ):
        # Пополнение и отказ не расходуют кредит.
        super().add_operation(
            operation_type, balance_before, amount, balance_after, status
        )
        self.operations_history[-1]["used_credit"] = (
            operation_type == "withdraw"
            and status == "success"
            and balance_after < 0
        )

if __name__ == "__main__":
    acc1 = Account("John Doe", 0)
    acc2 = Account("John Doe", 20)
    acc2.deposit(40)
    try:
        acc2.deposit(-10)
    except ValueError as error:
        print(f"Неудачная попытка внесения средств: {error}")
    acc2.withdraw(10)
    acc2.withdraw(100)
    print("Баланс:", acc2.get_balance())
    acc2.get_operations()

    credit_acc = CreditAccount("Jane Doe", balance=100, credit_limit=200)
    credit_acc.withdraw(250)
    print("Кредитный баланс:", credit_acc.get_balance())
    print("Доступная сумма:", credit_acc.get_available_balance())
    credit_acc.get_operations()
