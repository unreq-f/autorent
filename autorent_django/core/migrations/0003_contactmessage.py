from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_promocode'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContactMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name="Ім'я")),
                ('phone', models.CharField(blank=True, max_length=30, verbose_name='Телефон')),
                ('email', models.EmailField(max_length=254, verbose_name='Email')),
                ('subject', models.CharField(choices=[('booking', 'Питання щодо бронювання'), ('conditions', 'Умови прокату'), ('support', 'Технічна підтримка'), ('corporate', 'Корпоративне співробітництво'), ('other', 'Інше')], default='other', max_length=20, verbose_name='Тема')),
                ('message', models.TextField(verbose_name='Повідомлення')),
                ('status', models.CharField(choices=[('new', 'Нове'), ('read', 'Прочитано'), ('replied', 'Відповідено')], default='new', max_length=10, verbose_name='Статус')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата')),
                ('reply', models.TextField(blank=True, verbose_name='Відповідь менеджера')),
            ],
            options={
                'verbose_name': 'Повідомлення з форми',
                'verbose_name_plural': 'Повідомлення з форми',
                'ordering': ['-created_at'],
            },
        ),
    ]