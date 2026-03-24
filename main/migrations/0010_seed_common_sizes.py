from django.db import migrations


def seed_sizes(apps, schema_editor):
    Size = apps.get_model('main', 'Size')
    clothing = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
    shoes_eu = [str(n) for n in range(35, 49)]
    for name in clothing + shoes_eu:
        Size.objects.get_or_create(name=name)


def unseed_sizes(apps, schema_editor):
    Size = apps.get_model('main', 'Size')
    Size.objects.filter(
        name__in=['XS', 'S', 'M', 'L', 'XL', 'XXL']
        + [str(n) for n in range(35, 49)]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0009_product_size_kind'),
    ]

    operations = [
        migrations.RunPython(seed_sizes, unseed_sizes),
    ]
