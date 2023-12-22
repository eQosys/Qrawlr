def escape_string(string: str, double_backslash: bool = True) -> str:
    string = string.replace("\t", "\\t")
    string = string.replace("\"", "\\\"")
    string = string.replace("\n", "\\n")
    if double_backslash:
        string = string.replace("\\", "\\\\")
    return string