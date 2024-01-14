def escape_string(string: str) -> str:
    string = string.replace("\\", '\\\\')
    string = string.replace("\t", '\\t')
    string = string.replace("\"", '\\"')
    string = string.replace("\n", '\\n')
    return string

def index_to_line_and_column(text: str, column: int) -> tuple[int, int]:
    line = text.count("\n", 0, column) + 1
    last_line_break = text.rfind("\n", 0, column)
    return (line, column - last_line_break)