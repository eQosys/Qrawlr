from abc import ABC, abstractmethod

from GrammarParseTree import *
from GrammarException import *

QUANTIFIER_ZERO_OR_ONE = "?"
QUANTIFIER_ZERO_OR_MORE = "*"
QUANTIFIER_ONE_OR_MORE = "+"
QUANTIFIER_ONE = ""

class RuleOption(ABC):
    def __init__(self, inverted: bool = False, quantifier: str = QUANTIFIER_ONE, omit_match: bool = False) -> None:
        self.inverted = inverted
        self.quantifier = quantifier
        self.omit_match = omit_match

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

    def _modifiers_to_str(self) -> str:
        mod_str = ""

        if self.inverted:
            mod_str += "!"

        mod_str += self.quantifier

        if self.omit_match:
            mod_str += "_"

        return mod_str
    
    def _modifiers_to_arg_str(self) -> str:
        args = []
        args.append(f"inverted={self.inverted}")
        args.append(f"quantifier=\"{self.quantifier}\"")
        args.append(f"omit_match={self.omit_match}")
        return ", ".join(args)

    def __str__(self) -> str:
        return self._to_string() + self._modifiers_to_str()

    @abstractmethod
    def _match(self, string: str, ruleset: dict[str, "RuleOption"]) -> (ParseTree, int):
        raise NotImplementedError("RuleOption._match() must be implemented by subclasses")
   
    @abstractmethod
    def _to_string(self) -> str:
        raise NotImplementedError("RuleOption.__to_string() must be implemented by subclasses")

    @abstractmethod
    def _generate_python_code(self) -> str:
        raise NotImplementedError("RuleOption._generate_python_code() must be implemented by subclasses")

RuleSet = dict[str, RuleOption]

class RuleOptionList(RuleOption):
    def __init__(self, options: list[RuleOption] = [], inverted: bool = False, quantifier: str = QUANTIFIER_ONE, omit_match: bool = False) -> None:
        super().__init__(inverted, quantifier, omit_match)
        self.options: list[RuleOption] = list(options)

    def _generate_python_code_option_list(self) -> str:
        optionStrs = []
        for option in self.options:
            optionStrs.append(option._generate_python_code())
        return f"[ {', '.join(optionStrs)} ]"

# (...)
class RuleOptionMatchAll(RuleOptionList):
    def __init__(self, options: list[RuleOption] = [], inverted: bool = False, quantifier: str = QUANTIFIER_ONE, omit_match: bool = False) -> None:
        super().__init__(options, inverted, quantifier, omit_match)

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
    
    def _generate_python_code(self) -> str:
        return f"RuleOptionMatchAll({self._generate_python_code_option_list()}, {self._modifiers_to_arg_str()})"

# [...]
class RuleOptionMatchAny(RuleOptionList):
    def __init__(self, options: list[RuleOption] = [], inverted: bool = False, quantifier: str = QUANTIFIER_ONE, omit_match: bool = False) -> None:
        super().__init__(options, inverted, quantifier, omit_match)

    def _match(self, string: str, ruleset: RuleSet) -> (ParseTree, int):
        for option in self.options:
            node, length = option.match(string, ruleset)
            if node is not None:
                return node, length
        return None, 0
    
    def _to_string(self) -> str:
        return f"[{' '.join([str(o) for o in self.options])}]"
    
    def _generate_python_code(self) -> str:
        return f"RuleOptionMatchAny({self._generate_python_code_option_list()}, {self._modifiers_to_arg_str()})"

# 'xx'
class RuleOptionMatchRange(RuleOption):
    def __init__(self, first: str, last: str, inverted: bool = False, quantifier: str = QUANTIFIER_ONE, omit_match: bool = False) -> None:
        super().__init__(inverted, quantifier, omit_match)
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

    def _generate_python_code(self) -> str:
        return f"RuleOptionMatchRange(\"{escape_string(self.first, True)}\", \"{escape_string(self.last, True)}\", {self._modifiers_to_arg_str()})"

# "..."
class RuleOptionMatchExact(RuleOption):
    def __init__(self, value: str, inverted: bool = False, quantifier: str = QUANTIFIER_ONE, omit_match: bool = False) -> None:
        super().__init__(inverted, quantifier, omit_match)
        self.value = value

    def _match(self, string: str, ruleset: RuleSet) -> (ParseTree, int):
        if string.startswith(self.value):
            return ParseTreeExactMatch(self.value), len(self.value)
        return None, 0
    
    def _to_string(self) -> str:
        return f"\"{escape_string(self.value, False)}\""
    
    def _generate_python_code(self) -> str:
        return f"RuleOptionMatchExact(\"{escape_string(self.value)}\", {self._modifiers_to_arg_str()})"

# rulename
class RuleOptionMatchRule(RuleOption):
    def __init__(self, rulename: str, inverted: bool = False, quantifier: str = QUANTIFIER_ONE, omit_match: bool = False) -> None:
        super().__init__(inverted, quantifier, omit_match)
        self.rulename = rulename

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
    
    def _generate_python_code(self) -> str:
        return f"RuleOptionMatchRule(\"{escape_string(self.rulename, True)}\", {self._modifiers_to_arg_str()})"

class Rule(RuleOptionMatchAny):
    def __init__(self, name=None, anonymous=False, fuse_children=False, options=[], inverted: bool = False, quantifier: str = QUANTIFIER_ONE, omit_match: bool = False) -> None:
        super().__init__(options, inverted, quantifier, omit_match)
        self.name = name
        self.anonymous = anonymous
        self.fuse_children = fuse_children

    def match(self, string: str, ruleset: RuleSet) -> (ParseTree, int):
        tree, length = super().match(string, ruleset)
        if self.fuse_children:
            self.__fuse_children(tree)
        return tree, length
    
    def _generate_python_code(self) -> str:
        args = []
        args.append(f"name=\"{escape_string(self.name, True)}\"")
        args.append(f"anonymous={self.anonymous}")
        args.append(f"fuse_children={self.fuse_children}")
        args.append(f"options={self._generate_python_code_option_list()}")
        return f"Rule({', '.join(args)}, {self._modifiers_to_arg_str()})"

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

def foo():
    ruleset = {}
    ruleset['Grammar'] = Rule(name="Grammar", anonymous=False, fuse_children=False, options=[ RuleOptionMatchAll([ RuleOptionMatchAny([ RuleOptionMatchRule("RuleDefinition", inverted=False, quantifier="", omit_match=False), RuleOptionMatchRule("Comment", inverted=False, quantifier="", omit_match=True), RuleOptionMatchRule("Whitespace", inverted=False, quantifier="", omit_match=True), RuleOptionMatchExact("\n", inverted=False, quantifier="", omit_match=True) ], inverted=False, quantifier="*", omit_match=False) ], inverted=False, quantifier="", omit_match=False) ], inverted=False, quantifier="", omit_match=False)