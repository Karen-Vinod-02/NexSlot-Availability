from django.db import migrations, models


ROLE_CHOICES = [
    ("Admin", "Administrator"),
    ("Faculty", "Faculty"),
    ("Student", "Student"),
    ("Employee", "Employee"),
]


def migrate_corporate_students(apps, schema_editor):
    database = schema_editor.connection.alias
    SystemConfig = apps.get_model("classroom", "SystemConfig")
    if SystemConfig.objects.using(database).filter(pk=1, org_type="Corporate").exists():
        apps.get_model("classroom", "User").objects.using(database).filter(
            role="Student"
        ).update(role="Employee")
        apps.get_model("classroom", "AuthorizedEmail").objects.using(database).filter(
            role="Student"
        ).update(role="Employee")


def restore_corporate_students(apps, schema_editor):
    database = schema_editor.connection.alias
    SystemConfig = apps.get_model("classroom", "SystemConfig")
    if SystemConfig.objects.using(database).filter(pk=1, org_type="Corporate").exists():
        apps.get_model("classroom", "User").objects.using(database).filter(
            role="Employee"
        ).update(role="Student")
        apps.get_model("classroom", "AuthorizedEmail").objects.using(database).filter(
            role="Employee"
        ).update(role="Student")


class Migration(migrations.Migration):

    dependencies = [
        ("classroom", "0011_document_uploaded_by"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(choices=ROLE_CHOICES, max_length=20),
        ),
        migrations.AlterField(
            model_name="authorizedemail",
            name="role",
            field=models.CharField(choices=ROLE_CHOICES, max_length=20),
        ),
        migrations.RunPython(migrate_corporate_students, restore_corporate_students),
    ]
