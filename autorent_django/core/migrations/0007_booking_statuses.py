from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_booking_delivery_address'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='status',
            field=models.CharField(choices=[('pending', 'Очікує'), ('awaiting_payment', 'Очікує оплати'), ('paid', 'Оплачено'), ('active', 'Активне'), ('completed', 'Завершено'), ('cancelled', 'Скасовано')], default='pending', max_length=20, verbose_name='Статус'),
        ),
    ]