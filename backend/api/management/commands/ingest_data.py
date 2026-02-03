from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction

from  ...models import Customer, Loan


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [
        str(c)
        .strip()
        .lower()
        .replace("\n", " ")
        .replace("-", "_")
        .replace(" ", "_")
        for c in df.columns
    ]
    return df


def _get(row: Any, key: str, default: Any = None) -> Any:
    """
    Safe accessor for pandas Series rows:
    - returns default if key missing
    - returns default if value is NaN/NaT
    """
    if key not in row:
        return default
    val = row[key]
    if pd.isna(val):
        return default
    return val


def _to_int(val: Any, default: int | None = None) -> int | None:
    if val is None:
        return default
    try:
        # Handles numeric strings and floats like 12.0
        return int(float(val))
    except (TypeError, ValueError):
        return default


def _clean_phone(val: Any) -> str:
    """
    Coerce phone numbers from Excel-friendly formats:
    - 9876543210.0 -> "9876543210"
    - "+91 98765 43210" -> "9876543210"
    """
    s = "" if val is None else str(val).strip()
    if s.endswith(".0"):
        s = s[:-2]
    digits = re.sub(r"\D+", "", s)
    if len(digits) > 10:
        digits = digits[-10:]
    return digits


def _to_date(val: Any):
    if val is None:
        return None
    dt = pd.to_datetime(val, errors="coerce")
    if pd.isna(dt):
        return None
    return dt.date()


class Command(BaseCommand):
    help = "Ingest initial customer and loan data using pandas (idempotent)."

    def handle(self, *args, **options):
        self.stdout.write("Starting data ingestion...")

        # Hard-coded data directory: credit-approval-system/backend/datafiles/
        # settings.BASE_DIR points to backend/backend/, so we go one level up.
        base = Path(settings.BASE_DIR).parent / "backend/datafiles"
        customers_path = base / "customer_data.xlsx"
        loans_path = base / "loan_data.xlsx"

        self.ingest_customers(customers_path)
        self.ingest_loans(loans_path)

        self.stdout.write(self.style.SUCCESS("Data ingestion completed successfully"))

    def ingest_customers(self, path: Path) -> None:
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"Customer file not found, skipping: {path}"))
            return

        df = _normalize_columns(pd.read_excel(path))

        created = 0
        updated = 0
        skipped = 0

        with transaction.atomic():
            for _, row in df.iterrows():
                customer_id = _to_int(_get(row, "customer_id"))
                if customer_id is None:
                    skipped += 1
                    continue

                phone = _clean_phone(_get(row, "phone_number"))
                if not phone:
                    skipped += 1
                    continue

                defaults = {
                    "first_name": str(_get(row, "first_name", "")).strip(),
                    "last_name": str(_get(row, "last_name", "")).strip(),
                    "age": _to_int(_get(row, "age"), 0) or 0,
                    "phone_number": phone,
                    "monthly_salary": _to_int(_get(row, "monthly_salary"), 0) or 0,
                    "approved_limit": _to_int(_get(row, "approved_limit"), 0) or 0,
                    "current_debt": _to_int(_get(row, "current_debt"), 0) or 0,
                }

                try:
                    obj, was_created = Customer.objects.update_or_create(
                        id=customer_id,
                        defaults=defaults,
                    )
                except IntegrityError:
                    # likely duplicate phone_number; skip this row
                    skipped += 1
                    continue

                created += int(was_created)
                updated += int(not was_created)

        self.stdout.write(
            f"Customers ingested (created={created}, updated={updated}, skipped={skipped})"
        )

    def ingest_loans(self, path: Path) -> None:
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"Loan file not found, skipping: {path}"))
            return

        df = _normalize_columns(pd.read_excel(path))

        created = 0
        updated = 0
        skipped = 0
        missing_customer = 0

        with transaction.atomic():
            for _, row in df.iterrows():
                customer_id = _to_int(_get(row, "customer_id"))
                loan_id = _to_int(_get(row, "loan_id"))
                if customer_id is None or loan_id is None:
                    skipped += 1
                    continue

                try:
                    customer = Customer.objects.get(id=customer_id)
                except Customer.DoesNotExist:
                    missing_customer += 1
                    continue

                # Column variants after normalization:
                # - "EMIs paid on Time" -> "emis_paid_on_time"
                # - "Date of Approval" -> "date_of_approval"
                # - "End Date" -> "end_date"
                emi_paid_on_time = _to_int(
                    _get(row, "emis_paid_on_time", _get(row, "emi_paid_on_time")), 0
                ) or 0

                # Your Excel doesn't have a separate "start date" column.
                # We treat "Date of Approval" as both the approval date and the start date.
                date_of_approval = _to_date(_get(row, "date_of_approval"))
                start_date = _to_date(_get(row, "start_date", date_of_approval))
                end_date = _to_date(_get(row, "end_date"))

                if start_date is None or end_date is None or date_of_approval is None:
                    skipped += 1
                    continue

                defaults = {
                    "customer": customer,
                    "loan_amount": _to_int(_get(row, "loan_amount"), 0) or 0,
                    "tenure": _to_int(_get(row, "tenure"), 0) or 0,
                    "interest_rate": _to_int(_get(row, "interest_rate"), 0) or 0,
                    "emi": _to_int(_get(row, "monthly_repayment", _get(row, "emi")), 0) or 0,
                    "emi_paid_on_time": emi_paid_on_time,
                    "start_date": start_date,
                    "end_date": end_date,
                    "date_of_approval": date_of_approval,
                }

                obj, was_created = Loan.objects.update_or_create(
                    id=loan_id,
                    defaults=defaults,
                )
                created += int(was_created)
                updated += int(not was_created)

        self.stdout.write(
            "Loans ingested "
            f"(created={created}, updated={updated}, skipped={skipped}, missing_customer={missing_customer})"
        )

