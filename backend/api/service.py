from datetime import date
from models import Loan

def calculate_credit_score(customer):
    loans = Loan.objects.filter(customer=customer)

    if customer.current_debt > customer.approved_limit:
        return 0

    score = 0

    if loans.exists():
        on_time_ratio = sum(l.emi_paid_on_time for l in loans) / sum(l.tenure for l in loans)
        score += 35 if on_time_ratio > 0.9 else 20
    else:
        score += 10

    loan_count = loans.count()
    score += 15 if loan_count <= 3 else 5

    current_year_loans = loans.filter(start_date__year=date.today().year).count()
    score += 15 if current_year_loans <= 2 else 5

    total_volume = sum(l.loan_amount for l in loans)
    score += 20 if total_volume < customer.approved_limit else 5

    return min(score, 100)

def get_interest_rate_from_score(score):
    if score > 50:
        return 10
    elif score > 30:
        return 12
    elif score > 10:
        return 16
    return None

def calculate_emi(principal, annual_rate, tenure):
    r = annual_rate / (12 * 100)
    return round((principal * r * (1 + r) ** tenure) / ((1 + r) ** tenure - 1), 2)