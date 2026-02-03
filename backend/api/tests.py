from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Customer


class CustomerAPITests(APITestCase):
    def test_register_customer_creates_customer(self):
        url = reverse("register-customer")
        payload = {
            "first_name": "John",
            "last_name": "Doe",
            "age": 30,
            "monthly_salary": 50000,
            "phone_number": "9999999999",
        }

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Customer.objects.count(), 1)
        customer = Customer.objects.get()
        self.assertEqual(customer.first_name, "John")
        # approved_limit gets computed based on salary
        self.assertGreater(customer.approved_limit, 0)


class LoanEligibilityAPITests(APITestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            first_name="Alice",
            last_name="Smith",
            age=28,
            phone_number="8888888888",
            monthly_salary=60000,
            approved_limit=200000,
            current_debt=0,
        )

    def test_check_eligibility_basic_flow(self):
        url = reverse("check-eligibility")
        payload = {
            "customer_id": self.customer.id,
            "loan_amount": 100000,
            "interest_rate": 12,
            "tenure": 12,
        }

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["customer_id"], self.customer.id)
        self.assertIn("monthly_installment", data)

# Create your tests here.
