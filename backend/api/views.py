from rest_framework.views import APIView
from rest_framework.response import Response, Serializer
from rest_framework import status
from .models import Customer, Loan
from .Serializer import CustomerRegisterSerializer, LoanEligibilityRequestSerializer, LoanCreateSerializer, LoanDetailSerializer, LoanListSerializer
from .service import calculate_credit_score, get_interest_rate_from_score, calculate_emi


class RegisterCustomerView(APIView):
    def post(self, request):
        serializer = CustomerRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=201)

class CheckEligibilityView(APIView):
    def post(self, request):
        req = LoanEligibilityRequestSerializer(data=request.data)
        req.is_valid(raise_exception=True)

        customer = Customer.objects.get(id=req.validated_data["customer_id"])
        score = calculate_credit_score(customer)
        interest_rate = get_interest_rate_from_score(score)

        emi = calculate_emi(
            req.validated_data["loan_amount"],
            interest_rate,
            req.validated_data["tenure"]
        )

        return Response({
            "customer_id": customer.id,
            "approval": score > 10,
            "interest_rate": req.validated_data["interest_rate"],
            "corrected_interest_rate": interest_rate,
            "tenure": req.validated_data["tenure"],
            "monthly_installment": emi
        })

class CreateLoanView(APIView):
    def post(self, request):
        serializer = LoanCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        loan = serializer.save()
        return Response({
            "loan_id": loan.id,
            "customer_id": loan.customer.id,
            "loan_approved": True,
            "monthly_installment": loan.emi
        })

class ViewLoanView(APIView):
    def get(self, request, loan_id):
        loan = Loan.objects.get(id=loan_id)
        return Response(LoanDetailSerializer(loan).data)

class ViewCustomerLoansView(APIView):
    def get(self, request, customer_id):
        # Optional: check customer exists
        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            return Response(
                {"error": "Customer not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        loans = Loan.objects.filter(customer=customer)

        serializer = LoanListSerializer(loans, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)