# Generated by Django 5.0.6 on 2025-02-14 04:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0016_alter_orderdeliveryassignment_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderdeliveryassignment',
            name='otp',
            field=models.CharField(blank=True, max_length=6, null=True),
        ),
    ]
