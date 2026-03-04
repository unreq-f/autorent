from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PromoCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=32, unique=True, verbose_name='Код')),
                ('discount_pct', models.PositiveIntegerField(default=10, help_text='Відсоток знижки від фінальної суми', verbose_name='Знижка (%)')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активний')),
                ('valid_until', models.DateField(blank=True, help_text='Залиште порожнім — без обмеження дати', null=True, verbose_name='Діє до')),
                ('used_count', models.PositiveIntegerField(default=0, editable=False, verbose_name='Використань')),
                ('max_uses', models.PositiveIntegerField(default=0, help_text='0 — необмежено', verbose_name='Макс. використань')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Промокод',
                'verbose_name_plural': 'Промокоди',
                'ordering': ['-created_at'],
            },
        ),
    ]