import json
from Grammar import Grammar, GrammarException
from GrammarTools import index_to_line_and_column
from GrammarParseTree import ParseTree, ParseTreeNode, ParseTreeExactMatch

def load_dynamic_grammar():
    raise GrammarException("this_is_a_test_code_name should have been replaced by code generation")

def write_tree_graphviz(tree: ParseTree, verbose):
    print("INFO: Writing tree to tree.gv... ", end="", flush=True)
    with open("tree.gv", "w") as f:
        f.write(tree.to_digraph(verbose).source)
    print("DONE")

def render_tree(tree: ParseTree, verbose):
    print("INFO: Rendering tree to tree.pdf... ", end="", flush=True)
    tree.to_digraph(verbose).render(format="pdf", outfile="tree.pdf")
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

def run_test(grammarfile: str, entry_rule: str, text: str, filename: str = None, verbose: bool = True):
    g = Grammar(grammarfile)

    tree = g.apply_to(text, entry_rule)
    
    if tree is None or tree.length < len(text):
        print(f"Max index: {g.ruleset.farthest_match_index}", end="" if filename else "\n")
        if filename:
            line, col = index_to_line_and_column(text, g.ruleset.farthest_match_index)
            print(f" -> {filename}:{line}:{col}")
        print(f"Remaining text: {repr(text[g.ruleset.farthest_match_index:][:32])}")
        print("WARN: Text was not fully parsed")

        if tree is None:
            raise GrammarException("Could not parse text")
    else:
        print("INFO: Fully parsed text")

    write_tree_graphviz(tree, verbose)
    render_tree(tree, verbose)

    return tree

def test_algebra():
    expression = "-533+(256-79+105)-703+79-603+(87*(475))/(744)+274-((524/162*42-504*638))/(163*814-(((885)+451)-573+408-(649+267+((582-464))+688+590+524)*594+706))-881-728-133"

    tree = run_test("grammars/algebra_grammar.txt", "Expression", expression, verbose = False)

    result = evaluate_expression(tree)

    print(f"INFO: {expression} = {result}")

def test_grammar():
    filename = "grammars/grammar_grammar.txt"
    with open(filename, "r") as f:
        text = f.read()

    run_test("grammars/grammar_grammar.txt", "Grammar", text, filename, verbose = True)

def test_qism():
    filename = "test_files/bootloader.qsm"
    with open(filename, "r") as f:
        text = f.read()

    run_test("grammars/qism_grammar.txt", "Code", text, filename)

def test_qinp():
    filename = "test_files/push_pop_test.qnp"
    with open(filename, "r") as f:
        text = f.read()

    run_test("grammars/qinp_grammar.txt", "GlobalCode", text, filename, verbose = True)

def test_integer_list():
    text = "0 1 2 3 12 0x12 054 00"

    run_test("grammars/integer_list_grammar.txt", "IntegerList", text, verbose = True)

def test_code_generation():
    g = Grammar("grammars/grammar_grammar.txt")
    pre_str = str(g)

    exec(g.generate_python_code("load_dynamic_grammar"), globals())
    g = load_dynamic_grammar()
    post_str = str(g)

    if pre_str != post_str:
        print("ERROR: Grammar strings do not match")
        print("Pre:")
        print(" ", pre_str.replace("\n", "\n  "))
        print("Post:")
        print(" ", post_str.replace("\n", "\n  "))
    else:
        print("INFO: Grammar strings match")

if __name__ == "__main__":
    try:
        #test_algebra()
        #test_qism()
        test_grammar()
        #test_qinp()
        #test_integer_list()
        #test_code_generation()
    except GrammarException as e:
        print(f"Error: {e}")