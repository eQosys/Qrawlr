def escape_string(string: str, backslash_count: int = 2) -> str:
    backslashs = "\\" * backslash_count
    string = string.replace("\\", backslashs)
    string = string.replace("\t", backslashs + 't')
    string = string.replace("\"", backslashs + '"')
    string = string.replace("\n", backslashs + 'n')
    return string

def index_to_line_and_column(text: str, column: int) -> tuple[int, int]:
    line = text.count("\n", 0, column) + 1
    last_line_break = text.rfind("\n", 0, column)
    return (line, column - last_line_break)