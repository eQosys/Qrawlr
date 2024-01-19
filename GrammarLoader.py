from GrammarException import GrammarException
from GrammarRule import *

NAME_TYPE_RULE = "Rule name"
NAME_TYPE_OPTIONAL = "Optional name"
NAME_TYPE_STACK = "Stack name"

HEX_DIGITS = "0123456789abcdefABCDEF"

class GrammarLoader:
    def __init__(self, path: str = None, init_tree: ParseTree = None) -> None:
        self.__referenced_rules: dict[str, tuple(bool, list[tuple[int, int]])] = {}
        self.rules = dict()

        if path is not None:
            self.__load_rules_from_file(path)
        elif init_tree is not None:
            self.__load_rules_from_tree(init_tree)
        else:
            raise GrammarException("GrammarLoader needs either a path or a tree")

        self.__check_for_unknown_references()

    def __load_rules_from_file(self, path: str) -> None:
        self.filename = path

        self.__load_lines()

        while True:
            try:
                rule = self.__get_parse_rule_definition()
                self.rules[rule.name] = rule
            except IndexError:
                break

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

    def __check_if_rule_name_exists(self, name: str, col: int) -> None:
        if name in self.rules.keys():
            raise self.__make_exception(f"'{name}' already exists", col)

    def __check_for_unknown_references(self) -> None:
        err_msgs = []
        for name, references in self.__referenced_rules.items():
            if name not in self.rules:
                for line, col in references:
                    err_msgs.append(self.__make_exception(f"Undefined rule '{name}'", col, line))
        
        if len(err_msgs) > 0:
            raise self.__make_exception("Found undefined references:\n" + "\n".join([str(e) for e in err_msgs]), addPosition=False)

    def __get_parse_rule_definition(self) -> Rule:
        rule = self.__get_parse_rule_definition_header()
        rule.options = self.__get_parse_rule_options()
        return rule

    def __get_parse_rule_definition_header(self) -> Rule:
        rule = Rule()
        line = self.__get_next_line()

        rule.name, col = self.__get_parse_identifier(line, 0)
        self.__check_if_rule_name_exists(rule.name, col)
        self.rules[rule.name] = None
        rule.anonymous, rule.fuse_children, line, col = self.__get_parse_rule_definition_header_modifiers(line, col)

        if col >= len(line) or line[col] != ":":
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
            
            if not line[col] in HEX_DIGITS or not line[col+1] in HEX_DIGITS:
                raise self.__make_exception("Expected hex digit after '\\x'", col)
            
            return chr(int(line[col:col+2], 16)), col+2

        raise self.__make_exception("Unknown escape sequence", col)

    def __get_parse_rule_definition_header_modifiers(self, line: str, col: int) -> (bool, bool, str, int):
        anonymous = False
        fuse_children = False

        if col >= len(line) or line[col] != "(":
            return anonymous, fuse_children, line, col
        col += 1

        col = self.__parse_whitespace(line, col, True)
        
        while col < len(line) and line[col] != ")":
            param, col = self.__get_parse_identifier(line, col)
            if param == "hidden":
                anonymous = True
            elif param == "fuse":
                fuse_children = True
            else:
                raise self.__make_exception(f"Unknown rule modifier '{param}'", col)
            
            col = self.__parse_whitespace(line, col, True)

        if col >= len(line) or line[col] != ")":
            raise self.__make_exception("Expected closing ')'", col)
        col += 1

        return anonymous, fuse_children, line, col
    
    def __get_parse_rule_options(self) -> list[Matcher]:
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

            rule_options.append(self.__get_parse_rule_option(line, col))

        if len(rule_options) == 0:
            raise self.__make_exception("Rule must have at least one rule option")

        return rule_options
    
    def __get_parse_rule_option(self, line: str, col: int) -> Matcher:
        rule_option = MatcherMatchAll()
        while col < len(line):
            matcher, col = self.__get_parse_matcher(line, col)
            if matcher is None:
                raise self.__make_exception("Expected matcher", col)
            rule_option.options.append(matcher)
        
        return rule_option

    def __get_parse_matcher(self, line: str, col: int) -> (Matcher, int):      
        if line[col] == ".":
            matcher, col = self.__get_parse_matcher_match_any_char(line, col+1)
        elif line[col] == "(":
            matcher, col = self.__get_parse_matcher_match_all(line, col+1)
        elif line[col] == "[":
            matcher, col = self.__get_parse_matcher_match_any(line, col+1)
        elif line[col] == "'":
            matcher, col = self.__get_parse_matcher_match_range(line, col+1)
        elif line[col] == "\"":
            matcher, col = self.__get_parse_matcher_match_exact(line, col+1)
        elif line[col] == ":":
            matcher, col = self.__get_parse_matcher_match_stack(line, col+1)
        else:
            matcher, col = self.__get_parse_matcher_match_rule(line, col)

        if matcher is None:
            return None, col

        col = self.__parse_matcher_modifiers(line, col, matcher)
        col = self.__parse_whitespace(line, col, True)

        col = self.__parse_matcher_actions(line, col, matcher)
        col = self.__parse_whitespace(line, col, True)

        return matcher, col
    
    def __get_parse_matcher_match_any_char(self, line: str, col: int) -> (MatcherMatchAnyChar, int):
        return MatcherMatchAnyChar(), col

    def __get_parse_matcher_match_all(self, line: str, col: int) -> (MatcherMatchAll, int):
        matcher = MatcherMatchAll()

        col = self.__parse_whitespace(line, col, True)

        while col < len(line) and line[col] != ")":
            sub_matcher, col = self.__get_parse_matcher(line, col)
            if sub_matcher is None:
                return None, col
            matcher.options.append(sub_matcher)

        if col >= len(line):
            raise self.__make_exception("Expected closing ')'", col)

        return matcher, col+1
    
    def __get_parse_matcher_match_any(self, line: str, col: int) -> (MatcherMatchAny, int):
        matcher = MatcherMatchAny()

        col = self.__parse_whitespace(line, col, True)

        while col < len(line) and line[col] != "]":
            sub_matcher, col = self.__get_parse_matcher(line, col)
            if sub_matcher is None:
                return None, col
            matcher.options.append(sub_matcher)

        if col >= len(line):
            raise self.__make_exception("Expected closing ']'", col)

        return matcher, col+1
    
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

        if col >= len(line) or line[col] != ".":
            raise self.__make_exception("Expected '.'", col)
        col += 1

        index, col = self.__get_parse_literal_integer(line, col)

        if col >= len(line) or line[col] != ":":
            raise self.__make_exception("Expected ':'", col)

        return MatcherMatchStack(name, index), col+1

    def __get_parse_matcher_match_rule(self, line: str, col: int) -> (MatcherMatchRule, int):
        begin = col

        name, col = self.__get_parse_identifier(line, col)

        if name not in self.__referenced_rules:
            self.__referenced_rules[name] = []
        self.__referenced_rules[name].append((self.__last_line_id, begin))
        
        return MatcherMatchRule(name), col

    def __parse_matcher_modifiers(self, line: str, col: int, matcher: Matcher) -> int:
        matcher.inverted, col = self.__get_parse_matcher_modifier_inverted(line, col)
        (matcher.count_min, matcher.count_max), col = self.__get_parse_matcher_modifier_quantifier(line, col)
        matcher.look_ahead, col = self.__get_parse_matcher_modifier_look_ahead(line, col)
        matcher.omit_match, col = self.__get_parse_matcher_modifier_omit_match(line, col)
        matcher.match_repl, col = self.__get_parse_matcher_modifier_match_replacement(line, col)
        return col

    def __parse_matcher_actions(self, line: str, col: int, matcher: Matcher) -> int:
        if col >= len(line) or line[col] != "{":
            return col
        col += 1

        col = self.__parse_whitespace(line, col, True)

        while col < len(line) and line[col] != "}":
            col = self.__parse_matcher_action_trigger(line, col, matcher)
            col = self.__parse_whitespace(line, col, True)

            if col >= len(line) or line[col] != ",":
                break
            col += 1

            col = self.__parse_whitespace(line, col, True)

        if col >= len(line) or line[col] != "}":
            raise self.__make_exception("Expected closing '}'", col)
        col += 1

        return col
    
    def __parse_matcher_action_trigger(self, line: str, col: int, matcher: Matcher) -> int:
        trigger_name, col = self.__get_parse_identifier(line, col)
        if not trigger_name in ACTION_TRIGGERS:
            raise self.__make_exception(f"Unknown action trigger '{trigger_name}'", col)

        col = self.__parse_whitespace(line, col, True)

        if col >= len(line) or line[col] != ":":
            raise self.__make_exception("Expected ':'", col)
        
        col = self.__parse_whitespace(line, col+1, True)

        if col >= len(line):
            raise self.__make_exception("Expected at least one action", col)

        if is_action_list := line[col] == "[":
            col += 1
            col = self.__parse_whitespace(line, col, True)

        while col < len(line) and line[col] != "]":
            col = self.__parse_matcher_action(line, col, matcher, trigger_name)

            if not is_action_list:
                break

            col = self.__parse_whitespace(line, col, True)

            if col >= len(line) or line[col] != ",":
                break
            col += 1

            col = self.__parse_whitespace(line, col, True)

        if is_action_list:
            if col >= len(line) or line[col] != "]":
                raise self.__make_exception("Expected closing ']'", col)
            col += 1

        return col

    def __parse_matcher_action(self, line: str, col: int, matcher: Matcher, trigger_name: str) -> int:
        action_name, col = self.__get_parse_identifier(line, col)
        col = self.__parse_whitespace(line, col, True)

        if col >= len(line) or line[col] != "(":
            raise self.__make_exception("Expected '('", col)
        col += 1
        
        col = self.__parse_whitespace(line, col, True)

        args = []
        while col < len(line) and line[col] != ")":
            if line[col] == "\"":
                arg, col = self.__get_parse_literal_string(line, col+1)
                args.append((ACTION_ARG_TYPE_STRING, arg))
            elif line[col] == "_":
                col += 1
                args.append((ACTION_ARG_TYPE_MATCH, None))
            else:
                arg, col = self.__get_parse_identifier(line, col)
                args.append((ACTION_ARG_TYPE_IDENTIFIER, arg))
            
            col = self.__parse_whitespace(line, col, True)

            if col >= len(line) or line[col] != ",":
                break
            col += 1

            col = self.__parse_whitespace(line, col, True)

        if col >= len(line) or line[col] != ")":
            raise self.__make_exception("Expected closing ')'", col)
        col += 1

        actions = matcher.actions.get(trigger_name, [])
        actions.append((action_name, args))
        matcher.actions[trigger_name] = actions
        
        return col

    def __get_parse_matcher_modifier_inverted(self, line: str, col: int) -> (bool, int):
        if col < len(line) and line[col] == "!":
            return True, col+1
        return False, col

    def __get_parse_matcher_modifier_quantifier(self, line: str, col: int) -> ((int, int), int):
        if col >= len(line):
            return (1, 1), col

        if line[col] == QUANTIFIER_ZERO_OR_ONE:
            return (0, 1), col+1
        if line[col] == QUANTIFIER_ZERO_OR_MORE:
            return (0, -1), col+1
        if line[col] == QUANTIFIER_ONE_OR_MORE:
            return (1, -1), col+1

        if line[col] == QUANTIFIER_SPECIFY_RANGE:
            return self.__get_parse_matcher_modifier_range(line, col+1)

        return (1, 1), col
    
    def __get_parse_matcher_modifier_range(self, line: str, col: int) -> ((int, int), int):
        if col >= len(line):
            raise self.__make_exception("Expected quantifier range", col)

        if line[col] in [QUANTIFIER_SPECIFY_LOWER_BOUND, QUANTIFIER_SPECIFY_UPPER_BOUND]:
            return self.__get_parse_matcher_modifier_quantifier_open_range(line, col)

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
    
    def __get_parse_matcher_modifier_quantifier_open_range(self, line: str, col: int) -> ((int, int), int):
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
        
        raise self.__make_exception("Expected quantifier open range", col)
    
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
    
    def __is_exact_match(self, tree: ParseTree, value: str = None) -> bool:
        if not isinstance(tree, ParseTreeExactMatch):
            return False
        if value is not None and tree.value != value:
            return False
        return True

    def __expect_exact_match(self, tree: ParseTree, value: str = None) -> None:
        if not self.__is_exact_match(tree, value):
            raise GrammarException("Expected 'ParseTreeExactMatch' but got", type(tree))

    def __is_node(self, tree: ParseTree, name: str = None) -> bool:
        if not isinstance(tree, ParseTreeNode):
            return False
        if name is not None and tree.name != name:
            return False
        return True

    def __expect_node(self, tree: ParseTree, name: str = None) -> None:
        if not self.__is_node(tree, name):
            raise GrammarException(f"Expected '{name}' but got", tree.name)

    def __load_rules_from_tree(self, init_tree: ParseTree) -> None:
        self.__expect_node(init_tree)
        
        for child in init_tree.children:
            self.__expect_node(child)
            
            if self.__is_node(child, "RuleDefinition"):
                rule = self.__load_rule_definition_from_tree(child)
                self.rules[rule.name] = rule
            elif self.__is_node(child, "Comment"):
                pass
            elif self.__is_node(child):
                raise GrammarException("Expected 'RuleDefinition' but got", child.name)
            else:
                raise GrammarException("Expected 'ParseTreeNode' but got", type(child))

    def __load_rule_definition_from_tree(self, tree: ParseTree) -> Rule:
        self.__expect_node(tree, "RuleDefinition")

        if len(tree.children) < 2:
            raise GrammarException("Expected at least 2 children but got", len(tree.children))

        rule = self.__load_rule_header_from_tree(tree.children[0])
        rule.options = self.__load_rule_body_from_tree(tree.children[1])

        return rule
    
    def __load_rule_header_from_tree(self, tree: ParseTree) -> Rule:
        self.__expect_node(tree, "RuleHeader")

        rule = Rule()

        self.__expect_node(tree.children[0], "Identifier")
        rule.name = tree.children[0].children[0].value

        if rule.name in self.rules:
            raise GrammarException(f"'{rule.name}' already exists")

        for i in range(1, len(tree.children)):
            child = tree.children[i]
            if self.__is_node(child, "RuleModifier"):
                self.__load_rule_modifier_from_tree(rule, child)
            else:
                raise GrammarException("Expected 'RuleModifier' but got", child.name)

        return rule
    
    def __load_rule_modifier_from_tree(self, rule: Rule, tree: ParseTree) -> None:
        self.__expect_node(tree, "RuleModifier")

        name = tree.children[0].value

        if name == "hidden":
            rule.anonymous = True
        elif name == "fuse":
            rule.fuse_children = True
        else:
            raise GrammarException("Unknown rule modifier", name)
        
    def __load_rule_body_from_tree(self, tree: ParseTree) -> None:
        self.__expect_node(tree, "RuleBody")

        options = []
        for child in tree.children:
            if self.__is_node(child, "RuleOptionDefinition"):
                options.append(self.__load_rule_option_definition_from_tree(child))
            elif self.__is_node(child, "Comment"):
                pass
            elif self.__is_node(child):
                raise GrammarException("Expected 'RuleOptionDefinition' but got", child.name)
            else:
                raise GrammarException("Expected 'ParseTreeNode' but got", type(child))
            
        return options

    def __load_rule_option_definition_from_tree(self, tree: ParseTree) -> Matcher:
        self.__expect_node(tree, "RuleOptionDefinition")

        if len(tree.children) == 0:
            raise GrammarException("Expected at least 1 matcher but got 0")

        rule_option = MatcherMatchAll()

        for child in tree.children:
            rule_option.options.append(self.__load_full_matcher_from_tree(child))

        return rule_option
    
    def __load_full_matcher_from_tree(self, tree: ParseTree) -> Matcher:
        self.__expect_node(tree, "FullMatcher")

        if len(tree.children) != 3:
            raise GrammarException("Expected 3 children but got", len(tree.children))

        matcher = self.__load_matcher_from_tree(tree.children[0])

        self.__load_matcher_modifiers_from_tree(matcher, tree.children[1])
        self.__load_matcher_actions_from_tree(matcher, tree.children[2])

        return matcher
    
    def __load_matcher_from_tree(self, tree: ParseTree) -> Matcher:
        self.__expect_node(tree)

        if self.__is_node(tree, "MatchAnyChar"):
            matcher = MatcherMatchAnyChar()
        elif self.__is_node(tree, "MatchAll"):
            matcher = MatcherMatchAll()
            for child in tree.children:
                matcher.options.append(self.__load_full_matcher_from_tree(child))
        elif self.__is_node(tree, "MatchAny"):
            matcher = MatcherMatchAny()
            for child in tree.children:
                matcher.options.append(self.__load_full_matcher_from_tree(child))
        elif self.__is_node(tree, "MatchRange"):
            matcher = MatcherMatchRange(tree.children[0].children[0].value, tree.children[1].children[0].value)
        elif self.__is_node(tree, "MatchExact"):
            matcher = MatcherMatchExact(self.__load_string_from_tree(tree.children[0]))
        elif self.__is_node(tree, "MatchRule"):
            matcher = MatcherMatchRule(tree.children[0].children[0].value)
        elif self.__is_node(tree, "MatchStack"):
            matcher = MatcherMatchStack(tree.children[0].children[0].value, self.__load_integer_from_tree(tree.children[1]))
        else:
            raise GrammarException(f"Unknown matcher '{tree.name}'")
        
        return matcher
    
    def __load_string_from_tree(self, tree: ParseTree) -> str:
        self.__expect_node(tree, "String")
        result = ""

        for child in tree.children:
            if self.__is_node(child, "EscapeSequence"):
                result += self.__load_escape_sequence_from_tree(child)
            elif self.__is_exact_match(child):
                result += child.value

        return result

    def __load_escape_sequence_from_tree(self, tree: ParseTree) -> str:
        self.__expect_node(tree, "EscapeSequence")

        value = tree.children[0].value

        if value.startswith("x"):
            return chr(int(value[1:], 16))
        
        return eval(f"'\\{value}'")

    def __load_matcher_modifiers_from_tree(self, matcher: Matcher, tree: ParseTree) -> None:
        self.__expect_node(tree, "MatcherModifiers")

        for child in tree.children:
            if self.__is_node(child, "MatcherModifierInvert"):
                matcher.inverted = True
            elif self.__is_node(child, "MatcherModifierQuantifier"):
                self.__load_matcher_modifier_quantifier_from_tree(matcher, child)
            elif self.__is_node(child, "MatcherModifierLookAhead"):
                matcher.look_ahead = True
            elif self.__is_node(child, "MatcherModifierOmitMatch"):
                matcher.omit_match = True
            elif self.__is_node(child, "MatcherModifierReplaceMatch"):
                matcher.match_repl = self.__load_matcher_modifier_replace_match_from_tree(child)
            elif self.__is_node(child):
                raise GrammarException("Expected 'MatcherModifier' but got", child.name)
            else:
                raise GrammarException("Expected 'ParseTreeNode' but got", type(child))
    
    def __load_matcher_modifier_quantifier_from_tree(self, matcher: Matcher, tree: ParseTree) -> None:
        self.__expect_node(tree, "MatcherModifierQuantifier")
        tree = tree.children[0]

        if self.__is_node(tree, "QuantifierSymbolic"):
            if tree.children[0].value == QUANTIFIER_ZERO_OR_ONE:
                matcher.count_min = 0
                matcher.count_max = 1
            elif tree.children[0].value == QUANTIFIER_ZERO_OR_MORE:
                matcher.count_min = 0
                matcher.count_max = -1
            elif tree.children[0].value == QUANTIFIER_ONE_OR_MORE:
                matcher.count_min = 1
                matcher.count_max = -1
            else:
                raise GrammarException("Unknown quantifier", tree.children[0].value)
        elif self.__is_node(tree, "QuantifierRange"):
            matcher.count_min = self.__load_integer_from_tree(tree.children[0])
            matcher.count_max = self.__load_integer_from_tree(tree.children[1])
        elif self.__is_node(tree, "QuantifierExact"):
            matcher.count_min = self.__load_integer_from_tree(tree.children[0])
            matcher.count_max = matcher.count_min
        elif self.__is_node(tree, "QuantifierLowerBound"):
            matcher.count_min = self.__load_integer_from_tree(tree.children[0]) + 1
            matcher.count_max = -1
        elif self.__is_node(tree, "QuantifierUpperBound"):
            matcher.count_min = 0
            matcher.count_max = self.__load_integer_from_tree(tree.children[0]) - 1
        elif self.__is_node(tree):
            raise GrammarException("Expected 'Quantifier' but got", tree.name)
        else:
            raise GrammarException("Expected 'ParseTreeNode' but got", type(tree))

    def __load_matcher_modifier_replace_match_from_tree(self, tree: ParseTree) -> tuple[int, str]:
        self.__expect_node(tree, "MatcherModifierReplaceMatch")
        tree = tree.children[0]

        if self.__is_node(tree, "Identifier"):
            return (MATCH_REPL_IDENTIFIER, tree.children[0].value)
        elif self.__is_node(tree, "String"):
            return (MATCH_REPL_STRING, tree.children[0].value)
        elif self.__is_node(tree, "MatchStack"):
            return (MATCH_REPL_STACK, f"{tree.children[0].children[0].value}.{self.__load_integer_from_tree(tree.children[1])}")

    def __load_matcher_actions_from_tree(self, matcher: Matcher, tree: ParseTree) -> None:
        self.__expect_node(tree, "MatcherActions")

        for child in tree.children:
            self.__load_matcher_trigger_from_tree(matcher, child)

    def __load_matcher_trigger_from_tree(self, matcher: Matcher, tree: ParseTree) -> None:
        self.__expect_node(tree, "MatcherTrigger")
        
        trigger_name = tree.children[0].children[0].value

        matcher.actions[trigger_name] = []

        for child in tree.children[1].children:
            matcher.actions[trigger_name].append(self.__load_matcher_action_from_tree(child))

    def __load_matcher_action_from_tree(self, tree: ParseTree) -> tuple[str, list[tuple[str, str]]]:
        self.__expect_node(tree, "MatcherAction")

        action_name = tree.children[0].children[0].value

        args = []
        for child in tree.children[1].children:
            if self.__is_node(child, "Identifier"):
                args.append((ACTION_ARG_TYPE_IDENTIFIER, child.children[0].value))
            elif self.__is_node(child, "String"):
                args.append((ACTION_ARG_TYPE_STRING, child.children[0].value))
            elif self.__is_node(child, "Match"):
                args.append((ACTION_ARG_TYPE_MATCH, None))
            else:
                raise GrammarException("Expected 'Identifier', 'String' or 'Match' but got", child.name)

        return (action_name, args)

    def __load_integer_from_tree(self, tree: ParseTree) -> int:
        self.__expect_node(tree, "Integer")
        base_str = tree.children[1].name
        if base_str == "FormatHex":
            base = 16
        elif base_str == "FormatBin":
            base = 2
        elif base_str == "FormatOct":
            base = 8
        elif base_str == "FormatDec":
            base = 10
        else:
            raise GrammarException("Unknown integer format", base_str)

        return int(tree.children[0].value, base)

    def __make_exception(self, msg: str, column: int = None, line: int = None, addPosition: bool = True) -> GrammarException:
        if addPosition:
            column = 1 if column is None else column+1
            line = self.__last_line_id if line is None else line
            errPos = f"{self.filename}:{line}:{column}:"
        else:
            errPos = ""
        return GrammarException(f"{errPos} {msg}")
