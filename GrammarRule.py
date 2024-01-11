from abc import ABC, abstractmethod

from GrammarParseTree import *
from GrammarException import *

QUANTIFIER_ZERO_OR_ONE = "?"
QUANTIFIER_ZERO_OR_MORE = "*"
QUANTIFIER_ONE_OR_MORE = "+"
QUANTIFIER_ONE = ""

class RuleOption(ABC):
    def __init__(self, inverted: bool = False, quantifier: str = QUANTIFIER_ONE, omit_match: bool = False, executors: list[(str, str)] = []) -> None:
        self.inverted = inverted
        self.quantifier = quantifier
        self.omit_match = omit_match
        self.executors = []

    def match(self, string: str, ruleset: "RuleSet") -> (ParseTreeNode, int):
        if isinstance(self, RuleOptionMatchExact):
            if self.value == "\\\"":
                pass

        tree = ParseTreeNode()
        length = 0
        match_count = 0
        checkpoint = ruleset.get_checkpoint()

        while True:
            sub_tree, sub_length = self._apply_optional_invert(string[length:], *self._match(string[length:], ruleset))
            if sub_tree is None:
                break
            match_count += 1

            length += sub_length

            tree.add_child(sub_tree, self.omit_match)

            if self.quantifier == QUANTIFIER_ONE:
                break
            if self.quantifier == QUANTIFIER_ZERO_OR_ONE:
                break
        
        if match_count == 0:
            if self.quantifier == QUANTIFIER_ONE or self.quantifier == QUANTIFIER_ONE_OR_MORE:
                # TODO: Not sure if this is the correct way to handle this, probably not but it works for now
                ruleset.revert_to_checkpoint(checkpoint)
                return None, 0

        self._apply_executors(tree, ruleset)

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
        args.append(f"executors={self._executors_to_arg_str()}")
        return ", ".join(args)

    def _executors_to_arg_str(self) -> str:
        executors = []
        for (operator, operand) in self.executors:
            executors.append(f"(\"{escape_string(operator)}\", \"{escape_string(operand)}\")")
        return f"[ {', '.join(executors)} ]"

    def _apply_optional_invert(self, string: str, tree: ParseTreeNode, length: int) -> (ParseTreeNode, int):
        if not self.inverted:
            return tree, length
        
        if tree is None:
            return ParseTreeExactMatch(string[0]), 1
        
        return None, 0

    def _apply_executors(self, tree: ParseTreeNode, ruleset: "RuleSet") -> None:
        for (operator, operand) in self.executors:
            stack = ruleset.stacks[operand]
            history = ruleset.stack_histories[operand]

            if operator == "push":
                stack.append(str(tree))
                history.append((operator, str(tree)))
            elif operator == "pop":
                value = stack.pop()
                history.append((operator, value))
            else:
                raise GrammarException(f"Unknown executor operator '{operator}'")

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

class RuleSet:
    def __init__(self, rules: dict[str, RuleOption], stack_names: set[str]) -> None:
        self.rules = rules
        self.stacks = dict(map(lambda name : (name, []), stack_names))
        self.stack_histories = dict(map(lambda name : (name, []), stack_names))

    def get_checkpoint(self) -> dict[str, int]:
        return dict(map(lambda name : (name, len(self.stack_histories[name])), self.stack_histories.keys()))
    
    def revert_to_checkpoint(self, checkpoint: dict[str, int]) -> None:
        for name, index in checkpoint.items():
            stack = self.stacks[name]
            history = self.stack_histories[name]
            while len(history) > index:
                operator, value = history.pop()
                if operator == "push":
                    stack.pop()
                elif operator == "pop":
                    stack.append(value)
                else:
                    raise GrammarException(f"Unknown executor operator '{operator}'")

    def clear_stacks(self) -> None:
        for stack in self.stacks.values():
            stack.clear()
        for history in self.stack_histories.values():
            history.clear()

    def stacks_are_empty(self) -> bool:
        for stack in self.stacks.values():
            if len(stack) > 0:
                return False
        return True

class RuleOptionList(RuleOption):
    def __init__(self, options: list[RuleOption] = [], **kwargs) -> None:
        super().__init__(**kwargs)
        self.options: list[RuleOption] = list(options)

    def _generate_python_code_option_list(self) -> str:
        optionStrs = []
        for option in self.options:
            optionStrs.append(option._generate_python_code())
        return f"[ {', '.join(optionStrs)} ]"

# (...)
class RuleOptionMatchAll(RuleOptionList):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

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
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

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
        if len(string) == 0 or string[0] < self.first or string[0] > self.last:
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
            if self.value == "pass":
                pass
            return ParseTreeExactMatch(self.value), len(self.value)
        return None, 0
    
    def _to_string(self) -> str:
        return f"\"{escape_string(self.value, False)}\""
    
    def _generate_python_code(self) -> str:
        return f"RuleOptionMatchExact(\"{escape_string(self.value)}\", {self._modifiers_to_arg_str()})"

class RuleOptionMatchRule(RuleOption):
    def __init__(self, rulename: str, inverted: bool = False, quantifier: str = QUANTIFIER_ONE, omit_match: bool = False) -> None:
        super().__init__(inverted, quantifier, omit_match)
        self.rulename = rulename

    def _match(self, string: str, ruleset: RuleSet) -> (ParseTree, int):
        if self.rulename not in ruleset.rules:
            raise GrammarException(f"Rule '{self.rulename}' not found")
        rule = ruleset.rules[self.rulename]
        tree, length = rule.match(string, ruleset)
        if tree is not None and not rule.anonymous:
            tree.name = self.rulename
        return tree, length
    
    def _to_string(self) -> str:
        return self.rulename
    
    def _generate_python_code(self) -> str:
        return f"RuleOptionMatchRule(\"{escape_string(self.rulename, True)}\", {self._modifiers_to_arg_str()})"

class RuleOptionStackMatchExact(RuleOption):
    def __init__(self, name: str, index: int, **kwargs) -> None:
        super().__init__(**kwargs)
        self.name = name
        self.index = index

    def _match(self, string: str, ruleset: RuleSet) -> (ParseTree, int):
        if not self.name in ruleset.stacks:
            raise GrammarException(f"Stack '{self.name}' not found")
        stack = ruleset.stacks[self.name]
        if self.index >= len(stack):
            to_match = ""
        else:
            to_match = ruleset.stacks[self.name][-self.index-1]

        if string.startswith(to_match):
            return ParseTreeExactMatch(to_match), len(to_match)
        return None, 0
    
    def _to_string(self) -> str:
        return f":{escape_string(self.name)}.{self.index}:"

    def _generate_python_code(self) -> str:
        return f"RuleOptionStackMatchExact({escape_string(self.name)}, {self.index}, {self._modifiers_to_arg_str()})"

class Rule(RuleOptionMatchAny):
    def __init__(self, name=None, anonymous=False, fuse_children=False, **kwargs) -> None:
        super().__init__(**kwargs)
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