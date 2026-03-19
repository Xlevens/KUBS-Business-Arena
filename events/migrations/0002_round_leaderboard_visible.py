from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='round',
            name='leaderboard_visible',
            field=models.BooleanField(default=False),
        ),
    ]
