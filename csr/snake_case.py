import re

camel_case_to_snake_case_pattern = re.compile('(?!^)([A-Z]+)')


def camel_case_to_snake_case(camel_case_text: str) -> str:
    return camel_case_to_snake_case_pattern.sub(r'_\1', camel_case_text).lower()
