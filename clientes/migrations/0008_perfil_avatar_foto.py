from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clientes', '0007_perfil_avatar_estilo_perfil_avatar_semilla'),
    ]

    operations = [
        migrations.AddField(
            model_name='perfil',
            name='avatar_foto',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/'),
        ),
    ]
