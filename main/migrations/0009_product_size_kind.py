from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0008_remove_product_type_and_attributes'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='size_kind',
            field=models.CharField(
                choices=[('clothing', 'Clothing'), ('shoes', 'Shoes')],
                default='clothing',
                help_text='Shoes: label as shoe sizes; add numeric EU/US rows via product sizes below.',
                max_length=20,
            ),
        ),
    ]
