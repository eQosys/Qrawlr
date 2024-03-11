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
        template <typename... Args>
        Rule(const std::string& name, const qrawlr::Flags<Flags>& rule_flags, Args... args)
            : MatcherMatchAny(args...), m_name(name), m_rule_flags(rule_flags)
        {}
        Rule(const Rule&) = default;
        Rule(Rule&&) = default;
        Rule& operator=(const Rule&) = default;
        Rule& operator=(Rule&&) = default;
        virtual ~Rule() = default;
    public:
        void set_name(const std::string& name) { m_name = name; }
        const std::string& get_name() const { return m_name; }
        qrawlr::Flags<Flags>& get_rule_flags() { return m_rule_flags; }
        const qrawlr::Flags<Flags>& get_rule_flags() const { return m_rule_flags; }
    protected:
        virtual MatchResult match_impl(ParseData& data, int index) const override;
        virtual std::string to_string_impl() const override;
        virtual std::string gen_cpp_code() const override;
    private:
        void fuse_children(ParseTreeRef tree) const;
    protected:
        std::string m_name;
        qrawlr::Flags<Flags> m_rule_flags;
    private:
        friend class MatcherMatchRule;
    };
}; // namespace qrawlr