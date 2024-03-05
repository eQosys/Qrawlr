#include "Rule.h"

#include <stdexcept>

namespace qrawlr
{
    Rule::Rule()
    {}

    MatchResult Rule::match_impl(const ParseData& data, int index) const
    {
        MatchResult result = MatcherMatchAny::match_impl(data, index);
        if (m_flags.is_set(Flags::FuseChildren))
            fuse_children(result.tree);
        return result;
    }

    std::string Rule::to_string_impl() const
    {
        throw std::runtime_error("Rule::to_string_impl() not implemented");
    }

    std::string Rule::gen_cpp_code() const
    {
        throw std::runtime_error("Rule::gen_cpp_code() not implemented");
    }

    void Rule::fuse_children(ParseTreeRef tree) const
    {
        (void)tree; // Currently unused

        throw std::runtime_error("Rule::fuse_children() not implemented");
    }

} // namespace qrawlr