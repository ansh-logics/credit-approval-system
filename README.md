## Credit Approval System (Django + PostgreSQL)

This is a simple credit approval system built with Django and Django REST Framework. It exposes APIs to register customers, check loan eligibility, create loans, and view loan details. All services (web app + PostgreSQL) are fully dockerized and can be started with a single command.

### Tech stack
- **Backend**: Django 6, Django REST Framework
- **Database**: PostgreSQL
- **Data ingest**: Custom Django management command using pandas + openpyxl
- **Containerization**: Docker, docker-compose

### Project structure (backend)
- `backend/backend/` – Django project (settings, URLs, WSGI)
- `backend/api/` – Application code:
  - `models.py` – `Customer` and `Loan` models
  - `serializers.py` – DRF serializers
  - `service.py` – credit score & EMI calculation logic
  - `views.py` – API views
  - `urls.py` – API routes
  - `management/commands/ingest_data.py` – loads initial data from Excel
  - `tests.py` – basic API tests
- `backend/datafiles/` – `customer_data.xlsx`, `loan_data.xlsx`

---

## Running with Docker (recommended)

Prerequisites:
- Docker
- docker-compose

From the project root (`credit-approval-system`):

```bash
docker-compose up --build
```

What this does:
- Starts a PostgreSQL container (`db`)
- Builds and starts the Django app container (`web`)
- Waits for Postgres to be ready
- Applies database migrations
- Runs the `ingest_data` command to load customers and loans from Excel
- Starts the Django development server on `http://localhost:8000`

To stop everything:

```bash
docker-compose down
```

If you want a completely fresh database (useful during development):

```bash
docker-compose down -v
docker-compose up --build
```

---

## Running locally without Docker (optional)

Prerequisites:
- Python 3.12
- PostgreSQL running locally

1. Create a virtual environment and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Ensure Postgres has a database/user matching `backend/backend/settings.py` or override using env vars:
   - `POSTGRES_DB`
   - `POSTGRES_USER`
   - `POSTGRES_PASSWORD`
   - `POSTGRES_HOST`
   - `POSTGRES_PORT`

3. Apply migrations and ingest data:
   ```bash
   cd backend
   python manage.py migrate
   python manage.py ingest_data
   python manage.py runserver
   ```

App will be available at `http://127.0.0.1:8000`.

---

## API overview

Base path (inside Django project): `/api/` (or whatever is configured in `backend/urls.py`).

- **Register customer**
  - `POST /api/register/`
  - Body: `first_name`, `last_name`, `age`, `monthly_salary`, `phone_number`
  - Computes `approved_limit` and creates a customer.

- **Check loan eligibility**
  - `POST /api/check-eligibility/`
  - Body: `customer_id`, `loan_amount`, `interest_rate`, `tenure`
  - Returns approval flag, corrected interest rate (based on credit score), and monthly installment.

- **Create loan**
  - `POST /api/create-loan/`
  - Body: `customer_id`, `loan_amount`, `tenure`
  - Applies business rules (credit score, approved limit, EMI <= 50% of salary) and creates a loan if valid.

- **View single loan**
  - `GET /api/view-loan/<loan_id>/`
  - Returns loan details plus minimal customer info.

- **View all loans for a customer**
  - `GET /api/view-loans/<customer_id>/`
  - Returns all loans for that customer with remaining repayments.

---

## Tests

To run Django tests (inside the `web` container or locally with a configured DB):

```bash
cd backend
python manage.py test api
```

This currently covers:
- Customer registration flow
- Basic loan eligibility flow

Postman tests:
- A Postman test run report is stored as `Assignment test.postman_test_run.json` in the project root.
- It shows successful calls to all main endpoints: register, check eligibility, create loan, view loan, and view loans for a customer.

