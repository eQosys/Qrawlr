#pragma once

namespace qrawlr
{
    struct MatchReplacement
    {
        enum class Type
        {
            None = 0,
            Identifier,
            String,
            Stack
        } type = Type::None;
        std::string value = "";
    };
} // namespace qrawlr