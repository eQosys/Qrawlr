from GrammarRule import *
from Grammar import Grammar
from GrammarException import GrammarException

from InternalGrammarLoader import load_internal_grammar

HEX_DIGITS = "0123456789abcdefABCDEF"

class GrammarLoader:
    def __init__(self, init_tree: ParseTree = None, path: str = None) -> None:
        self.__path = path

        self.__referenced_rules: dict[str, tuple(bool, list[tuple[int, int]])] = {}
        self.rules = dict()

        if init_tree is not None:
            self.__load_rules_from_tree(init_tree)
        elif path is not None:
            self.__load_rules_from_file(path)
        else:
            raise GrammarException("GrammarLoader needs either a path or a tree")

        self.__check_for_unknown_references()

    def get_grammar(self) -> Grammar:
        return Grammar(self.rules)

    def __load_rules_from_file(self, path: str) -> None:
        with open(path, "r") as f:
            text = f.read()

        g = load_internal_grammar()
        result = g.apply_to(text, "Grammar", path)
        tree = result.tree
        max_pos = result.farthest_match_position

        if tree is None or max_pos.index < len(text):
            raise self.__make_exception("Unable to load grammar", max_pos)
        
        self.__load_rules_from_tree(tree)

    def __check_for_unknown_references(self) -> None:
        err_msgs = []
        for name, references in self.__referenced_rules.items():
            if name not in self.rules:
                for line, col in references:
                    err_msgs.append(self.__make_exception(f"Undefined rule '{name}'", col, line))
        
        if len(err_msgs) > 0:
            raise self.__make_exception("Found undefined references:\n" + "\n".join([str(e) for e in err_msgs]), addPosition=False)
    
    def __is_exact_match(self, tree: ParseTree, value: str = None) -> bool:
        if not isinstance(tree, ParseTreeExactMatch):
            return False
        if value is not None and tree.value != value:
            return False
        return True

    def __expect_exact_match(self, tree: ParseTree, value: str = None) -> None:
        if not self.__is_exact_match(tree):
            raise self.__make_exception(f"Expected 'ParseTreeExactMatch' but got '{type(tree)}'", tree.position_begin)
        if not self.__is_exact_match(tree, value):
            raise self.__make_exception(f"Expected {repr(value)} but got {repr(tree.value)}", tree.position_begin)

    def __is_node(self, tree: ParseTree, name: str = None) -> bool:
        if not isinstance(tree, ParseTreeNode):
            return False
        if name is not None and tree.name != name:
            return False
        return True

    def __expect_node(self, tree: ParseTree, name: str = None) -> None:
        if not self.__is_node(tree):
            raise self.__make_exception(f"Expected 'ParseTreeNode' but got '{type(tree)}'", tree.position_begin)
        if not self.__is_node(tree, name):
            raise self.__make_exception(f"Expected '{name}' but got '{tree.name}", tree.position_begin)

    def __load_rules_from_tree(self, init_tree: ParseTree) -> None:
        self.__expect_node(init_tree)
        
        for child in init_tree.children:
            if self.__is_node(child, "RuleDefinition"):
                rule = self.__load_rule_definition_from_tree(child)
                self.rules[rule.name] = rule
            elif self.__is_node(child, "Comment"):
                pass
            elif self.__is_node(child):
                raise self.__make_exception(f"Expected 'RuleDefinition' or 'Comment' but got {child.name}", child.position_begin)
            else:
                raise self.__make_exception(f"Expected 'ParseTreeNode' but got {type(child)}", child.position_begin)

    def __load_rule_definition_from_tree(self, tree: ParseTree) -> Rule:
        self.__expect_node(tree, "RuleDefinition")

        rule = self.__load_rule_header_from_tree(tree.children[0])
        rule.options = self.__load_rule_body_from_tree(tree.children[1])

        return rule
    
    def __load_rule_header_from_tree(self, tree: ParseTree) -> Rule:
        self.__expect_node(tree, "RuleHeader")

        rule = Rule()

        self.__expect_node(tree.children[0], "Identifier")
        rule.name = tree.children[0].children[0].value

        if rule.name in self.rules:
            raise self.__make_exception(f"Rule with name '{rule.name}' already exists", tree.children[0].position_begin)

        for i in range(1, len(tree.children)):
            child = tree.children[i]
            if self.__is_node(child, "RuleModifier"):
                self.__load_rule_modifier_from_tree(rule, child)
            else:
                raise self.__make_exception(f"Expected 'RuleModifier' but got {child.name}", child.position_begin)

        return rule
    
    def __load_rule_modifier_from_tree(self, rule: Rule, tree: ParseTree) -> None:
        self.__expect_node(tree, "RuleModifier")

        name = tree.children[0].value

        if name == "hidden":
            rule.anonymous = True
        elif name == "fuse":
            rule.fuse_children = True
        else:
            raise self.__make_exception(f"Unknown rule modifier '{name}'", tree.children[0].position_begin)
        
    def __load_rule_body_from_tree(self, tree: ParseTree) -> None:
        self.__expect_node(tree, "RuleBody")

        options = []
        for child in tree.children:
            if self.__is_node(child, "RuleOptionDefinition"):
                options.append(self.__load_rule_option_definition_from_tree(child))
            elif self.__is_node(child, "Comment"):
                pass
            elif self.__is_node(child):
                raise self.__make_exception(f"Expected 'RuleOptionDefinition' or 'Comment' but got {child.name}", child.position_begin)
            else:
                raise self.__make_exception(f"Expected 'ParseTreeNode' but got {type(child)}", child.position_begin)
            
        return options

    def __load_rule_option_definition_from_tree(self, tree: ParseTree) -> Matcher:
        self.__expect_node(tree, "RuleOptionDefinition")

        rule_option = MatcherMatchAll()

        for child in tree.children:
            rule_option.options.append(self.__load_full_matcher_from_tree(child))

        return rule_option
    
    def __load_full_matcher_from_tree(self, tree: ParseTree) -> Matcher:
        self.__expect_node(tree, "FullMatcher")

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
            raise self.__make_exception(f"Unknown matcher '{tree.name}'", tree.position_begin)
        
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

        self.__expect_node(tree, "EscapeSequence")

        value = tree.children[0].value

        if value.startswith("x"):
            return chr(int(value[1:], 16))
    
        if len(value) != 1 or ord(value) not in SHORT_ESCAPES:
            raise self.__make_exception("Unknown escape sequence", tree.position_begin)

        return value.translate(SHORT_ESCAPES)        

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
                raise self.__make_exception(f"Expected 'MatcherModifier*' but got '{child.name}'", child.position_begin)
            else:
                raise self.__make_exception(f"Expected 'ParseTreeNode' but got '{type(child)}'", child.position_begin)
    
    def __load_matcher_modifier_quantifier_from_tree(self, matcher: Matcher, tree: ParseTree) -> None:
        self.__expect_node(tree, "MatcherModifierQuantifier")
        tree = tree.children[0]

        if self.__is_node(tree, "QuantifierSymbolic"):
            value = tree.children[0].value
            if value == QUANTIFIER_ZERO_OR_ONE:
                matcher.count_min = 0
                matcher.count_max = 1
            elif value == QUANTIFIER_ZERO_OR_MORE:
                matcher.count_min = 0
                matcher.count_max = -1
            elif value == QUANTIFIER_ONE_OR_MORE:
                matcher.count_min = 1
                matcher.count_max = -1
            else:
                raise self.__make_exception(f"Unknown quantifier '{value}", tree.children[0].position_begin)
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
            raise self.__make_exception(f"Expected 'Quantifier*' but got '{tree.name}'", tree.position_begin)
        else:
            raise self.__make_exception(f"Expected 'ParseTreeNode' but got '{type(tree)}'", tree.position_begin)

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
            elif self.__is_node(child, "MatchedText"):
                args.append((ACTION_ARG_TYPE_MATCH, None))
            elif self.__is_node(child):
                raise self.__make_exception(f"Expected 'Identifier', 'String' or 'Match' but got '{child.name}'", child.position_begin)
            else:
                raise self.__make_exception(f"Expected 'ParseTreeNode' but got '{type(child)}'", child.position_begin)

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
            raise self.__make_exception(f"Unknown integer format '{base_str}'", tree.position_begin)

        return int(tree.children[0].value, base)

    def __make_exception(self, msg: str, pos: Position = None) -> GrammarException:
        return GrammarException(msg, self.__path, pos)
