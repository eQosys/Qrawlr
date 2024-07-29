#pragma once

#include <string>
#include <functional>

namespace qrawlr
{
    struct Position
    {
        int tree_id;
        int index;
        int line;
        int column;

        std::string to_string() const;
        std::string to_string(std::function<std::string(int)> tree_id_to_name) const;
    };
} // namespace qrawlr