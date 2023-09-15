# Generated by Django 3.2.16 on 2023-05-15 16:06

from django.db import migrations


def drop_ci_setting(apps, schema_editor):
    Setting = apps.get_model('core', 'Setting')
    Setting.objects.filter(
        name='submission_competing_interests',
    ).delete()


def create_ci_setting(apps, schema_editor):
    SettingGroup = apps.get_model('core', 'SettingGroup')
    Setting = apps.get_model('core', 'Setting')
    Role = apps.get_model('core', 'Role')

    group = SettingGroup.objects.get(name='general')

    setting, c = Setting.objects.get_or_create(
        group=group,
        name='submission_competing_interests',
        defaults={
            'pretty_name': "Enable Competing Interests",
            'types': 'boolean',
            'description': 'Enables the CI submission field.',
            'is_translatable': False,
        },
    )
    roles = Role.objects.filter(
        slug__in=['editor', 'journal-manager']
    )
    setting.editable_by.add(*roles)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0081_alter_account_preferred_timezone'),
    ]

    operations = [
        migrations.RunPython(
            drop_ci_setting,
            reverse_code=create_ci_setting),
    ]