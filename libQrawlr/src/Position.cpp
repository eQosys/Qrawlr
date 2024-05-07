#include "Position.h"

namespace qrawlr {
    std::string Position::to_string(const std::string& path)
    {
        return path + ":" + std::to_string(line) + ":" + std::to_string(column);
    }
} // namespace qrawlr