# Generated by Django 3.1 on 2020-08-05 10:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0002_account_owner'),
        ('transfer', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScheduledPayment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('next_payment_date', models.DateField()),
                ('amount', models.DecimalField(decimal_places=2, max_digits=18)),
                ('from_account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sender', to='account.account')),
                ('to_account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='receiver', to='account.account')),
            ],
        ),
    ]
