from django.db import models

# Create your models here.
class Customer(models.Model):
    #i've not created customer id because django will already handle the id
    first_name = models.CharField(max_length = 100)
    last_name = models.CharField(max_length = 100)
    phone_number = models.CharField(max_length = 10, unique = True)
    monthly_salary= models.IntegerField()
    approved_limit = models.IntegerField()
    current_debt = models.IntegerField()

    def __str__(self):
        return self.first_name

class Loan(models.Model):
    #same for the loan id
    customer = models.ForeignKey(
        Customer,
        on_delete= models.CASCADE,
        related_name="loans"
    )
    loan_amount = models.IntegerField()
    tenure = models.IntegerField()
    interest_rate = models.IntegerField()
    emi = models.IntegerField()
    start_date = models.DateField()
    emi_paid_on_time = models.IntegerField()
    date_of_approval = models.DateField()
    end_date = models.DateField()
    def __str__(self):
        return f"Loan {self.id} - {self.customer_id.first_name} - ₹{self.loan_amount}"