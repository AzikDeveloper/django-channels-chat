# Generated by Django 4.0.3 on 2022-03-09 13:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='baseuser',
            name='online',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='baseuser',
            name='avatar',
            field=models.ImageField(upload_to='avatars/'),
        ),
    ]
