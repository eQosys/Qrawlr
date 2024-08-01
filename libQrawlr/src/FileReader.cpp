#include "FileReader.h"

#include <fstream>

#include "GrammarException.h"

namespace qrawlr
{
    std::string read_file(const std::string& filename)
    {
        std::fstream file(filename, std::ios::in);
        if (!file.is_open())
            throw GrammarException("Failed to open file '" + filename + "'");

        std::string text, line;
        while (std::getline(file, line))
            text += line + "\n";

        return text;
    }
}; // namespace qrawlr