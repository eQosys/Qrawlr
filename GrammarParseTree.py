import graphviz
import itertools
from abc import ABC, abstractmethod
from GrammarTools import escape_string

class ParseTree(ABC):
    __id_iter = itertools.count()

    def __init__(self, position: tuple[int, int], length: int = 0) -> None:
        self.id = next(ParseTree.__id_iter)
        self.position = position
        self.length = length

    def to_digraph(self, verbose: bool = True) -> graphviz.Digraph:
        dot = graphviz.Digraph()
        dot.graph_attr["rankdir"] = "LR"
        self._to_digraph(dot, verbose)
        return dot

    def _add_optional_verbose_info(self, text: str, verbose: bool) -> str:
        if verbose:
            text += f"\\n{self.position[0]}:{self.position[1]}"

        return text

    @abstractmethod
    def _to_digraph(self, dot: graphviz.Digraph, verbose) -> str:
        raise NotImplementedError("ParseTree.__to_digraph() must be implemented by subclasses")

class ParseTreeNode(ParseTree):
    def __init__(self, position: tuple[int, int]) -> None:
        super().__init__(position)
        self.name: str = None
        self.children: list[ParseTree] = []

    def add_child(self, child: "ParseTree", omit_match: bool = False) -> None:
        if not omit_match:
            if isinstance(child, ParseTreeNode) and child.name is None:
                self.children.extend(child.children)
            else:
                self.children.append(child)
        self.length += child.length

    def _to_digraph(self, dot: graphviz.Digraph, verbose) -> str:
        text = f"{self.name}"
        text = self._add_optional_verbose_info(text, verbose)
        dot.node(str(self.id), text, shape="ellipse")

        for child in self.children:
            child._to_digraph(dot, verbose)
            dot.edge(str(self.id), str(child.id))

    def __str__(self) -> str:
        return "".join([str(c) for c in self.children])

class ParseTreeExactMatch(ParseTree):
    def __init__(self, value: str, position: tuple[int, int], length_override: int = None) -> None:
        super().__init__(position, len(value) if length_override is None else length_override)
        self.value = value

    def _to_digraph(self, dot: graphviz.Digraph, verbose) -> str:
        text = f"\"{escape_string(self.value)}\""
        text = self._add_optional_verbose_info(text, verbose)
        dot.node(str(self.id), text, shape="plaintext")

    def __str__(self) -> str:
        return f"{self.value}"