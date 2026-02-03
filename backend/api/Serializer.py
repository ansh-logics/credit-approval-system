from rest_framework import serializers
from models import Loan, Customer
from services import (
    calculate_credit_score,
    get_interest_rate_from_score,
    calculate_emi
)

class CustomerRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            "id",
            "first_name",
            "last_name",
            "age",
            "monthly_salary",
            "approved_limit",
            "phone_number",
            "current_debt",
        ]
        read_only_fields = ["id", "approved_limit", "current_debt"]

    def create(self, validated_data):
        salary = validated_data["monthly_salary"]
        approved_limit = round((36 * salary) / 100000) * 100000

        return Customer.objects.create(
            approved_limit=approved_limit,
            current_debt=0,
            **validated_data
        )

class LoanEligibilityRequestSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    loan_amount = serializers.FloatField()
    interest_rate = serializers.FloatField()
    tenure = serializers.IntegerField()

class LoanEligibilityResponseSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    approval = serializers.BooleanField()
    interest_rate = serializers.FloatField()
    corrected_interest_rate = serializers.FloatField()
    tenure = serializers.IntegerField()
    monthly_installment = serializers.FloatField()

class LoanCreateSerializer(serializers.ModelSerializer):
    customer_id = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(),
        source="customer"
    )

    class Meta:
        model = Loan
        fields = [
            "id",
            "customer_id",
            "loan_amount",
            "tenure",
            "interest_rate",
            "emi",
        ]
        read_only_fields = ["id", "emi", "interest_rate"]

    def create(self, validated_data):
        customer = validated_data["customer"]
        loan_amount = validated_data["loan_amount"]
        tenure = validated_data["tenure"]

        credit_score = calculate_credit_score(customer)

        if credit_score < 10:
            raise serializers.ValidationError("Loan not approved")

        if customer.current_debt + loan_amount > customer.approved_limit:
            raise serializers.ValidationError("Approved limit exceeded")

        interest_rate = get_interest_rate_from_score(credit_score)
        emi = calculate_emi(loan_amount, interest_rate, tenure)

        if emi > 0.5 * customer.monthly_salary:
            raise serializers.ValidationError("EMI exceeds 50% of salary")

        loan = Loan.objects.create(
            customer=customer,
            interest_rate=interest_rate,
            emi=emi,
            **validated_data
        )

        customer.current_debt += loan_amount
        customer.save()

        return loan

class CustomerMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "first_name", "last_name", "phone_number", "age"]

class LoanDetailSerializer(serializers.ModelSerializer):
    customer = CustomerMiniSerializer()

    class Meta:
        model = Loan
        fields = [
            "id",
            "customer",
            "loan_amount",
            "interest_rate",
            "emi",
            "tenure",
        ]

class LoanListSerializer(serializers.ModelSerializer):
    repayments_left = serializers.SerializerMethodField()

    class Meta:
        model = Loan
        fields = [
            "id",
            "loan_amount",
            "interest_rate",
            "emi",
            "repayments_left",
        ]

    def get_repayments_left(self, obj):
        return max(obj.tenure - obj.emi_paid_on_time, 0)
