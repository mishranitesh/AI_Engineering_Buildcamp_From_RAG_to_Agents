import re


def extract_code_files(text: str) -> dict:
    # \w+ matches any language identifier (python, java, typescript, etc.)
    pattern = r"###\s+([^\n]+)\n```\w+\n(.*?)```"

    matches = re.findall(pattern, text, re.DOTALL)

    files = {}
    for raw_filename, code in matches:
        filename_match = re.search(r'[\w./-]+\.\w+', raw_filename)
        filename = filename_match.group() if filename_match else raw_filename.strip()
        files[filename] = code.strip()

    return files