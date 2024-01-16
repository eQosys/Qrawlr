from GrammarException import GrammarException
from GrammarRule import *

NAME_TYPE_RULE = "Rule name"
NAME_TYPE_OPTIONAL = "Optional name"
NAME_TYPE_STACK = "Stack name"

class GrammarLoader:
    def __init__(self, filename: str) -> None:
        self.filename: str = filename
        self.optional_names = set[str]()
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
                if line.startswith("\\"):
                    continue
                self.lines.append((lineCount, line))

    def __load_rules(self) -> None:
        self.__referenced_rules: dict[str, tuple(bool, list[tuple[int, int]])] = {}

        self.rules = dict()
        self.stack_names = set()

        while True:
            try:
                rule = self.__get_parse_rule_definition()
                self.rules[rule.name] = rule
            except IndexError:
                break

        self.ruleset = RuleSet(self.rules, self.stack_names)

    def __check_if_name_exists(self, name: str, name_type: str, col: int, exclude_own_type: bool = False) -> None:
        namesets = (
            (NAME_TYPE_RULE, self.rules.keys()),
            (NAME_TYPE_OPTIONAL, self.optional_names),
            (NAME_TYPE_STACK, self.stack_names)
        )

        for other_type, names in namesets:
            if exclude_own_type and name_type == other_type:
                continue
            if name in names:
                raise self.__make_exception(f"{name_type} '{name}' already exists as {other_type.lower()}", col)

    def __check_for_unknown_references(self) -> None:
        err_msgs = []
        for name, references in self.__referenced_rules.items():
            if name not in self.ruleset.rules:
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

        rule.name, col = self.__get_parse_identifier(line, 0)
        self.__check_if_name_exists(rule.name, NAME_TYPE_RULE, col)
        self.rules[rule.name] = None
        rule.anonymous, rule.fuse_children, line, col = self.__get_parse_rule_definition_header_modifiers(line, col)

        if line[col] != ":":
            raise self.__make_exception("Expected ':' after rule name", col)
        col += 1

        return rule
    
    def __get_parse_identifier(self, line: str, col: int) -> (str, int):
        begin = col

        while col < len(line) and line[col].isalnum():
            col += 1

        name = line[begin:col]

        if name == "":
            raise self.__make_exception("Expected identifier", begin)
        if not name.isalnum():
            raise self.__make_exception("Identifiers must be alphanumeric", begin)
        if not name[0].isalpha():
            raise self.__make_exception("Identifiers must begin with an alpha character", begin)

        return name, col
    
    def __get_parse_literal_integer(self, line: str, col: int) -> (int, int):
        begin = col

        while col < len(line) and line[col].isdigit():
            col += 1

        value = line[begin:col]

        if value == "":
            raise self.__make_exception("Expected integer", begin)
        
        return int(value), col
    
    def __get_parse_literal_string(self, line: str, col: int) -> (str, int):
        begin = col

        content = ""

        while col < len(line) and line[col] != "\"":
            if line[col] == "\\":
                part, col = self.__parse_escape_sequence(line, col+1)
                content += part
            else:
                content += line[col]
                col += 1
        
        if col >= len(line) or line[col] != "\"":
            raise self.__make_exception("Expected closing '\"'", col)
        col += 1

        return content, col
        
    def __parse_escape_sequence(self, line: str, col: int) -> (str, int):
        SHORT_ESCAPES = {
            ord("a"):  "\a",
            ord("b"):  "\b",
            ord("e"):  "\e",
            ord("f"):  "\f",
            ord("n"):  "\n",
            ord("r"):  "\r",
            ord("t"):  "\t",
            ord("v"):  "\v",
            ord("\\"): "\\",
            ord("'"):  "'",
            ord("\""): "\""
        }

        if col >= len(line):
            raise self.__make_exception("Expected escape sequence after '\\'", col)
    
        if ord(line[col]) in SHORT_ESCAPES:
            return line[col].translate(SHORT_ESCAPES), col+1
        
        if line[col] == "x":
            col += 1
            if col+1 >= len(line):
                raise self.__make_exception("Expected hex digit after '\\x'", col)
            
            if not line[col].isxdigit() or not line[col+1].isxdigit():
                raise self.__make_exception("Expected hex digit after '\\x'", col)
            
            return chr(int(line[col:col+2], 16)), col+2

        raise self.__make_exception("Unknown escape sequence", col)

    def __get_parse_rule_definition_header_modifiers(self, line: str, col: int) -> (bool, bool, str, int):
        anonymous = False
        fuse_children = False

        if col >= len(line):
            return anonymous, fuse_children, line, col

        if line[col] != "(":
            return anonymous, fuse_children, line, col
        col += 1

        col = self.__parse_whitespace(line, col, True)
        
        while line[col] != ")":
            param, col = self.__get_parse_identifier(line, col)
            if param == "hidden":
                anonymous = True
            elif param == "fuse":
                fuse_children = True
            else:
                raise self.__make_exception(f"Unknown rule modifier '{param}'", col)
            
            col = self.__parse_whitespace(line, col, True)

        if line[col] != ")":
            raise self.__make_exception("Expected closing ')'", col)
        col += 1

        return anonymous, fuse_children, line, col
    
    def __get_parse_rule_definition_body(self) -> list[Matcher]:
        rule_options: list[Matcher] = []

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

            rule_option = MatcherMatchAll()
            while col < len(line):
                matcher, col = self.__get_parse_matcher(line, col)
                if matcher is None:
                    raise self.__make_exception("Expected rule option", col)
                rule_option.options.append(matcher)

            rule_options.append(rule_option)

        if len(rule_options) == 0:
            raise self.__make_exception("Rule must have at least one option")

        return rule_options

    def __get_parse_matcher(self, line: str, col: int) -> (Matcher, int):      
        if line[col] == ".":
            option, col = self.__get_parse_matcher_match_any_char(line, col+1)
        elif line[col] == "(":
            option, col = self.__get_parse_matcher_match_all(line, col+1)
        elif line[col] == "[":
            option, col = self.__get_parse_matcher_match_any(line, col+1)
        elif line[col] == "'":
            option, col = self.__get_parse_matcher_match_range(line, col+1)
        elif line[col] == "\"":
            option, col = self.__get_parse_matcher_match_exact(line, col+1)
        elif line[col] == ":":
            option, col = self.__get_parse_matcher_match_stack(line, col+1)
        else:
            option, col = self.__get_parse_matcher_match_rule(line, col)

        if option is None:
            return None, col

        col = self.__parse_matcher_modifiers(line, col, option)
        col = self.__parse_whitespace(line, col, True)

        col = self.__parse_matcher_actions(line, col, option)
        col = self.__parse_whitespace(line, col, True)

        return option, col
    
    def __get_parse_matcher_match_any_char(self, line: str, col: int) -> (MatcherMatchAnyChar, int):
        return MatcherMatchAnyChar(), col

    def __get_parse_matcher_match_all(self, line: str, col: int) -> (MatcherMatchAll, int):
        option = MatcherMatchAll()

        col = self.__parse_whitespace(line, col, True)

        while col < len(line) and line[col] != ")":
            sub_option, col = self.__get_parse_matcher(line, col)
            if sub_option is None:
                return None, col
            option.options.append(sub_option)

        if col >= len(line):
            raise self.__make_exception("Expected closing ')'", col)

        return option, col+1
    
    def __get_parse_matcher_match_any(self, line: str, col: int) -> (MatcherMatchAny, int):
        option = MatcherMatchAny()

        col = self.__parse_whitespace(line, col, True)

        while col < len(line) and line[col] != "]":
            sub_option, col = self.__get_parse_matcher(line, col)
            if sub_option is None:
                return None, col
            option.options.append(sub_option)

        if col >= len(line):
            raise self.__make_exception("Expected closing ']'", col)

        return option, col+1
    
    def __get_parse_matcher_match_range(self, line: str, col: int) -> (MatcherMatchRange, int):
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
        col += 1

        if first >= last:
            raise self.__make_exception("Invalid range", col)

        return MatcherMatchRange(first, last), col
    
    def __get_parse_matcher_match_exact(self, line: str, col: int) -> (MatcherMatchExact, int):
        value, col = self.__get_parse_literal_string(line, col)

        # TODO: Empty strings are allowed for now
        #       but they should be disallowed, because the are "useless"
        #       and can cause infinite loops.
        #       Allowed for now, for actions to work.
        #if value == "":
        #    raise self.__make_exception("Empty string not allowed", begin)
        
        return MatcherMatchExact(value), col
    
    def __get_parse_matcher_match_stack(self, line: str, col: int) -> (MatcherMatchStack, int):
        name, col = self.__get_parse_identifier(line, col)
        self.__check_if_name_exists(name, NAME_TYPE_STACK, col, True)
        self.stack_names.add(name)

        if line[col] != ".":
            raise self.__make_exception("Expected '.'", col)
        col += 1

        index, col = self.__get_parse_literal_integer(line, col)

        if line[col] != ":":
            raise self.__make_exception("Expected ':'", col)

        return MatcherMatchStack(name, index), col+1

    def __get_parse_matcher_match_rule(self, line: str, col: int) -> (MatcherMatchRule, int):
        begin = col

        name, col = self.__get_parse_identifier(line, col)

        if name not in self.__referenced_rules:
            self.__referenced_rules[name] = []
        self.__referenced_rules[name].append((self.__last_line_id, begin))
        
        return MatcherMatchRule(name), col

    def __parse_matcher_modifiers(self, line: str, col: int, option: Matcher) -> int:
        option.inverted, col = self.__get_parse_matcher_modifier_inverted(line, col)
        (option.count_min, option.count_max), col = self.__get_parse_matcher_modifier_quantifier(line, col)
        option.look_ahead, col = self.__get_parse_matcher_modifier_look_ahead(line, col)
        option.omit_match, col = self.__get_parse_matcher_modifier_omit_match(line, col)
        option.match_repl, col = self.__get_parse_matcher_modifier_match_replacement(line, col)
        return col

    def __parse_matcher_actions(self, line: str, col: int, option: Matcher) -> int:
        if col >= len(line) or line[col] != "{":
            return col
        col += 1

        col = self.__parse_whitespace(line, col, True)

        while line[col] != "}":
            exec_name, col = self.__get_parse_identifier(line, col)
            col = self.__parse_whitespace(line, col, False)
            
            stack_name, col = self.__get_parse_identifier(line, col)
            self.stack_names.add(stack_name)
            col = self.__parse_whitespace(line, col, True)
            
            option.actions.append((exec_name, stack_name))

            if line[col] != ",":
                break

        if line[col] != "}":
            raise self.__make_exception("Expected closing '}'", col)

        return col+1

    def __get_parse_matcher_modifier_inverted(self, line: str, col: int) -> (bool, int):
        if col < len(line) and line[col] == "!":
            return True, col+1
        return False, col

    def __get_parse_matcher_modifier_quantifier(self, line: str, col: int) -> (str, int):
        if col >= len(line):
            return (1, 1), col

        if line[col] == QUANTIFIER_ZERO_OR_ONE:
            return (0, 1), col+1
        if line[col] == QUANTIFIER_ZERO_OR_MORE:
            return (0, -1), col+1
        if line[col] == QUANTIFIER_ONE_OR_MORE:
            return (1, -1), col+1

        if line[col] == QUANTIFIER_SPECIFY_RANGE:
            col += 1

            if col >= len(line):
                raise self.__make_exception("Expected quantifier range", col)
            
            if line[col] == QUANTIFIER_SPECIFY_LOWER_BOUND:
                col += 1
                minimum, col = self.__get_parse_literal_integer(line, col)
                minimum += 1
                if minimum < 0:
                    raise self.__make_exception("Quantifier range cannot be negative", col)
                return (minimum, -1), col
            if line[col] == QUANTIFIER_SPECIFY_UPPER_BOUND:
                col += 1
                maximum, col = self.__get_parse_literal_integer(line, col)
                maximum -= 1
                if maximum < 0:
                    raise self.__make_exception("Quantifier range cannot be negative", col)
                return (0, maximum), col

            minimum, col = self.__get_parse_literal_integer(line, col)

            if col < len(line) and line[col] == "-":
                col += 1
                maximum, col = self.__get_parse_literal_integer(line, col)
            else:
                maximum = minimum
            
            if minimum < 0 or maximum < 0:
                raise self.__make_exception("Quantifier range cannot be negative", col)

            if minimum > maximum:
                raise self.__make_exception("Invalid quantifier range", col)
            
            if minimum == 0 and maximum == 0:
                raise self.__make_exception("Quantifier range cannot be zero", col)
            
            return (minimum, maximum), col

        return (1, 1), col
    
    def __get_parse_matcher_modifier_look_ahead(self, line: str, col: int) -> (bool, int):
        if col < len(line) and line[col] == "~":
            return True, col+1
        return False, col
    
    def __get_parse_matcher_modifier_omit_match(self, line: str, col: int) -> (bool, int):
        if col < len(line) and line[col] == "_":
            return True, col+1
        return False, col
    
    def __get_parse_matcher_modifier_match_replacement(self, line: str, col: int) -> ((int, str), int):
        if not line.startswith("->", col):
            return None, col
        col += 2

        if col >= len(line):
            raise self.__make_exception("Expected match replacement", col)

        if line[col] == "\"":
            text, col = self.__get_parse_literal_string(line, col+1)
            return (MATCH_REPL_STRING, text), col
        
        if line[col] == ":":
            rOpt, col = self.__get_parse_matcher_match_stack(line, col+1)
            return (MATCH_REPL_STACK, f"{rOpt.name}.{rOpt.index}"), col

        name, col = self.__get_parse_identifier(line, col)
        self.__check_if_name_exists(name, NAME_TYPE_OPTIONAL, col, True)
        self.optional_names.add(name)
        return (MATCH_REPL_IDENTIFIER, name), col

    def __parse_whitespace(self, line: str, col: int, optional: bool) -> int:
        begin = col
        while col < len(line) and line[col] in " \t":
            col += 1

        if not optional and col == begin:
            raise self.__make_exception("Expected whitespace", col)

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
