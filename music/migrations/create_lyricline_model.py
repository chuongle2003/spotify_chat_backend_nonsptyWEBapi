from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('music', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LyricLine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.FloatField(help_text='Thời điểm hiển thị lời (tính bằng giây)')),
                ('text', models.TextField()),
                ('song', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lyric_lines', to='music.song')),
            ],
            options={
                'db_table': 'lyric_lines',
                'ordering': ['timestamp'],
            },
        ),
    ] 