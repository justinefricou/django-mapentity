# Generated by Django 3.2.13 on 2022-08-02 14:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('test_app', '0011_alter_dummymodel_date_update'),
    ]

    operations = [
        migrations.AddField(
            model_name='dummymodel',
            name='short_description',
            field=models.TextField(blank=True, default='', help_text='Short description'),
        ),
    ]
