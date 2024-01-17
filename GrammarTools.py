class Position:
    def __init__(self, index: int, line: int, column: int):
        self.index = index
        self.line = line
        self.column = column

def escape_string(string: str) -> str:
    string = string.replace("\\", '\\\\')
    string = string.replace("\t", '\\t')
    string = string.replace("\"", '\\"')
    string = string.replace("\n", '\\n')
    return string