from django.db import migrations


def create_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    groups_data = {
        'Admin': ['add', 'change', 'delete', 'view'],
        'Marketing': ['add', 'change', 'view'],
        'Sales': ['add', 'change', 'view'],
        'Support': ['view'],
    }

    for group_name, actions in groups_data.items():
        group, _ = Group.objects.get_or_create(name=group_name)

        app_models = {
            'accounts': ['customuser', 'otp'],
            'vehicles': ['car', 'carimage'],
            'leads': ['lead', 'appointment'],
            'chatbot': ['chatsession', 'chatmessage'],
            'notifications': ['smslog'],
            'campaigns': ['campaign', 'campaignrecipient'],
        }

        for app_label, models in app_models.items():
            for model_name in models:
                try:
                    ct = ContentType.objects.get(app_label=app_label, model=model_name)
                except ContentType.DoesNotExist:
                    continue

                for action in actions:
                    codename = f'{action}_{model_name}'
                    try:
                        perm = Permission.objects.get(content_type=ct, codename=codename)
                        group.permissions.add(perm)
                    except Permission.DoesNotExist:
                        pass


def reverse_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=['Admin', 'Marketing', 'Sales', 'Support']).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_groups, reverse_groups),
    ]
