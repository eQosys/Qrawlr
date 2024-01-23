#pragma once

#include <string>
#include <stdexcept>

namespace qrawlr
{
    class GrammarException : public std::runtime_error
    {
    public:
        GrammarException(const std::string& message)
            : std::runtime_error(message)
        {}
    };
};