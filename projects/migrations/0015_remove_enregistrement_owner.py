# Generated by Django 4.2.1 on 2023-06-15 20:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0014_enregistrement_owner'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='enregistrement',
            name='owner',
        ),
    ]
