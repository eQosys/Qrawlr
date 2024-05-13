#pragma once

#include <string>

namespace qrawlr
{
    struct Position
    {
        int index;
        int line;
        int column;

        std::string to_string(const std::string& path) const;
    };
} // namespace qrawlr