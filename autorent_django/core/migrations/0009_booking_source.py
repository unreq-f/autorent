from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_profile_docs_booking_return'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='source',
            field=models.CharField(
                choices=[('web','Сайт (повна форма)'),('quick','Швидке замовлення'),('manager','Менеджер')],
                default='web',
                max_length=20,
                verbose_name='Джерело',
            ),
        ),
    ]