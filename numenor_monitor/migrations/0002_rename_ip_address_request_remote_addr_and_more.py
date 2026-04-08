from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("numenor_monitor", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="request",
            old_name="ip_address",
            new_name="remote_addr",
        ),
        migrations.AddField(
            model_name="request",
            name="x_forwarded_for",
            field=models.TextField(
                blank=True,
                null=True,
                help_text="Raw value of the X-Forwarded-For header. May contain multiple IPs (client, proxy1, proxy2). Null if not present.",
            ),
        ),
        migrations.AddField(
            model_name="request",
            name="cf_connecting_ip",
            field=models.GenericIPAddressField(
                blank=True,
                null=True,
                help_text="Value of the CF-Connecting-IP header set by Cloudflare. Null if not behind Cloudflare.",
            ),
        ),
    ]
