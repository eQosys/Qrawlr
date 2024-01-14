from GrammarLoader import GrammarLoader
from GrammarParseTree import ParseTree
from GrammarException import GrammarException
from GrammarRule import RuleSet

class Grammar:
    def __init__(self, filename: str = None) -> None:
        self.ruleset = RuleSet()
        
        if filename is not None:
            self.ruleset = GrammarLoader(filename).ruleset

    def apply_to(self, string: str, rule: str) -> ParseTree:
        if rule not in self.ruleset.rules:
            raise GrammarException(f"Rule '{rule}' not found")
        
        self.ruleset.reset()
        tree, index, length = self.ruleset.rules[rule].match(string, 0, self.ruleset)

        if tree is not None:
            tree.name = rule

        if not self.ruleset.stacks_are_empty():
            raise GrammarException("Stacks not empty after parsing")

        return tree

    def generate_python_code(self, func_name: str = "load_grammar_grammar", add_includes: bool = True) -> str:
        result = ""
        if add_includes:
            result += "from GrammarRule import Rule, RuleOption, RuleOptionMatchAll, RuleOptionMatchAny, RuleOptionMatchRange, RuleOptionMatchExact, RuleOptionMatchRule\n"
        result += f"def {func_name}() -> dict[str, Rule]:\n"
        result += "    ruleset: dict[str, Rule] = {}\n"
        for name, rule in self.ruleset.items():
            result += f"    ruleset['{name}'] = {rule._generate_python_code()}\n"

        result += "    g = Grammar()\n"
        result += "    g.ruleset = ruleset\n"
        result += "    return g\n"

        return result

    def __str__(self) -> str:
        result = ""
        for name, rule in self.ruleset.items():
            modifiers = []
            if rule.anonymous:
                modifiers.append("hidden")
            if rule.fuse_children:
                modifiers.append("fuse")
            if len(modifiers) > 0:
                name += "(" + " ".join(modifiers) + ")"
            result += f"{name}: {rule}\n"
        return result
