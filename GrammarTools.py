def escape_string(string: str) -> str:
    string = string.replace("\\", '\\\\')
    string = string.replace("\t", '\\t')
    string = string.replace("\"", '\\"')
    string = string.replace("\n", '\\n')
    return string

def index_to_position(text: str, index: int) -> tuple[int, int]:
    line = text.count("\n", 0, index) + 1
    last_line_break = text.rfind("\n", 0, index)
    return (line, index - last_line_break)

def make_position_string(filename: str, text: str, index: int) -> str:
    line, col = index_to_position(text, index)
    return f"{filename}:{line}:{col}"