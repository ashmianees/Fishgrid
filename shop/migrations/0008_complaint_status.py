# Generated by Django 5.1.1 on 2024-10-13 07:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0007_categoryrequest_reason'),
    ]

    operations = [
        migrations.AddField(
            model_name='complaint',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('responded', 'Responded'), ('resolved', 'Resolved')], default='pending', max_length=20),
        ),
    ]
