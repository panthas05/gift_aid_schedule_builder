# gift_aid_schedule_builder, a script for building gift aid schedules for UK-based
# charities - Copyright (C) 2024  Peter Thomas

import re


def clean_key(reference_or_identifier: str) -> str:
    return re.sub(
        r"[^a-z]+",
        "",
        reference_or_identifier.lower(),
    )
