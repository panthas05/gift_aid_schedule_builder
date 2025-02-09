import re


def clean_key(reference_or_identifier: str) -> str:
    return re.sub(
        r"[^a-z]+",
        "",
        reference_or_identifier.lower(),
    )
