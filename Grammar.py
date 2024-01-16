from GrammarRule import RuleSet
from GrammarTools import escape_string
from GrammarParseTree import ParseTree
from GrammarLoader import GrammarLoader
from GrammarException import GrammarException

class Grammar:
    def __init__(self, filename: str = None) -> None:
        self.ruleset = RuleSet()
        
        if filename is not None:
            self.ruleset = GrammarLoader(filename).ruleset

    def apply_to(self, string: str, rule: str, filename: str) -> ParseTree:
        if rule not in self.ruleset.rules:
            raise GrammarException(f"Rule '{rule}' not found")
        
        self.ruleset.reset()
        tree, index = self.ruleset.rules[rule].match(string, 0, self.ruleset, filename)

        if tree is not None:
            tree.name = rule

        if not self.ruleset.stacks_are_empty():
            raise GrammarException("Stacks not empty after parsing")

        return tree

    def generate_python_code(self, func_name: str = "load_grammar_grammar", add_includes: bool = True) -> str:
        result = ""
        if add_includes:
            result += "from Grammar import Grammar\n"
            result += "from GrammarRule import MatcherInitializers, RuleSet\n"
            result += "from GrammarRule import Rule, MatcherMatchAnyChar\n"
            result += "from GrammarRule import MatcherMatchAll, MatcherMatchAny\n"
            result += "from GrammarRule import MatcherMatchRange, MatcherMatchExact\n"
            result += "from GrammarRule import MatcherMatchRule, MatcherMatchStack\n"

        result += f"def {func_name}() -> Grammar:\n"

        result += "    rules: dict[str, Rule] = {}\n"
        for name, rule in self.ruleset.rules.items():
            result += f"    rules['{name}'] = {rule._generate_python_code()}\n"

        result += "    stack_names: set[str] = {"
        for name in self.ruleset.stacks.keys():
            result += f"'{escape_string(name)}', "
        result += "}\n"

        result += "    ruleset = RuleSet(rules, stack_names)\n"

        result += "    g = Grammar()\n"
        result += "    g.ruleset = ruleset\n"
        result += "    return g\n"

        return result

    def __str__(self) -> str:
        result = ""
        for _, rule in self.ruleset.rules.items():
            result += f"{rule}\n"
        
        return result
