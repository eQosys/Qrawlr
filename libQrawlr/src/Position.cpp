#include "Position.h"

namespace qrawlr {
    std::string Position::to_string() const
    {
        return std::to_string(line) + ":" + std::to_string(column);
    }

    std::string Position::to_string(std::function<std::string(int)> tree_id_to_name) const
    {
        return tree_id_to_name(tree_id) + ":" + to_string();
    }
} // namespace qrawlr