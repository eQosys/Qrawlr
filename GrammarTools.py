def escape_string(string: str, double_backslash: bool = True) -> str:
    if double_backslash:
        string = string.replace("\\", "\\\\")
    string = string.replace("\t", "\\t")
    string = string.replace("\"", "\\\"")
    string = string.replace("\n", "\\n")
    return string