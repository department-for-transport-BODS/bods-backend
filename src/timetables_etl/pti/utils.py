from datetime import date

from django.utils import timezone

# TODO: This comes from settings.PTI_ENFORCED_DATE. Hardcode in constants file or add env var?
PTI_ENFORCED_DATE = date(2025, 1, 1)


# TODO: Test
def get_important_note():
    pti_enforced_date = PTI_ENFORCED_DATE
    if pti_enforced_date.date() > timezone.localdate():
        important_note = (
            "Data containing this observation will be rejected by " f'BODS after {date(pti_enforced_date, "jS F, Y")}'
        )
    else:
        important_note = ""

    return important_note