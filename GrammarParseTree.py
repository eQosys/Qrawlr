import graphviz
import itertools
from abc import ABC, abstractmethod

from GrammarTools import escape_string

class ParseTree(ABC):
    __id_iter = itertools.count()

    def __init__(self) -> None:
        self.id = next(ParseTree.__id_iter)
        self.length = 0

    def to_digraph(self) -> graphviz.Digraph:
        dot = graphviz.Digraph()
        dot.graph_attr["rankdir"] = "LR"
        self._to_digraph(dot)
        return dot

    @abstractmethod
    def _to_digraph(self, dot: graphviz.Digraph) -> str:
        raise NotImplementedError("ParseTree.__to_digraph() must be implemented by subclasses")

class ParseTreeNode(ParseTree):
    def __init__(self) -> None:
        super().__init__()
        self.name: str = None
        self.children: list[ParseTree] = []

    def add_child(self, child: "ParseTree", omit_match: bool = False) -> None:
        if not omit_match:
            if isinstance(child, ParseTreeNode) and child.name is None:
                self.children.extend(child.children)
            else:
                self.children.append(child)
        self.length += child.length

    def _to_digraph(self, dot: graphviz.Digraph) -> str:
        dot.node(str(self.id), f"{self.name}:{self.id}")
        for child in self.children:
            child._to_digraph(dot)
            dot.edge(str(self.id), str(child.id))

    def __str__(self) -> str:
        return "".join([str(c) for c in self.children])

class ParseTreeExactMatch(ParseTree):
    def __init__(self, value: str) -> None:
        super().__init__()
        self.value = value
        self.length = len(value)

    def _to_digraph(self, dot: graphviz.Digraph) -> str:
        dot.node(str(self.id), f"\"{escape_string(self.value, True)}\":{self.id}")

    def __str__(self) -> str:
        return f"{self.value}"