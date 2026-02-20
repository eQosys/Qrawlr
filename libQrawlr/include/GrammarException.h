#pragma once

#include <string>
#include <stdexcept>

#include "Position.h"

namespace qrawlr
{
    class GrammarException : public std::runtime_error
    {
    public:
        GrammarException(const std::string& message)
            : std::runtime_error(message)
        {}

        GrammarException(const std::string& message, const Position& pos)
            : std::runtime_error(pos.to_string() + ": " + message)
        {}
    };
} // namespace qrawlr