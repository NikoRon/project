from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('pages', '0002_alter_account_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='card_pin',
            field=models.CharField(default='0000', max_length=4),
        ),
        migrations.CreateModel(
            name='AuditEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('username', models.CharField(max_length=150)),
                ('event', models.CharField(max_length=100)),
                ('details', models.CharField(blank=True, max_length=255)),
            ],
        ),
    ]
