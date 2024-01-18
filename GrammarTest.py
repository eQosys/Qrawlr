import os
import json
from Grammar import Grammar, GrammarException
from GrammarParseTree import ParseTree, ParseTreeNode, ParseTreeExactMatch

def load_dynamic_grammar():
    raise GrammarException("load_dynamic_grammar should have been replaced by code generation")

def make_output_dir():
    os.makedirs("output", exist_ok = True)

def path_to_name(path: str):
    return path.replace("/", "::")

def path_to_output_filename(path: str, extension: str):
    return os.path.join("output", path_to_name(path + extension))

def write_tree_graphviz(tree: ParseTree, filename: str, verbose: bool):
    print("  INFO: Writing tree to tree.gv... ", end="", flush=True)
    make_output_dir()
    with open(path_to_output_filename(filename, ".gv"), "w") as f:
        f.write(tree.to_digraph(verbose).source)
    print("DONE")

def render_tree(tree: ParseTree, filename: str, verbose: bool):
    print("  INFO: Rendering tree to tree.pdf... ", end="", flush=True)
    make_output_dir()
    tree.to_digraph(verbose).render(format="pdf", outfile=path_to_output_filename(filename, ".pdf"), cleanup=True)
    print("DONE")

def evaluate_expression(tree: ParseTree):
    if isinstance(tree, ParseTreeNode):
        if tree.name == "Expression":
            return evaluate_expression(tree.children[0])
        elif tree.name == "Sum":
            if isinstance(tree.children[0], ParseTreeExactMatch):
                sign = tree.children[0].value
                first_sub_id = 1
            else:
                sign = "+"
                first_sub_id = 0

            result = evaluate_expression(tree.children[first_sub_id])
            result = result if sign == "+" else -result

            for i in range(first_sub_id+1, len(tree.children), 2):
                part = evaluate_expression(tree.children[i+1])
                if tree.children[i].value == "+":
                    result += part
                elif tree.children[i].value == "-":
                    result -= part
                else:
                    raise GrammarException("Unknown operator", tree.children[i].value)
            return result
        elif tree.name == "Product":
            result = evaluate_expression(tree.children[0])
            for i in range(1, len(tree.children), 2):
                part = evaluate_expression(tree.children[i+1])
                if tree.children[i].value == "*":
                    result *= part
                elif tree.children[i].value == "/":
                    result //= part
                else:
                    raise GrammarException("Unknown operator", tree.children[i].value)
            return result
        elif tree.name == "Atom":
            return evaluate_expression(tree.children[0])
        elif tree.name == "Number":
            return evaluate_expression(tree.children[0])
        else:
            raise GrammarException("Unknown name", tree.name)
    elif isinstance(tree, ParseTreeExactMatch):
        return int(tree.value)
    else:
        raise GrammarException("Expected ParseTreeNode but got", type(tree))

def run_test(grammarfile: str, entry_rule: str, text: str, filename: str = None, verbose: bool = True, do_write_tree: bool = False, do_render_tree: bool = True):
    print(f"INFO: Testing {grammarfile} on {filename}")
    
    g = Grammar(grammarfile)

    result = g.apply_to(text, entry_rule, filename)
    
    tree = result.tree
    max_pos = result.farthes_match_position

    if tree is None or tree.position_end.index < len(text):
        print("  ERROR: Text was not fully parsed")
        print(f"    Max index: {max_pos.index}", end="" if filename else "\n")
        if filename:
            print(f" -> {filename}:{max_pos.line}:{max_pos.column}")
        print(f"    Remaining text: {repr(text[max_pos.index:][:32])}")

        if tree is None:
            raise GrammarException("Could not parse text")
    else:
        print("  INFO: Fully parsed text")

    if do_render_tree:
        render_tree(tree, filename, verbose)
    if do_write_tree:
        write_tree_graphviz(tree, filename, verbose)

    return tree

def test_algebra():
    filename = "test_files/algebra_expression.txt"
    with open(filename, "r") as f:
        expression = f.read().strip()

    tree = run_test("grammars/algebra_grammar.qgr", "Expression", expression, filename, verbose = False)

    result = evaluate_expression(tree)

    print(f"  INFO: result = {result}")
    print(f"        reference = {eval(expression.replace('/', '//'))}")

def test_grammar(self_only):
    grammar_path = "grammars/grammar_grammar.qgr"

    for filename in os.listdir("grammars"):
        if filename.endswith("algebra_grammar.qgr"): # TODO: Remove 'algebra_grammar' from string (for testing purposes only)
            path = os.path.join("grammars", filename)
            if self_only and path != grammar_path:
                continue

            with open(path, "r") as f:
                text = f.read()

            run_test(grammar_path, "Grammar", text, path, verbose = True, do_render_tree = True)

def test_qism():
    filename = "test_files/bootloader.qsm"
    with open(filename, "r") as f:
        text = f.read()

    run_test("grammars/qism_grammar.qgr", "Code", text, filename)

def test_qinp():
    filename = "test_files/push_pop_test.qnp"
    with open(filename, "r") as f:
        text = f.read()

    run_test("grammars/qinp_grammar.qgr", "GlobalCode", text, filename, verbose = True)

def test_code_generation():
    g = Grammar("grammars/qinp_grammar.qgr")
    pre_str = str(g)

    exec(g.generate_python_code("load_dynamic_grammar"), globals())
    g = load_dynamic_grammar()
    post_str = str(g)
    
    print("Pre:")
    print(" ", pre_str.replace("\n", "\n  "))
    print("Post:")
    print(" ", post_str.replace("\n", "\n  "))

    if pre_str != post_str:
        print("ERROR: Grammar strings do not match")
    else:
        print("INFO: Grammar strings match")

if __name__ == "__main__":
    try:
        #test_algebra()
        #test_qism()
        test_grammar(False)
        #test_qinp()
        #test_code_generation()
    except GrammarException as e:
        print(f"  ERROR: {e}")