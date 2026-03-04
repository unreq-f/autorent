from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_car_photos'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='delivery_address',
            field=models.CharField(blank=True, max_length=255, verbose_name='Адреса доставки'),
        ),
        migrations.AlterField(
            model_name='booking',
            name='pickup_location',
            field=models.CharField(choices=[('office', 'Офіс, вул. Клочківська, 94а'), ('airport', 'Аеропорт «Харків»'), ('station', 'Залізничний вокзал'), ('delivery', 'Доставка по місту'), ('delivery_out', 'Доставка за місто')], default='office', max_length=20, verbose_name='Місце'),
        ),
    ]