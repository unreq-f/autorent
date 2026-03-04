import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_car_is_popular'),
    ]

    operations = [
        migrations.CreateModel(
            name='CarPhoto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='cars/gallery/', verbose_name='Фото')),
                ('caption', models.CharField(blank=True, max_length=100, verbose_name='Підпис')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
                ('is_main', models.BooleanField(default=False, verbose_name='Головне фото')),
                ('car', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='photos', to='core.car')),
            ],
            options={
                'verbose_name': 'Фото авто',
                'verbose_name_plural': 'Фото авто',
                'ordering': ['order', 'id'],
            },
        ),
    ]