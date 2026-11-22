import io
import runpy
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta
from pathlib import Path


# Дефис в имени учебного файла не позволяет использовать обычный import.
classes = runpy.run_path(str(Path(__file__).with_name("HW5-classes.py")))
Account = classes["Account"]
CreditAccount = classes["CreditAccount"]


class AccountTests(unittest.TestCase):
    def test_initial_balance_and_holder(self):
        account = Account("Alice")
        self.assertEqual(account.holder, "Alice")
        self.assertEqual(account.account_holder, "Alice")
        self.assertEqual(account.get_balance(), 0)
        self.assertEqual(account.get_history(), [])
        with self.assertRaises(TypeError):
            Account(123)
        for balance in (-1, float("nan"), float("inf")):
            with self.subTest(balance=balance), self.assertRaises(ValueError):
                Account("Alice", balance)

    def test_successful_operations(self):
        account = Account("Alice", 100)
        account.deposit(50)
        account.withdraw(150)
        self.assertEqual(account.get_balance(), 0)
        history = account.get_history()
        self.assertEqual(
            [item["type"] for item in history], ["deposit", "withdraw"]
        )
        self.assertEqual([item["balance_after"] for item in history], [150, 0])
        self.assertTrue(all(item["status"] == "success" for item in history))
        self.assertTrue(all(
            isinstance(item["timestamp"], datetime) for item in history
        ))
        self.assertEqual(history[0]["amount"], 50)
        self.assertEqual(history[1]["balance_before"], 150)

    def test_insufficient_funds(self):
        account = Account("Alice", 100)
        account.withdraw(101)
        self.assertEqual(account.get_balance(), 100)
        operation = account.get_history()[0]
        self.assertEqual(operation["status"], "fail")
        self.assertEqual(operation["amount"], 101)
        self.assertEqual(operation["balance_after"], 100)

    def test_invalid_amounts(self):
        for cls in (Account, CreditAccount):
            for method in ("deposit", "withdraw"):
                for amount in (0, -10, float("nan"), float("inf")):
                    with self.subTest(cls=cls, method=method, amount=amount):
                        account = cls("Alice", 100)
                        with self.assertRaises(ValueError):
                            getattr(account, method)(amount)
                        self.assertEqual(account.get_balance(), 100)
                        self.assertEqual(
                            account.get_history()[0]["status"], "fail"
                        )

    def test_independent_and_copied_histories(self):
        first, second = Account("Alice"), Account("Bob")
        first.deposit(10)
        self.assertEqual(second.get_history(), [])
        history = first.get_history()
        history[0]["amount"] = 999
        history.clear()
        self.assertEqual(first.get_history()[0]["amount"], 10)

    def test_printed_history_and_dates(self):
        account = Account("Alice")
        account.deposit(10)
        timestamp = account.get_history()[0]["timestamp"]
        for start, end, visible in (
            (None, None, True),
            (timestamp, timestamp, True),
            (timestamp + timedelta(seconds=1), None, False),
            (None, timestamp - timedelta(seconds=1), False),
        ):
            with self.subTest(start=start, end=end):
                output = io.StringIO()
                with redirect_stdout(output):
                    account.get_operations(start, end)
                self.assertEqual("deposit" in output.getvalue(), visible)

    def test_table_alignment_and_credit(self):
        account = CreditAccount("Alice", balance=100, credit_limit=200)
        account.withdraw(250)
        account.deposit(1234567.89)
        output = io.StringIO()
        with redirect_stdout(output):
            account.get_operations()
        lines = output.getvalue().splitlines()
        self.assertEqual(len({len(line) for line in lines}), 1)
        rows = [line for line in lines if line.startswith("|")]
        borders = [
            [i for i, char in enumerate(line) if char == "|"]
            for line in rows
        ]
        self.assertTrue(all(item == borders[0] for item in borders))
        withdrawal = [cell.strip() for cell in rows[1].split("|")[1:-1]]
        self.assertEqual(withdrawal[2:5], ["100.00", "250.00", "-150.00"])
        self.assertEqual(withdrawal[-1], "Да")
        self.assertEqual(rows[2].split("|")[-2].strip(), "Нет")
        self.assertEqual(
            withdrawal[1],
            account.get_history()[0]["timestamp"].strftime(
                "%d.%m.%Y %H:%M:%S"
            ),
        )

    def test_empty_table(self):
        output = io.StringIO()
        with redirect_stdout(output):
            Account("Alice").get_operations()
        self.assertIn("Операций за указанный период нет.", output.getvalue())

    def test_credit_initialization_and_boundaries(self):
        for balance, limit in (
            (-1, 0), (-201, 200), (0, -1),
            (float("nan"), 200), (0, float("inf")),
        ):
            with self.subTest(balance=balance, limit=limit):
                with self.assertRaises(ValueError):
                    CreditAccount("Alice", balance, limit)
        account = CreditAccount("Alice", balance=-200, credit_limit=200)
        self.assertEqual(account.get_balance(), -200)
        self.assertEqual(account.get_available_balance(), 0)
        account.withdraw(1)
        self.assertEqual(account.get_balance(), -200)
        self.assertFalse(account.get_history()[-1]["used_credit"])
        zero_limit = CreditAccount("Bob")
        zero_limit.withdraw(1)
        self.assertEqual(zero_limit.get_history()[-1]["status"], "fail")

    def test_credit_operations_and_history(self):
        account = CreditAccount("Alice", balance=100, credit_limit=200)
        account.withdraw(50)
        self.assertFalse(account.get_history()[-1]["used_credit"])
        account.withdraw(200)
        self.assertEqual(account.get_balance(), -150)
        self.assertEqual(account.get_available_balance(), 50)
        self.assertTrue(account.get_history()[-1]["used_credit"])
        account.withdraw(50)
        self.assertEqual(account.get_balance(), -200)
        account.withdraw(1)
        self.assertEqual(account.get_balance(), -200)
        self.assertEqual(account.get_history()[-1]["status"], "fail")
        self.assertFalse(account.get_history()[-1]["used_credit"])
        account.deposit(250)
        self.assertEqual(account.get_balance(), 50)
        self.assertFalse(account.get_history()[-1]["used_credit"])


if __name__ == "__main__":
    unittest.main()
