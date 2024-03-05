#pragma once

#include <string>
#include <vector>

namespace qrawlr
{
    class Action
    {
    public:
        enum class ArgType
        {
            None = 0,
            Identifier,
            String,
            Match
        };
    public:
        Action();
        ~Action();
    private:
        std::string m_name;
        std::vector<std::pair<ArgType, std::string>> m_args;
    };
} // namespace qrawlr