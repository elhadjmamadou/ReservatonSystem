# Generated by Django 5.1.1 on 2024-10-18 19:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_resource_alter_reservation_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservation',
            name='is_waitlisted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='resource',
            name='capacity',
            field=models.PositiveIntegerField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='resource',
            name='conditions',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='resource',
            name='equipments',
            field=models.TextField(blank=True),
        ),
    ]
