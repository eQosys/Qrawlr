def escape_string(string: str, backslash_count: int = 2) -> str:
    backslashs = "\\" * backslash_count
    string = string.replace("\\", backslashs)
    string = string.replace("\t", backslashs + 't')
    string = string.replace("\"", backslashs + '"')
    string = string.replace("\n", backslashs + 'n')
    return string