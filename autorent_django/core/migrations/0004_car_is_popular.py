from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_contactmessage'),
    ]

    operations = [
        migrations.AddField(
            model_name='car',
            name='is_popular',
            field=models.BooleanField(default=False, verbose_name='Популярний'),
        ),
    ]