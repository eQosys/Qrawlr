import graphviz
import itertools
from abc import ABC, abstractmethod
from GrammarTools import Position, escape_string

class ParseTree(ABC):
    __id_iter = itertools.count()

    def __init__(self, position_begin: Position, position_end: Position = None) -> None:
        # TODO: Remove these checks
        if not isinstance(position_begin, Position):
            raise ValueError
        if not isinstance(position_end, Position) and position_end is not None:
            raise ValueError
        
        self.id = next(ParseTree.__id_iter)
        self.position_begin = position_begin
        self.position_end = position_begin if position_end is None else position_end

    def to_digraph(self, verbose: bool = True) -> graphviz.Digraph:
        dot = graphviz.Digraph()
        dot.graph_attr["rankdir"] = "LR"
        self._to_digraph(dot, verbose)
        return dot

    def _add_optional_verbose_info(self, text: str, verbose: bool) -> str:
        if verbose:
            text += f"\\n{self.position_begin.line}:{self.position_begin.column}"
            text += f" -> {self.position_end.line}:{self.position_end.column}"

        return text

    @abstractmethod
    def _to_digraph(self, dot: graphviz.Digraph, verbose) -> str:
        raise NotImplementedError("ParseTree.__to_digraph() must be implemented by subclasses")

class ParseTreeNode(ParseTree):
    def __init__(self, position_begin: Position) -> None:
        super().__init__(position_begin)
        self.name: str = None
        self.children: list[ParseTree] = []

    def add_child(self, child: "ParseTree", omit_match: bool = False) -> None:
        if not omit_match:
            if isinstance(child, ParseTreeNode) and child.name is None:
                self.children.extend(child.children)
            else:
                self.children.append(child)

        if self.position_end.index < child.position_end.index:
            self.position_end = child.position_end

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
    def __init__(self, value: str, position_begin: Position, position_end: Position) -> None:
        super().__init__(position_begin, position_end)
        self.value = value

    def _to_digraph(self, dot: graphviz.Digraph, verbose) -> str:
        text = f"\"{escape_string(self.value)}\""
        text = self._add_optional_verbose_info(text, verbose)
        dot.node(str(self.id), text, shape="plaintext")

    def __str__(self) -> str:
        return f"{self.value}"