#pragma once

#include "RuleRef.h"
#include "Matcher.h"

namespace qrawlr
{
    class Rule : public MatcherMatchAny
    {
    public:
        enum class Flags
        {
            Anonymous = 0,
            FuseChildren = 1,
        }; 
    public:
        Rule();
        Rule(const Rule&) = default;
        Rule(Rule&&) = default;
        Rule& operator=(const Rule&) = default;
        Rule& operator=(Rule&&) = default;
        virtual ~Rule() = default;
    protected:
        virtual MatchResult match_impl(const ParseData& data, int index) const override;
        virtual std::string to_string_impl() const override;
        virtual std::string gen_cpp_code() const override;
    private:
        void fuse_children(ParseTreeRef tree) const;
    private:
        std::string m_name;
        qrawlr::Flags<Flags> m_flags;
    };
}; // namespace qrawlr