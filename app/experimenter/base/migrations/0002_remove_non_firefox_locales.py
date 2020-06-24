# Generated by Django 3.0.7 on 2020-06-23 19:25

from django.db import migrations

# Locales which appear in the Locale fixture but do not appear in
# https://hg.mozilla.org/mozilla-central/raw-file/tip/browser/locales/l10n-changesets.json
NON_FIREFOX_LOCALES = [
    "ak",
    "am-et",
    "as",
    "azz",
    "bm",
    "bn-BD",
    "bn-IN",
    "crh",
    "csb",
    "dbg",
    "de-AT",
    "de-CH",
    "de-DE",
    "ee",
    "en-AU",
    "en-NZ",
    "en-ZA",
    "es",
    "fj-FJ",
    "fur-IT",
    "ga",
    "gu",
    "ha",
    "hi",
    "ig",
    "kok",
    "ks",
    "ku",
    "la",
    "lg",
    "ln",
    "mai",
    "mg",
    "mi",
    "ml",
    "mn",
    "nr",
    "nso",
    "or",
    "pa",
    "rw",
    "sa",
    "sah",
    "sat",
    "sr-Cyrl",
    "sr-Latn",
    "ss",
    "st",
    "sw",
    "ta-IN",
    "ta-LK",
    "tn",
    "ts",
    "tsz",
    "tt-RU",
    "ve",
    "x-testing",
    "yo",
    "zu",
]


def remove_locales(apps, schema_editor):
    Locale = apps.get_model("base", "Locale")
    Locale.objects.all().filter(code__in=NON_FIREFOX_LOCALES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(remove_locales),
    ]
