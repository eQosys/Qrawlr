from GrammarLoader import GrammarLoader
from GrammarParseTree import ParseTree
from GrammarException import GrammarException
from GrammarRule import Rule

class Grammar:
    def __init__(self, filename: str) -> None:
        self.ruleset: dict[str, Rule] = GrammarLoader(filename).ruleset

    def apply_to(self, string: str, rule: str) -> ParseTree:
        if rule not in self.ruleset:
            raise GrammarException(f"Rule '{rule}' not found")
        
        tree, length = self.ruleset[rule].match(string, self.ruleset)

        if tree is not None:
            tree.name = rule

        return tree

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
        return "\n".join([f"{'~' if v.anonymous else ''}{k}: {v}" for k, v in self.ruleset.items()])
