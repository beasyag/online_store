# Generated manually

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0007_subcategory_product_subcategory'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='product_type',
        ),
        migrations.RemoveField(
            model_name='product',
            name='material',
        ),
        migrations.RemoveField(
            model_name='product',
            name='shoe_size',
        ),
        migrations.RemoveField(
            model_name='product',
            name='fragrance_top_notes',
        ),
        migrations.RemoveField(
            model_name='product',
            name='fragrance_heart_notes',
        ),
        migrations.RemoveField(
            model_name='product',
            name='fragrance_base_notes',
        ),
        migrations.RemoveField(
            model_name='product',
            name='volume_ml',
        ),
        migrations.RemoveField(
            model_name='product',
            name='metal_type',
        ),
        migrations.RemoveField(
            model_name='product',
            name='metal_purity',
        ),
        migrations.RemoveField(
            model_name='product',
            name='gemstone',
        ),
        migrations.RemoveField(
            model_name='product',
            name='weight_g',
        ),
        migrations.DeleteModel(
            name='ProductType',
        ),
    ]
