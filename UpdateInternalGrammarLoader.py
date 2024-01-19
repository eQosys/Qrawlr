from GrammarException import GrammarException
from GrammarLoader import GrammarLoader

OUTPUT_PATH = "InternalGrammarLoader.py"
GRAMMAR_PATH = "grammars/qrawlr_grammar.qgr"

def update_internal_grammar_loader():
    # Load old grammar
    print("INFO: Loading old grammar...")
    old_grammar = GrammarLoader(path = GRAMMAR_PATH).get_grammar()

    # Load text of new grammar
    print("INFO: Loading new grammar text...")
    with open(GRAMMAR_PATH, "r") as f:
        new_grammar_text = f.read()

    # Parse new grammar with old grammar
    print("INFO: Parsing new grammar...")
    result = old_grammar.apply_to(new_grammar_text, "Grammar", GRAMMAR_PATH)
    tree = result.tree
    max_pos = result.farthest_match_position

    if tree is None or tree.position_end.index < len(new_grammar_text):
        raise GrammarException("Unknown error while parsing new grammar", GRAMMAR_PATH, max_pos)

    # Generate new grammar implementation
    print("INFO: Generating new grammar implementation...")
    new_grammar = GrammarLoader(init_tree = tree).get_grammar()

    # TODO: Add tests for new grammar implementation
    print("TODO: Here should we run some tests...")

    # Generate new grammar loader
    print("INFO: Generating new grammar loader...")
    new_code = new_grammar.generate_python_code("load_internal_grammar", True)
    
    # Save new grammar loader
    print("INFO: Saving new grammar loader...")
    with open(OUTPUT_PATH, "w") as f:
        f.write(new_code)

    print("INFO: Done!")

if __name__ == "__main__":
    print("This script will replace the content of './InternalGrammarLoader.py' with a new implementation.")
    print("This step is necessary after modifying 'grammars/qrawlr_grammar.qgr' and not irreversible.")
    print("Do you want to continue? [y/N] ", end="", flush=True)
    if input().lower() != "y":
        print("Aborting...")
        exit()

    try:
        update_internal_grammar_loader()
    except GrammarException as e:
        print(f"ERROR: {e}")
        exit(1)