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
        } m_type = Type::None;
        std::string m_value = "";
    };
} // namespace qrawlr