#include "Position.h"

namespace qrawlr {
    std::string Position::to_string(std::function<std::string(int)> tree_id_to_name) const
    {
        std::string name = tree_id_to_name ? (tree_id_to_name(tree_id) + ":") : "";
        return name + std::to_string(line) + ":" + std::to_string(column);
    }
} // namespace qrawlr