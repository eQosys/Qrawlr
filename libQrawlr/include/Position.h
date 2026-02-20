#pragma once

#include <string>
#include <functional>

namespace qrawlr
{
    struct Position
    {
        int tree_id = -1;
        int index = -1;
        int line = -1;
        int column = -1;

        std::string to_string() const;
    };
} // namespace qrawlr