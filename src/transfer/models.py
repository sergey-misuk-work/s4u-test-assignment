from decimal import Decimal
from django.db import models, transaction
from account.models import Account
from django.utils import timezone
from transfer.utils import add_month


class InsufficientBalance(Exception):
    pass


class Transfer(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    from_account = models.ForeignKey(Account, models.CASCADE, related_name='transfers_in')
    to_account = models.ForeignKey(Account, models.CASCADE, related_name='transfers_out')
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    is_external = models.BooleanField(null=False, default=False)
    is_outbound = models.BooleanField(null=False, default=True)

    @staticmethod
    def do_transfer(from_account: Account, to_account: Account, amount: Decimal):
        if amount < 0:
            raise ValueError('Amount takes non-negative values only')

        with transaction.atomic():
            from_account_ = Account.objects.select_for_update().get(pk=from_account.pk)
            to_account_ = Account.objects.select_for_update().get(pk=to_account.pk)

            if from_account_.balance < amount:
                raise InsufficientBalance()

            from_account_.balance -= amount
            to_account_.balance += amount

            from_account_.save()
            to_account_.save()

            # preserve modified data if any
            from_account.refresh_from_db(fields=('balance',))
            to_account.refresh_from_db(fields=('balance',))

            return Transfer.objects.create(
                from_account=from_account,
                to_account=to_account,
                amount=amount
            )

    @staticmethod
    def do_external_transfer(account: Account, amount: Decimal, is_outbound: bool = True, **meta: str):
        if amount < 0:
            raise ValueError('Amount takes non-negative values only')

        with transaction.atomic():
            account_ = Account.objects.select_for_update().get(pk=account.pk)

            if is_outbound:
                if account_.balance < amount:
                    raise InsufficientBalance()

                account_.balance -= amount
            else:
                account_.balance += amount

            # save metadata
            for key, value in meta:
                account_.transfer_meta.create(
                    key=key,
                    value=value,
                )

            account_.save()

            # preserve modified data if any
            account.refresh_from_db(fields=('balance',))

            return Transfer.objects.create(
                from_account=account,
                to_account=account,
                amount=amount,
                is_external=True,
                is_outbound=is_outbound,
            )


class ScheduledPayment(models.Model):
    next_payment_date = models.DateField()
    from_account = models.ForeignKey(Account, models.CASCADE, related_name='sender')
    to_account = models.ForeignKey(Account, models.CASCADE, related_name='receiver')
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    # this field is required to handle different months length
    # example: payment scheduled at 2020-08-31 and the next payment must be executed at 2020-09-30, but the third
    # one is supposed to be executed at 2020-10-31.
    original_day = models.IntegerField()

    @staticmethod
    def schedule_payment(from_account: Account, to_account: Account, amount: Decimal, day: int = None, force_payment: bool = False):
        current_date = timezone.datetime.now().date()

        if day > current_date.day:
            next_payment_date = current_date.replace(day=day)
        else:
            if force_payment:
                Transfer.do_transfer(from_account, to_account, amount)
            next_payment_date = add_month(current_date, original_day=day)

        return ScheduledPayment.objects.create(
            next_payment_date=next_payment_date,
            from_account=from_account,
            to_account=to_account,
            amount=amount,
            original_day=day,
        )


class TransferMeta(models.Model):
    """
    A model that can be used for external transaction data
    """
    transfer = models.ForeignKey(Account, models.CASCADE, related_name='transfer_meta')
    key = models.CharField(max_length=50)
    value = models.CharField(max_length=128)
