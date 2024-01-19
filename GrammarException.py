from GrammarTools import Position

class GrammarException(Exception):
    def __init__(self, message, path = None, position: Position = None):
        pos_str = ""
        if path is not None:
            pos_str += path
        if position is not None:
            if path is None:
                pos_str += "<unknown>"
            pos_str += f":{position.line}:{position.column}"

        if pos_str:
            pos_str += ": "

        super().__init__(f"{pos_str}{message}")