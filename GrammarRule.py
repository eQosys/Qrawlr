import copy
import bisect
from abc import ABC, abstractmethod

from GrammarParseTree import *
from GrammarException import GrammarException

QUANTIFIER_ZERO_OR_ONE = "?"
QUANTIFIER_ZERO_OR_MORE = "*"
QUANTIFIER_ONE_OR_MORE = "+"
QUANTIFIER_SPECIFY_RANGE = "#"
QUANTIFIER_SPECIFY_LOWER_BOUND = ">"
QUANTIFIER_SPECIFY_UPPER_BOUND = "<"

MATCH_REPL_IDENTIFIER = 0
MATCH_REPL_STRING = 1
MATCH_REPL_STACK = 2

ACTION_ARG_TYPE_STRING = 0
ACTION_ARG_TYPE_MATCH = 1
ACTION_ARG_TYPE_IDENTIFIER = 2

TRIGGER_ON_MATCH = "onMatch"
TRIGGER_ON_FAIL = "onFail"
ACTION_TRIGGERS = [ TRIGGER_ON_MATCH, TRIGGER_ON_FAIL ]

class ParseData:
    def __init__(self, text: str, filename: str, rules: dict["Rule"]) -> None:
        self.__text = text
        self.__filename = filename
        self.__rules = rules
        self.__stacks = {}
        self.__stack_histories = {}
        self.farthest_match_index = -1

        self.__length = len(text)

        self.__gen_newline_cache()

    def has_rule(self, name: str) -> bool:
        return name in self.__rules

    def get_rule(self, name: str) -> "Rule":
        return self.__rules[name]

    def get_stack_names(self) -> list[str]:
        return list(self.__stacks.keys())

    def get_stack(self, name: str) -> list[str]:
        if name not in self.__stacks:
            self.__stacks[name] = []
            self.__stack_histories[name] = []

        return self.__stacks[name]

    def get_stack_history(self, name: str) -> list[tuple[str, str]]:
        if name not in self.__stacks:
            self.__stacks[name] = []
            self.__stack_histories[name] = []

        return self.__stack_histories[name]

    def eof(self, index: int) -> bool:
        return index >= self.__length

    def get_checkpoint(self) -> dict[str, int]:
        return dict(map(lambda name : (name, len(self.__stack_histories[name])), self.__stack_histories.keys()))
    
    def restore_checkpoint(self, checkpoint: dict[str, int]) -> None:
        for name, index in checkpoint.items():
            stack = self.__stacks[name]
            history = self.__stack_histories[name]
            while len(history) > index:
                operator, value = history.pop()
                if operator == "push":
                    stack.pop()
                elif operator == "pop":
                    stack.append(value)
                else:
                    raise GrammarException(f"Unknown action operator '{operator}'")

    def get_position(self, index: int) -> Position:
        line = bisect.bisect_left(self.__newline_cache, index)
        column = index - self.__newline_cache[line - 1]
        return Position(index, line, column)
    
    def get_position_string(self, index: int) -> str:
        pos = self.get_position(index)
        return f"{self.__filename}:{pos.line}:{pos.column}"
    
    def stacks_are_empty(self) -> bool:
        for stack in self.__stacks.values():
            if len(stack) > 0:
                return False
        return True

    def __gen_newline_cache(self) -> None:
        self.__newline_cache = [ -1 ]
        for i in range(len(self.__text)):
            if self.__text[i] == "\n":
                self.__newline_cache.append(i)

    # STRING ACCESS

    def startswith(self, value: str, start = None, end = None) -> bool:
        return self.__text.startswith(value, start, end)
    
    def endswith(self, value: str, start = None, end = None) -> bool:
        return self.__text.endswith(value, start, end)

    def __getitem__(self, key) -> str:
        return self.__text[key]

class MatcherInitializers:
    def __init__(self, inverted: bool = False, count_min: int = 1, count_max: int = 1, look_ahead: bool = False, omit_match: bool = False, match_repl: (int, str) = None, actions: dict[str, list[tuple[str, list[tuple[int, None]]]]] = {}) -> None:
        self.inverted      = inverted
        self.count_min     = count_min
        self.count_max     = count_max
        self.look_ahead    = look_ahead
        self.omit_match    = omit_match
        self.match_repl    = match_repl
        self.actions       = actions

class Matcher(ABC):
    def __init__(self, initializers: MatcherInitializers = MatcherInitializers()) -> None:
        self.inverted      = initializers.inverted
        self.count_min     = initializers.count_min
        self.count_max     = initializers.count_max
        self.look_ahead    = initializers.look_ahead
        self.omit_match    = initializers.omit_match
        self.match_repl    = initializers.match_repl
        self.actions       = copy.deepcopy(initializers.actions)

    def match(self, parseData: ParseData, index: int) -> tuple[ParseTree, int]:
        old_index = index
        match_count = 0
        checkpoint = parseData.get_checkpoint()

        tree = ParseTreeNode(parseData.get_position(index))
        while True:
            sub_tree, sub_index = self._match_specific(parseData, index)
            sub_tree, sub_index = self._apply_optional_invert(parseData, index, sub_index, sub_tree)

            index = sub_index

            if sub_tree is None:
                break
            match_count += 1

            tree.add_child(sub_tree, self.omit_match)

            if match_count == self.count_max:
                break
        
        if match_count < self.count_min:
            # TODO: Maybe 'index' should be 'old_index'?
            self._run_actions_for_trigger(TRIGGER_ON_FAIL, None, parseData, old_index)
            parseData.restore_checkpoint(checkpoint)
            return None, old_index

        # TODO: Maybe 'index' should be 'index + length'?
        if parseData.farthest_match_index < index:
            parseData.farthest_match_index = index

        if self.look_ahead:
            index = old_index

        # TODO: Maybe 'index' should be 'old_index'?
        self._run_actions_for_trigger(TRIGGER_ON_MATCH, tree, parseData, old_index)

        tree = self._apply_match_replacement(tree, parseData, index)

        return tree, index
    
    def _initializers_to_arg_str(self) -> str:
        args = []
        args.append(f"inverted={self.inverted}")
        args.append(f"count_min={self.count_min}")
        args.append(f"count_max={self.count_max}")
        args.append(f"look_ahead={self.look_ahead}")
        args.append(f"omit_match={self.omit_match}")
        args.append(f"match_repl={self.match_repl}")
        args.append(f"actions={self._actions_to_arg_str()}")
        return f"initializers=MatcherInitializers({', '.join(args)})"

    def _actions_to_arg_str(self) -> str:
        triggers = []
        for (trigger_name, action_list) in self.actions.items():
            triggers.append(f"\"{escape_string(trigger_name)}\": {self._action_list_to_arg_str(action_list)}")
        return f"{{{', '.join(triggers)}}}"
    
    def _action_list_to_arg_str(self, action_list: list[tuple[str, list[tuple[int, None]]]]) -> str:
        actions = []
        for (action_name, args) in action_list:
            actions.append(f"(\"{escape_string(action_name)}\", {self._action_args_to_arg_str(args)})")
        return f"[{', '.join(actions)}]"
    
    def _action_args_to_arg_str(self, action_args: list[tuple[int, None]]) -> str:
        args = []
        for (type_id, value) in action_args:
            args.append(f"({type_id}, \"{value}\")")
        return f"[{', '.join(args)}]"

    def _apply_optional_invert(self, parseData: ParseData, index_old: int, index_new: int, tree: ParseTree) -> tuple[ParseTree, int]:
        if not self.inverted:
            return tree, index_new
        
        next_index = index_old + 1
        
        if tree is None and not parseData.eof(index_old):
            return ParseTreeExactMatch(parseData[index_old], parseData.get_position(index_old), parseData.get_position(next_index)), next_index
        
        return None, index_old

    def _run_actions_for_trigger(self, trigger_name: str, tree: ParseTreeNode, parseData: ParseData, index: int) -> None:
        trigger = self.actions.get(trigger_name, [])
        for (action_name, args) in trigger:
            args = list(map(lambda arg : arg if arg[0] != ACTION_ARG_TYPE_MATCH else (ACTION_ARG_TYPE_STRING, str(tree)), args))
            
            if action_name == "push":
                self._run_action_push(tree, args, parseData, index)
            elif action_name == "pop":
                self._run_action_pop(tree, args, parseData, index)
            elif action_name == "message":
                self._run_action_message(tree, args, parseData, index)
            elif action_name == "fail":
                self._run_action_fail(tree, args, parseData, index)
            else:
                raise GrammarException(f"Unknown action '{action_name}'")

    def _run_action_push(self, tree: ParseTreeNode, args: list[tuple[int, None]], parseData: ParseData, index: int) -> None:
        if len(args) != 2:
            raise GrammarException("Wrong number of arguments for action 'push'")
        
        arg_item = args[0]
        arg_stack = args[1]

        if arg_stack[0] != ACTION_ARG_TYPE_IDENTIFIER:
            raise GrammarException("Expected identifier for action argument 'stack'")
        
        stack_name = arg_stack[1]

        if arg_item[0] == ACTION_ARG_TYPE_STRING:
            value = arg_item[1]
        elif arg_item[0] == ACTION_ARG_TYPE_IDENTIFIER:
            raise GrammarException("Identifier not allowed for action argument 'item'")
        else:
            raise GrammarException("Unknown action argument type for 'item'")
        
        stack = parseData.get_stack(stack_name)
        history = parseData.get_stack_history(stack_name)

        stack.append(value)
        history.append(("push", value))

    def _run_action_pop(self, tree: ParseTreeNode, args: list[tuple[int, None]], parseData: ParseData, index: int) -> None:
        if len(args) != 1:
            raise GrammarException("Wrong number of arguments for action 'pop'")
        
        arg_stack = args[0]

        if arg_stack[0] != ACTION_ARG_TYPE_IDENTIFIER:
            raise GrammarException("Expected identifier for action argument 'stack'")
        
        stack_name = arg_stack[1]

        stack = parseData.get_stack(stack_name)
        history = parseData.get_stack_history(stack_name)

        if len(stack) == 0:
            raise GrammarException(f"Cannot pop from empty stack '{stack_name}'")

        value = stack.pop()
        history.append(("pop", value))

    def _run_action_message(self, tree: ParseTreeNode, args: list[tuple[int, None]], parseData: ParseData, index: int) -> None:
        if len(args) != 1:
            raise GrammarException("Wrong number of arguments for action 'message'")
        
        arg_message = args[0]

        if arg_message[0] != ACTION_ARG_TYPE_STRING:
            raise GrammarException("Expected string for action argument 'message'")
        
        message = arg_message[1]

        print(f"MSG: {parseData.get_position_string(index)}: {message}")

    def _run_action_fail(self, tree: ParseTreeNode, args: list[tuple[int, None]], parseData: ParseData, index: int) -> None:
        if len(args) != 1:
            raise GrammarException("Wrong number of arguments for action 'fail'")
        
        arg_message = args[0]

        if arg_message[0] != ACTION_ARG_TYPE_STRING:
            raise GrammarException("Expected string for action argument 'message'")
        
        message = arg_message[1]

        raise GrammarException(f"FAIL: {parseData.get_position_string(index)}: {message}")

    def _apply_match_replacement(self, tree: ParseTree, parseData: ParseData, index: int) -> ParseTree:
        if self.match_repl is not None:
            repl_type, repl = self.match_repl

            if repl_type == MATCH_REPL_STRING:
                tree = ParseTreeExactMatch(repl, parseData.get_position(index))

            elif repl_type == MATCH_REPL_STACK:
                stack_name, stack_index = repl.split(".")
                stack_index = int(stack_index)
                
                stack = parseData.get_stack(stack_name)
                
                if stack_index < len(stack):
                    value = stack[-stack_index-1]
                else:
                    value = ""

                tree = ParseTreeExactMatch(value, parseData.get_position(index))

            elif repl_type == MATCH_REPL_IDENTIFIER:
                tree.name = repl

            else:
                raise GrammarException(f"Unknown match replacement type '{repl_type}'")
            
        return tree

    def _has_modifiers(self) -> bool:
        if self.inverted:
            return True
        if self.count_min != 1 or self.count_max != 1:
            return True
        if self.look_ahead:
            return True
        if self.omit_match:
            return True
        if self.match_repl:
            return True
        return False

    def _count_range_to_str(self) -> str:
        match (self.count_min, self.count_max):
            case (0, 1):
                return QUANTIFIER_ZERO_OR_ONE
            case (0, -1):
                return QUANTIFIER_ZERO_OR_MORE
            case (1, 1):
                return ""
            case (1, -1):
                return QUANTIFIER_ONE_OR_MORE
            case (minimum, maximum):
                result = QUANTIFIER_SPECIFY_RANGE
                if minimum == 0:
                    result += f"{QUANTIFIER_SPECIFY_UPPER_BOUND}{maximum+1}"
                elif maximum == -1:
                    result += f"{QUANTIFIER_SPECIFY_LOWER_BOUND}{minimum-1}"
                else:
                    result += f"{minimum}-{maximum}"
                return result

    def _modifiers_to_str(self) -> str:
        mod_str = ""

        if self.inverted:
            mod_str += "!"

        mod_str += self._count_range_to_str()

        if self.look_ahead:
            mod_str += "~"

        if self.omit_match:
            mod_str += "_"

        if self.match_repl is not None:
            mod_str += "->"
            repl_type, repl = self.match_repl
            if repl_type == MATCH_REPL_STRING:
                mod_str += f"\"{escape_string(repl)}\""
            elif repl_type == MATCH_REPL_STACK:
                mod_str += f":{escape_string(repl)}:"
            elif repl_type == MATCH_REPL_IDENTIFIER:
                mod_str += repl
            else:
                raise GrammarException(f"Unknown match replacement type '{repl_type}'")

        return mod_str

    def _actions_to_str(self) -> str:
        if len(self.actions) == 0:
            return ""
        
        triggers = []

        for trigger_name, action_list in self.actions.items():
            triggers.append(f"{trigger_name}: {self._action_list_to_str(action_list)}")

        return f"{{{', '.join(triggers)}}}"
    
    def _action_list_to_str(self, action_list: list[tuple[str, list[tuple[str, None]]]]) -> str:
        actions = []

        for (action_name, args) in action_list:
            actions.append(f"{action_name}({self._action_args_to_str(args)})")

        return f"[{', '.join(actions)}]"
    
    def _action_args_to_str(self, action_args: list[tuple[str, None]]) -> str:
        args = []

        for (type_id, value) in action_args:
            if type_id == ACTION_ARG_TYPE_STRING:
                args.append(f"\"{escape_string(value)}\"")
            elif type_id == ACTION_ARG_TYPE_MATCH:
                args.append("_")
            elif type_id == ACTION_ARG_TYPE_IDENTIFIER:
                args.append(value)
            else:
                raise GrammarException(f"Unknown action argument type '{type_id}'")

        return f"{', '.join(args)}"

    def __str__(self) -> str:
        return self._to_string() + self._modifiers_to_str() + self._actions_to_str()

    @abstractmethod
    def _match_specific(self, parseData: ParseData, index: int) -> tuple[ParseTree, int]:
        raise NotImplementedError("Matcher._match() must be implemented by subclasses")
   
    @abstractmethod
    def _to_string(self) -> str:
        raise NotImplementedError("Matcher.__to_string() must be implemented by subclasses")

    @abstractmethod
    def _generate_python_code(self) -> str:
        raise NotImplementedError("Matcher._generate_python_code() must be implemented by subclasses")

# .
class MatcherMatchAnyChar(Matcher):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def _match_specific(self, parseData: ParseData, index: int) -> tuple[ParseTree, int]:
        if parseData.eof(index):
            return None, index

        next_index = index + 1

        return ParseTreeExactMatch(parseData[index], parseData.get_position(index), parseData.get_position(next_index)), next_index

    def _to_string(self) -> str:
        return "."
    
    def _generate_python_code(self) -> str:
        return f"MatcherMatchAnyChar({self._initializers_to_arg_str()})"

class MatcherList(Matcher):
    def __init__(self, options: list[Matcher] = [], *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.options: list[Matcher] = list(options)

    def _generate_python_code_option_list(self) -> str:
        optionStrs = []
        for option in self.options:
            optionStrs.append(option._generate_python_code())
        return f"[{', '.join(optionStrs)}]"

# (...)
class MatcherMatchAll(MatcherList):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def _match_specific(self, parseData: ParseData, index: int) -> tuple[ParseTree, int]:
        old_index = index
        children = []
        for option in self.options:
            child, index = option.match(parseData, index)
            if child is None:
                return None, old_index
            children.append(child)

        node = ParseTreeNode(parseData.get_position(index))
        for child in children:
            node.add_child(child)

        return node, index
    
    def _to_string(self) -> str:
        result = " ".join([str(o) for o in self.options])
        if len(self.options) != 1 and self._has_modifiers():
            result = f"({result})"

        return result
    
    def _generate_python_code(self) -> str:
        return f"MatcherMatchAll({self._generate_python_code_option_list()}, {self._initializers_to_arg_str()})"

# [...]
class MatcherMatchAny(MatcherList):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def _match_specific(self, parseData: ParseData, index: int) -> tuple[ParseTree, int]:
        for option in self.options:
            node, new_index = option.match(parseData, index)
            if node is not None:
                return node, new_index
        return None, index
    
    def _to_string(self) -> str:
        result = " ".join([str(o) for o in self.options])
        if len(self.options) != 1:
            result = f"[{result}]"

        return result
    
    def _generate_python_code(self) -> str:
        return f"MatcherMatchAny({self._generate_python_code_option_list()}, {self._initializers_to_arg_str()})"

# 'xx'
class MatcherMatchRange(Matcher):
    def __init__(self, first: str, last: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.first = first
        self.last = last
    
    def _match_specific(self, parseData: ParseData, index: int) -> tuple[ParseTree, int]:
        if parseData.eof(index):
            return None, index
        
        if parseData[index] < self.first or parseData[index] > self.last:
            return None, index

        next_index = index + 1

        return ParseTreeExactMatch(parseData[index], parseData.get_position(index), parseData.get_position(next_index)), next_index
    
    def _to_string(self) -> str:
        return f"'{self.first}{self.last}'"

    def _generate_python_code(self) -> str:
        return f"MatcherMatchRange(\"{escape_string(self.first)}\", \"{escape_string(self.last)}\", {self._initializers_to_arg_str()})"

# "..."
class MatcherMatchExact(Matcher):
    def __init__(self, value: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.value = value
        
    def _match_specific(self, parseData: ParseData, index: int) -> tuple[ParseTree, int]:
        if not parseData.startswith(self.value, index):
            return None, index

        next_index = index + len(self.value)

        return ParseTreeExactMatch(self.value, parseData.get_position(index), parseData.get_position(next_index)), next_index
    
    def _to_string(self) -> str:
        return f"\"{escape_string(self.value)}\""
    
    def _generate_python_code(self) -> str:
        return f"MatcherMatchExact(\"{escape_string(self.value)}\", {self._initializers_to_arg_str()})"

class MatcherMatchRule(Matcher):
    def __init__(self, rulename: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.rulename = rulename

    def _match_specific(self, parseData: ParseData, index: int) -> tuple[ParseTree, int]:
        if not parseData.has_rule(self.rulename):
            raise GrammarException(f"Rule '{self.rulename}' not found")
        rule = parseData.get_rule(self.rulename)
        tree, index = rule.match(parseData, index)
        if isinstance(tree, ParseTreeNode) and not rule.anonymous:
            tree.name = self.rulename
        return tree, index
    
    def _to_string(self) -> str:
        return self.rulename
    
    def _generate_python_code(self) -> str:
        return f"MatcherMatchRule(\"{escape_string(self.rulename)}\", {self._initializers_to_arg_str()})"

class MatcherMatchStack(Matcher):
    def __init__(self, name: str, index: int, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.stack_name = name
        self.index = index

    def _match_specific(self, parseData: ParseData, index: int) -> tuple[ParseTree, int]:
        stack = parseData.get_stack(self.stack_name)

        if self.index < len(stack):
            to_match = stack[-self.index-1]
        else:
            to_match = ""

        if parseData.startswith(to_match, index):
            last_index = index + len(to_match)
            return ParseTreeExactMatch(to_match, parseData.get_position(index), parseData.get_position(last_index)), last_index

        return None, index
    
    def _to_string(self) -> str:
        return f":{escape_string(self.stack_name)}.{self.index}:"

    def _generate_python_code(self) -> str:
        return f"MatcherMatchStack(\"{escape_string(self.stack_name)}\", {self.index}, {self._initializers_to_arg_str()})"

class Rule(MatcherMatchAny):
    def __init__(self, name=None, anonymous=False, fuse_children=False, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.name = name
        self.anonymous = anonymous
        self.fuse_children = fuse_children

    def match(self, parseData: ParseData, index: int) -> tuple[ParseTree, int]:
        tree, index = super().match(parseData, index)
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
                    if tree.children[leafID].position_end.index < tree.children[i].position_end.index:
                        tree.children[leafID].position_end = tree.children[i].position_end
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