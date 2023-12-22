from abc import ABC, abstractmethod

from GrammarParseTree import *
from GrammarException import *

QUANTIFIER_ZERO_OR_ONE = "?"
QUANTIFIER_ZERO_OR_MORE = "*"
QUANTIFIER_ONE_OR_MORE = "+"
QUANTIFIER_ONE = ""

class RuleOption(ABC):
    def __init__(self) -> None:
        self.inverted = False
        self.quantifier = QUANTIFIER_ONE
        self.omit_match = False

    def match(self, string: str, ruleset: dict[str, "RuleOption"]) -> (ParseTreeNode, int):
        tree = ParseTreeNode()
        length = 0

        count = 0
        while True:
            sub_tree, sub_length = self._match(string[length:], ruleset)
            if sub_tree is None:
                break
            count += 1

            length += sub_length

            tree.add_child(sub_tree, self.omit_match)

            if self.quantifier == QUANTIFIER_ONE:
                break
            if self.quantifier == QUANTIFIER_ZERO_OR_ONE:
                break
            if self.quantifier == QUANTIFIER_ZERO_OR_MORE:
                continue
            if self.quantifier == QUANTIFIER_ONE_OR_MORE:
                continue
        
        if self.quantifier == QUANTIFIER_ZERO_OR_ONE:
            return tree, length
        if self.quantifier == QUANTIFIER_ZERO_OR_MORE:
            return tree, length
        
        if count == 0:
            return None, 0

        return tree, length

    @abstractmethod
    def _match(self, string: str, ruleset: dict[str, "RuleOption"]) -> (ParseTree, int):
        raise NotImplementedError("RuleOption._match() must be implemented by subclasses")
   
    @abstractmethod
    def _to_string(self) -> str:
        raise NotImplementedError("RuleOption.__to_string() must be implemented by subclasses")

    def __str__(self) -> str:
        modifier_str = ""

        if self.inverted:
            modifier_str += "!"

        modifier_str += self.quantifier

        if self.omit_match:
            modifier_str += "_"

        return self._to_string() + modifier_str

RuleSet = dict[str, RuleOption]

class RuleOptionList(RuleOption):
    def __init__(self) -> None:
        super().__init__()
        self.options: list[RuleOption] = []

# (...)
class RuleOptionMatchAll(RuleOptionList):
    def __init__(self) -> None:
        super().__init__()

    def _match(self, string: str, ruleset: RuleSet) -> (ParseTree, int):
        node = ParseTreeNode()
        length = 0
        for option in self.options:
            child, child_length = option.match(string[length:], ruleset)
            if child is None:
                return None, 0
            node.add_child(child)
            length += child_length
        return node, length
    
    def _to_string(self) -> str:
        return f"({' '.join([str(o) for o in self.options])})"

# [...]
class RuleOptionMatchAny(RuleOptionList):
    def __init__(self) -> None:
        super().__init__()

    def _match(self, string: str, ruleset: RuleSet) -> (ParseTree, int):
        for option in self.options:
            node, length = option.match(string, ruleset)
            if node is not None:
                return node, length
        return None, 0
    
    def _to_string(self) -> str:
        return f"[{' '.join([str(o) for o in self.options])}]"

# 'xx'
class RuleOptionMatchRange(RuleOption):
    def __init__(self, first: str, last: str) -> None:
        super().__init__()
        self.first = first
        self.last = last
    
    def _match(self, string: str, ruleset: RuleSet) -> (ParseTree, int):
        if len(string) == 0:
            return None, 0
        if string[0] < self.first or string[0] > self.last:
            return None, 0
        return ParseTreeExactMatch(string[0]), 1
    
    def _to_string(self) -> str:
        return f"'{self.first}{self.last}'"

# "..."
class RuleOptionMatchExact(RuleOption):
    def __init__(self, value: str) -> None:
        super().__init__()
        self.value = value

    def _match(self, string: str, ruleset: RuleSet) -> (ParseTree, int):
        if string.startswith(self.value):
            return ParseTreeExactMatch(self.value), len(self.value)
        return None, 0
    
    def _to_string(self) -> str:
        return f"\"{escape_string(self.value, False)}\""

# rulename
class RuleOptionMatchRule(RuleOption):
    def __init__(self, reference: str) -> None:
        super().__init__()
        self.rulename = reference

    def _match(self, string: str, ruleset: RuleSet) -> (ParseTree, int):
        if self.rulename not in ruleset:
            raise GrammarException(f"Rule '{self.rulename}' not found")
        rule = ruleset[self.rulename]
        tree, length = rule.match(string, ruleset)
        if tree is not None and not rule.anonymous:
            tree.name = self.rulename
        return tree, length
    
    def _to_string(self) -> str:
        return self.rulename

class Rule(RuleOptionMatchAny):
    def __init__(self) -> None:
        super().__init__()
        self.name = None
        self.anonymous = False
        self.fuse_children = False

    def match(self, string: str, ruleset: RuleSet) -> (ParseTree, int):
        tree, length = super().match(string, ruleset)
        if self.fuse_children:
            self.__fuse_children(tree)
        return tree, length
    
    def __fuse_children(self, tree: ParseTreeNode) -> None:
        if tree is None:
            return
        if not isinstance(tree, ParseTreeNode):
            return
        
        i = 0
        leafID = -1
        while i < len(tree.children):
            if isinstance(tree.children[i], ParseTreeExactMatch):
                if leafID < 0:
                    leafID = i
                else:
                    tree.children[leafID].value += tree.children[i].value
                    tree.children.pop(i)
                    i -= 1
            else:
                leafID = -1
            i += 1