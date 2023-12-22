from GrammarException import GrammarException
from GrammarRule import *

class GrammarLoader:
    def __init__(self, filename: str) -> None:
        self.filename: str = filename
        self.__load_lines()
        self.__load_rules()
        self.__check_for_unknown_references()

    def __load_lines(self) -> None:
        self.lines: list[tuple[int, str]] = []

        lineCount = 0
        with open(self.filename, "r") as f:
            for line in f:
                lineCount += 1
                line = line.rstrip()
                if line == "":
                    continue
                if line.startswith("#"):
                    continue
                self.lines.append((lineCount, line))

    def __load_rules(self) -> None:
        self.ruleset: RuleSet = {}
        self.__referenced_rules: dict[str, tuple(bool, list[tuple[int, int]])] = {}

        while True:
            try:
                rule = self.__get_parse_rule_definition()
                self.ruleset[rule.name] = rule
            except IndexError:
                break

    def __check_for_unknown_references(self) -> None:
        err_msgs = []
        for name, references in self.__referenced_rules.items():
            if name not in self.ruleset:
                for line, col in references:
                    err_msgs.append(self.__make_exception(f"Undefined rule '{name}'", col, line))
        
        if len(err_msgs) > 0:
            raise self.__make_exception("Found undefined references:\n" + "\n".join([str(e) for e in err_msgs]), addPosition=False)

    def __get_parse_rule_definition(self) -> Rule:
        rule = self.__get_parse_rule_definition_header()
        rule.options = self.__get_parse_rule_definition_body()
        return rule

    def __get_parse_rule_definition_header(self) -> Rule:
        rule = Rule()
        line = self.__get_next_line()

        if not line.endswith(":"):
            raise self.__make_exception("Expected ':' after rule name", len(line))
        line = line[:-1]

        rule.name, line = self.__get_parse_rule_definition_header_name(line)
        rule.anonymous, rule.fuse_children, line = self.__get_parse_rule_definition_header_modifiers(line)

        return rule
    
    def __get_parse_rule_definition_header_anonymous(self, line: str) -> (bool, str):
        if line.startswith("~"):
            return True, line[1:]
        return False, line
    
    def __get_parse_rule_definition_header_fuse_children(self, line: str) -> (bool, str):
        if line.startswith("+"):
            return True, line[1:]
        return False, line
    
    def __get_parse_rule_definition_header_name(self, line: str) -> (str, str):
        for i in range(len(line)):
            if not line[i].isalnum():
                name = line[:i]
                break
        else:
            name = line

        if name == "":
            raise self.__make_exception("Expected rule name")
        if not name[0].isalpha():
            raise self.__make_exception("Rule name must start with a letter")
        if name in self.ruleset:
            raise self.__make_exception("Rule name already exists")
        
        return name, line[i:]
    
    def __get_parse_rule_definition_header_modifiers(self, line: str) -> (bool, bool, str):
        anonymous = False
        fuse_children = False

        if not line.startswith("("):
            return anonymous, fuse_children, line
        
        if not line.endswith(")"):
            raise self.__make_exception("Expected closing ')'")
        
        line = line[1:-1]

        elements = line.split(" ")
        for element in elements:
            if element == "hidden":
                anonymous = True
            elif element == "fuse":
                fuse_children = True
            else:
                raise self.__make_exception(f"Unknown rule modifier '{element}'")

        return anonymous, fuse_children, ""

    def __get_parse_rule_definition_body(self) -> list[RuleOption]:
        rule_options: list[RuleOption] = []

        while True:
            try:
                if not self.__peek_next_line()[0].isspace():
                    break
            except IndexError:
                break
            line = self.__get_next_line()
            for col in range(len(line)):
                if not line[col].isspace():
                    break

            options = RuleOptionMatchAll()
            while col < len(line):
                option, col = self.__get_parse_rule_option(line, col)
                if option is None:
                    raise self.__make_exception("Expected rule option", col)
                options.options.append(option)

            rule_options.append(options)

        if len(rule_options) == 0:
            raise self.__make_exception("Rule must have at least one option")

        return rule_options

    def __get_parse_rule_option(self, line: str, col: int) -> (RuleOption, int):      
        if line[col] == "(":
            option, col = self.__get_parse_rule_option_match_all(line, col+1)
        elif line[col] == "[":
            option, col = self.__get_parse_rule_option_match_any(line, col+1)
        elif line[col] == "'":
            option, col = self.__get_parse_rule_option_match_range(line, col+1)
        elif line[col] == "\"":
            option, col = self.__get_parse_rule_option_match_exact(line, col+1)
        else:
            option, col = self.__get_parse_rule_option_match_rule(line, col)

        if option is None:
            return None, col

        col = self.__parse_rule_option_modifiers(line, col, option)

        col = self.__parse_whitespace(line, col)

        return option, col
        
    def __get_parse_rule_option_match_all(self, line: str, col: int) -> (RuleOptionMatchAll, int):
        option = RuleOptionMatchAll()

        col = self.__parse_whitespace(line, col)

        while col < len(line) and line[col] != ")":
            sub_option, col = self.__get_parse_rule_option(line, col)
            if sub_option is None:
                return None, col
            option.options.append(sub_option)

        if col >= len(line):
            raise self.__make_exception("Expected closing ')'", col)

        return option, col+1
    
    def __get_parse_rule_option_match_any(self, line: str, col: int) -> (RuleOptionMatchAny, int):
        option = RuleOptionMatchAny()

        col = self.__parse_whitespace(line, col)

        while col < len(line) and line[col] != "]":
            sub_option, col = self.__get_parse_rule_option(line, col)
            if sub_option is None:
                return None, col
            option.options.append(sub_option)

        if col >= len(line):
            raise self.__make_exception("Expected closing ']'", col)

        return option, col+1
    
    def __get_parse_rule_option_match_range(self, line: str, col: int) -> (RuleOptionMatchRange, int):
        if col >= len(line):
            raise self.__make_exception("Expected first character of range", col)
        first = line[col]

        col += 1
        if col >= len(line):
            raise self.__make_exception("Expected last character of range", col)
        last = line[col]

        col += 1
        if col >= len(line) or line[col] != "'":
            raise self.__make_exception("Expected closing '''", col)

        if first >= last:
            raise self.__make_exception("Invalid range", col)

        return RuleOptionMatchRange(first, last), col+1
    
    def __get_parse_rule_option_match_exact(self, line: str, col: int) -> (RuleOptionMatchExact, int):
        begin = col

        ESCAPE_CHARS = "\"\\nt"

        while col < len(line) and line[col] != "\"":
            if col < len(line) and line[col] == "\\":
                col += 1
                if col >= len(line):
                    raise self.__make_exception("Expected character after '\\'", col)
                if line[col] not in ESCAPE_CHARS:
                    raise self.__make_exception("Invalid escape sequence", col)
            col += 1
        
        if col >= len(line):
            raise self.__make_exception("Expected closing '\"'", col)

        value = line[begin:col]

        if value == "":
            raise self.__make_exception("Empty string not allowed", begin)

        for c in ESCAPE_CHARS:
            value = value.replace(f"\\{c}", eval(f"\"\\{c}\""))
        
        return RuleOptionMatchExact(value), col+1
    
    def __get_parse_rule_option_match_rule(self, line: str, col: int) -> (RuleOptionMatchRule, int):
        begin = col

        while col < len(line) and line[col].isalnum():
            col += 1

        name = line[begin:col]

        if name == "":
            raise self.__make_exception("Empty rule name not allowed", begin)
        
        if not name.isalnum():
            raise self.__make_exception("Rule name must be alphanumeric", begin)
        
        if not name[0].isalpha():
            raise self.__make_exception("Rule name must start with a letter", begin)

        if name not in self.__referenced_rules:
            self.__referenced_rules[name] = []
        self.__referenced_rules[name].append((self.__last_line_id, begin))
        
        return RuleOptionMatchRule(name), col   

    def __parse_rule_option_modifiers(self, line: str, col: int, option: RuleOption) -> int:
        option.inverted, col = self.__get_parse_rule_option_modifier_inverted(line, col)
        option.quantifier, col = self.__get_parse_rule_option_modifier_quantifier(line, col)
        option.omit_match, col = self.__get_parse_rule_option_modifier_omit_match(line, col)
        return col

    def __get_parse_rule_option_modifier_inverted(self, line: str, col: int) -> (bool, int):
        if col < len(line) and line[col] == "!":
            return True, col+1
        return False, col

    def __get_parse_rule_option_modifier_quantifier(self, line: str, col: int) -> (str, int):
        if col >= len(line):
            return QUANTIFIER_ONE, col
        if line[col] == QUANTIFIER_ZERO_OR_ONE:
            return QUANTIFIER_ZERO_OR_ONE, col+1
        if line[col] == QUANTIFIER_ZERO_OR_MORE:
            return QUANTIFIER_ZERO_OR_MORE, col+1
        if line[col] == QUANTIFIER_ONE_OR_MORE:
            return QUANTIFIER_ONE_OR_MORE, col+1
        if line[col] == QUANTIFIER_ONE:
            return QUANTIFIER_ONE, col+1
        return QUANTIFIER_ONE, col
    
    def __get_parse_rule_option_modifier_omit_match(self, line: str, col: int) -> (bool, int):
        if col < len(line) and line[col] == "_":
            return True, col+1
        return False, col

    def __parse_whitespace(self, line: str, col: int) -> int:
        while col < len(line) and line[col] in " \t":
            col += 1
        return col

    def __peek_next_line(self) -> str:
        return self.lines[0][1]

    def __get_next_line(self) -> str:
        id, line = self.lines.pop(0)
        self.__last_line_id = id
        return line

    def __make_exception(self, msg: str, column: int = None, line: int = None, addPosition: bool = True) -> GrammarException:
        if addPosition:
            column = 1 if column is None else column+1
            line = self.__last_line_id if line is None else line
            errPos = f"{self.filename}:{line}:{column}:"
        else:
            errPos = ""
        return GrammarException(f"{errPos} {msg}")
