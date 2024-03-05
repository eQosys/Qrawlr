#include "Grammar.h"

#include "GrammarException.h"
#include "FileReader.h"

namespace qrawlr
{
    Grammar::Grammar()
    {}

    Grammar::~Grammar()
    {}

    Grammar Grammar::load_from_file(const std::string& filename)
    {
        std::string text = read_file(filename);
        return load_from_text(text);
    }

    Grammar Grammar::load_from_text(const std::string& text)
    {
        (void)text; // Currently unused
        
        Grammar grammar;
        return grammar;
    }
}