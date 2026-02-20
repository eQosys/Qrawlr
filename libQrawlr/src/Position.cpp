#include "Position.h"

#include "ParseData.h"

namespace qrawlr {
    std::string Position::to_string() const
    {
        auto name = ParseData::tree_id_to_name(tree_id);
        return (name.empty() ? "" : (name + ":")) + std::to_string(line) + ":" + std::to_string(column);
    }
} // namespace qrawlr