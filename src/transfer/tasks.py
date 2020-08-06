from celery import shared_task
from transfer.models import ScheduledPayment, Transfer
from django.utils import timezone
from transfer.utils import add_month


@shared_task
def execute_scheduled_payments() -> None:
    current_date = timezone.datetime.now().date()
    scheduled_payments = ScheduledPayment.objects.filter(next_payment_date=current_date).all()
    for payment in scheduled_payments:
        Transfer.do_transfer(payment.from_account, payment.to_account, payment.amount)
        payment.next_payment_date = add_month(payment.next_payment_date)
        payment.save()
