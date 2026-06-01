import re


def extract_mermaid(text: str) -> str:
    pattern = r"```mermaid(.*?)```"

    match = re.search(
        pattern,
        text,
        re.DOTALL
    )

    if not match:
        return ""

    return match.group(1).strip()