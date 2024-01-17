def escape_string(string: str) -> str:
    string = string.replace("\\", '\\\\')
    string = string.replace("\t", '\\t')
    string = string.replace("\"", '\\"')
    string = string.replace("\n", '\\n')
    return string