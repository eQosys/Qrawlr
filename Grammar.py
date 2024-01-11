from GrammarLoader import GrammarLoader
from GrammarParseTree import ParseTree
from GrammarException import GrammarException
from GrammarRule import Rule

class Grammar:
    def __init__(self, filename: str = None) -> None:
        self.ruleset: dict[str, Rule] = {}
        
        if filename is not None:
            self.ruleset = GrammarLoader(filename).ruleset

    def apply_to(self, string: str, rule: str) -> ParseTree:
        if rule not in self.ruleset:
            raise GrammarException(f"Rule '{rule}' not found")
        
        tree, length = self.ruleset[rule].match(string, self.ruleset)

        if tree is not None:
            tree.name = rule

        return tree

    def generate_python_code(self, func_name: str = "load_grammar_grammar", add_includes: bool = True) -> str:
        result = ""
        if add_includes:
            result += "from GrammarRule import Rule, RuleOption, RuleOptionMatchAll, RuleOptionMatchAny, RuleOptionMatchRange, RuleOptionMatchExact, RuleOptionMatchRule\n"
        result += f"def {func_name}() -> dict[str, Rule]:\n"
        result += "    ruleset: dict[str, Rule] = {}\n"
        for name, rule in self.ruleset.items():
            result += f"    ruleset['{name}'] = {rule._generate_python_code()}\n"

        result += "    return ruleset\n"

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
