from decimal import Decimal
from django.db import models
from account.models import Account


class InsufficientBalance(Exception):
    pass


class Transfer(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    from_account = models.ForeignKey(Account, models.CASCADE, related_name='transfers_in')
    to_account = models.ForeignKey(Account, models.CASCADE, related_name='transfers_out')
    amount = models.DecimalField(max_digits=18, decimal_places=2)

    @staticmethod
    def do_transfer(from_account: Account, to_account: Account, amount: Decimal):
        if from_account.balance < amount:
            raise InsufficientBalance()

        from_account.balance -= amount
        to_account.balance += amount

        from_account.save()
        to_account.save()

        return Transfer.objects.create(
            from_account=from_account,
            to_account=to_account,
            amount=amount
        )


class ScheduledPayment(models.Model):
    next_payment_date = models.DateField()
    from_account = models.ForeignKey(Account, models.CASCADE)
    to_account = models.ForeignKey(Account, models.CASCADE)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
