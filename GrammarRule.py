from abc import ABC, abstractmethod

from GrammarParseTree import *
from GrammarException import *
from GrammarTools import index_to_line_and_column

QUANTIFIER_ZERO_OR_ONE = "?"
QUANTIFIER_ZERO_OR_MORE = "*"
QUANTIFIER_ONE_OR_MORE = "+"
QUANTIFIER_ONE = ""

class RuleOptionInitializers:
    def __init__(self, inverted: bool = False, quantifier: str = QUANTIFIER_ONE, look_ahead: bool = False, omit_match: bool = False, alt_name: str = "", executors: list[tuple[str, str]] = []) -> None:
        self.inverted      = inverted
        self.quantifier    = quantifier
        self.look_ahead    = look_ahead
        self.omit_match    = omit_match
        self.alt_name      = alt_name
        self.executors     = executors

class RuleOption(ABC):
    def __init__(self, initializers: RuleOptionInitializers = RuleOptionInitializers()) -> None:
        self.inverted      = initializers.inverted
        self.quantifier    = initializers.quantifier
        self.look_ahead    = initializers.look_ahead
        self.omit_match    = initializers.omit_match
        self.alt_name      = initializers.alt_name
        self.executors     = list(initializers.executors)

    def match(self, string: str, index: int, ruleset: "RuleSet") -> tuple[ParseTree, int]:
        if isinstance(self, RuleOptionMatchExact):
            if self.value == "\\\"":
                pass

        old_index = index
        tree = ParseTreeNode(*index_to_line_and_column(string, index))
        match_count = 0
        checkpoint = ruleset.get_checkpoint()

        while True:
            sub_tree, sub_index = self._match_specific(string, index, ruleset)
            sub_tree, index = self._apply_optional_invert(string, index, sub_index, sub_tree)

            if sub_tree is None:
                break
            match_count += 1

            tree.add_child(sub_tree, self.omit_match)

            if self.quantifier == QUANTIFIER_ONE:
                break
            if self.quantifier == QUANTIFIER_ZERO_OR_ONE:
                break
        
        if match_count == 0:
            if self.quantifier == QUANTIFIER_ONE or self.quantifier == QUANTIFIER_ONE_OR_MORE:
                ruleset.revert_to_checkpoint(checkpoint)
                return None, old_index

        self._apply_executors(tree, ruleset)

        if self.look_ahead:
            index = old_index

        if self.alt_name != "":
            tree.name = self.alt_name

        # TODO: Maybe 'index' should be 'index + length'?
        if ruleset.farthest_match_index < index:
            ruleset.farthest_match_index = index

        return tree, index
    
    def _initializers_to_arg_str(self) -> str:
        args = []
        args.append(f"inverted={self.inverted}")
        args.append(f"quantifier=\"{self.quantifier}\"")
        args.append(f"look_ahead={self.look_ahead}")
        args.append(f"omit_match={self.omit_match}")
        args.append(f"alt_name=\"{escape_string(self.alt_name)}\"")
        args.append(f"executors={self._executors_to_arg_str()}")
        return f"initializers=RuleOptionInitializers({', '.join(args)})"

    def _executors_to_arg_str(self) -> str:
        executors = []
        for (operator, operand) in self.executors:
            executors.append(f"(\"{escape_string(operator)}\", \"{escape_string(operand)}\")")
        return f"[ {', '.join(executors)} ]"

    def _apply_optional_invert(self, string: str, index_old: int, index_new: int, tree: ParseTree) -> tuple[ParseTree, int]:
        if not self.inverted:
            return tree, index_new
        
        if tree is None:
            return ParseTreeExactMatch(string[index_old], *index_to_line_and_column(string, index_old)), index_old+1
        
        return None, index_old

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

    def _has_modifiers(self) -> bool:
        if self.inverted:
            return True
        if self.quantifier:
            return True
        if self.look_ahead:
            return True
        if self.omit_match:
            return True
        if self.alt_name:
            return True
        return False

    def _modifiers_to_str(self) -> str:
        mod_str = ""

        if self.inverted:
            mod_str += "!"

        mod_str += self.quantifier

        if self.look_ahead:
            mod_str += "~"

        if self.omit_match:
            mod_str += "_"

        if self.alt_name:
            mod_str += f"@{self.alt_name}"

        return mod_str

    def _executors_to_str(self) -> str:
        if len(self.executors) == 0:
            return ""

        exec_str = "{"
        for operator, operand in self.executors:
            exec_str += f"{operator} {operand},"
        exec_str = exec_str[:-1]
        exec_str += "}"

        return exec_str

    def __str__(self) -> str:
        return self._to_string() + self._modifiers_to_str() + self._executors_to_str()

    @abstractmethod
    def _match_specific(self, string: str, index: int, ruleset: "RuleSet") -> tuple[ParseTree, int]:
        raise NotImplementedError("RuleOption._match() must be implemented by subclasses")
   
    @abstractmethod
    def _to_string(self) -> str:
        raise NotImplementedError("RuleOption.__to_string() must be implemented by subclasses")

    @abstractmethod
    def _generate_python_code(self) -> str:
        raise NotImplementedError("RuleOption._generate_python_code() must be implemented by subclasses")

class RuleSet:
    def __init__(self, rules: dict[str, "Rule"] = {}, stack_names: set[str] = {}) -> None:
        self.rules = dict(rules)
        self.stacks = dict(map(lambda name : (name, []), stack_names))
        self.stack_histories = dict(map(lambda name : (name, []), stack_names))
        self.farthest_match_index = 0

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

    def reset(self) -> None:
        for stack in self.stacks.values():
            stack.clear()
        for history in self.stack_histories.values():
            history.clear()
        self.farthest_match_index = 0

    def stacks_are_empty(self) -> bool:
        for stack in self.stacks.values():
            if len(stack) > 0:
                return False
        return True

class RuleOptionList(RuleOption):
    def __init__(self, options: list[RuleOption] = [], *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.options: list[RuleOption] = list(options)

    def _generate_python_code_option_list(self) -> str:
        optionStrs = []
        for option in self.options:
            optionStrs.append(option._generate_python_code())
        return f"[ {', '.join(optionStrs)} ]"

# (...)
class RuleOptionMatchAll(RuleOptionList):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def _match_specific(self, string: str, index: int, ruleset: RuleSet) -> tuple[ParseTree, int]:
        old_index = index
        node = ParseTreeNode(*index_to_line_and_column(string, index))
        for option in self.options:
            child, index = option.match(string, index, ruleset)
            if child is None:
                return None, old_index
            node.add_child(child)

        return node, index
    
    def _to_string(self) -> str:
        result = " ".join([str(o) for o in self.options])
        if len(self.options) != 1 and self._has_modifiers():
            result = f"({result})"

        return result
    
    def _generate_python_code(self) -> str:
        return f"RuleOptionMatchAll({self._generate_python_code_option_list()}, {self._initializers_to_arg_str()})"

# [...]
class RuleOptionMatchAny(RuleOptionList):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def _match_specific(self, string: str, index: int, ruleset: RuleSet) -> tuple[ParseTree, int]:
        for option in self.options:
            node, index = option.match(string, index, ruleset)
            if node is not None:
                return node, index
        return None, index
    
    def _to_string(self) -> str:
        result = " ".join([str(o) for o in self.options])
        if len(self.options) != 1:
            result = f"[{result}]"

        return result
    
    def _generate_python_code(self) -> str:
        return f"RuleOptionMatchAny({self._generate_python_code_option_list()}, {self._initializers_to_arg_str()})"

# 'xx'
class RuleOptionMatchRange(RuleOption):
    def __init__(self, first: str, last: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.first = first
        self.last = last
    
    def _match_specific(self, string: str, index: int, ruleset: RuleSet) -> tuple[ParseTree, int]:
        if index >= len(string) or string[index] < self.first or string[index] > self.last:
            return None, index

        return ParseTreeExactMatch(string[index], *index_to_line_and_column(string, index)), index+1
    
    def _to_string(self) -> str:
        return f"'{self.first}{self.last}'"

    def _generate_python_code(self) -> str:
        return f"RuleOptionMatchRange(\"{escape_string(self.first)}\", \"{escape_string(self.last)}\", {self._initializers_to_arg_str()})"

# "..."
class RuleOptionMatchExact(RuleOption):
    def __init__(self, value: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.value = value

    def _match_specific(self, string: str, index: int, ruleset: RuleSet) -> tuple[ParseTree, int]:
        if string.startswith(self.value, index):
            return ParseTreeExactMatch(self.value, *index_to_line_and_column(string, index)), index+len(self.value)

        return None, index
    
    def _to_string(self) -> str:
        return f"\"{escape_string(self.value)}\""
    
    def _generate_python_code(self) -> str:
        return f"RuleOptionMatchExact(\"{escape_string(self.value)}\", {self._initializers_to_arg_str()})"

class RuleOptionMatchRule(RuleOption):
    def __init__(self, rulename: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.rulename = rulename

    def _match_specific(self, string: str, index: int, ruleset: RuleSet) -> tuple[ParseTree, int]:
        if self.rulename not in ruleset.rules:
            raise GrammarException(f"Rule '{self.rulename}' not found")
        rule = ruleset.rules[self.rulename]
        tree, index = rule.match(string, index, ruleset)
        if isinstance(tree, ParseTreeNode) and not rule.anonymous:
            tree.name = self.rulename
        return tree, index
    
    def _to_string(self) -> str:
        return self.rulename
    
    def _generate_python_code(self) -> str:
        return f"RuleOptionMatchRule(\"{escape_string(self.rulename)}\", {self._initializers_to_arg_str()})"

class RuleOptionStackMatchExact(RuleOption):
    def __init__(self, name: str, index: int, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.name = name
        self.index = index

    def _match_specific(self, string: str, index: int, ruleset: RuleSet) -> tuple[ParseTree, int]:
        if not self.name in ruleset.stacks:
            raise GrammarException(f"Stack '{self.name}' not found")
        
        stack = ruleset.stacks[self.name]
        if self.index >= len(stack):
            to_match = ""
        else:
            to_match = ruleset.stacks[self.name][-self.index-1]

        if string.startswith(to_match, index):
            return ParseTreeExactMatch(to_match, *index_to_line_and_column(string, index)), index+len(to_match)

        return None, index
    
    def _to_string(self) -> str:
        return f":{escape_string(self.name)}.{self.index}:"

    def _generate_python_code(self) -> str:
        return f"RuleOptionStackMatchExact(\"{escape_string(self.name)}\", {self.index}, {self._initializers_to_arg_str()})"

class Rule(RuleOptionMatchAny):
    def __init__(self, name=None, anonymous=False, fuse_children=False, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.name = name
        self.anonymous = anonymous
        self.fuse_children = fuse_children

    def match(self, string: str, index: int, ruleset: RuleSet) -> tuple[ParseTree, int]:
        tree, index = super().match(string, index, ruleset)
        if self.fuse_children:
            self.__fuse_children(tree)
        return tree, index
    
    def _generate_python_code(self) -> str:
        args = []
        args.append(f"name=\"{escape_string(self.name)}\"")
        args.append(f"anonymous={self.anonymous}")
        args.append(f"fuse_children={self.fuse_children}")
        args.append(f"options={self._generate_python_code_option_list()}")
        return f"Rule({', '.join(args)}, {self._initializers_to_arg_str()})"

    def __fuse_children(self, tree: ParseTree) -> None:
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

    def __str__(self) -> str:
        modifiers = []
        if self.anonymous:
            modifiers.append("hidden")
        if self.fuse_children:
            modifiers.append("fuse")
        
        name = self.name
        if len(modifiers) > 0:
            name += "(" + " ".join(modifiers) + ")"

        return f"{name}: {super().__str__()}"