#include "FileWriter.h"

#include <fstream>
#include <stdexcept>

namespace qrawlr
{
    void write_file(const std::string& filename, const std::string& content)
    {
        std::ofstream file(filename);
        if (!file.is_open())
            throw std::runtime_error("Failed to open file for writing: " + filename);
        file << content;
    }
} // namespace qrawlr