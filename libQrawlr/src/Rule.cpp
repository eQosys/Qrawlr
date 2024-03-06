#include "Rule.h"

#include "GrammarException.h"

namespace qrawlr
{
    Rule::Rule()
    {}

    MatchResult Rule::match_impl(ParseData& data, int index) const
    {
        MatchResult result = MatcherMatchAny::match_impl(data, index);
        if (m_rule_flags.is_set(Flags::FuseChildren))
            fuse_children(result.tree);
        return result;
    }

    std::string Rule::to_string_impl() const
    {
        throw GrammarException("Rule::to_string_impl() not implemented");
    }

    std::string Rule::gen_cpp_code() const
    {
        throw GrammarException("Rule::gen_cpp_code() not implemented");
    }

    void Rule::fuse_children(ParseTreeRef tree) const
    {
        (void)tree; // Currently unused

        throw GrammarException("Rule::fuse_children() not implemented");
    }

} // namespace qrawlr