#include "Matcher.h"

namespace qrawlr
{
    // -------------------- MATCHER -------------------- //
    Matcher::Matcher()
        : m_flags(),
        m_count_min(1), m_count_max(1),
        m_match_repl(), m_actions()
    {}

    MatchResult Matcher::match(const ParseData& data, int index) const
    {
        // TODO: Proper implementation
        MatchResult result = match_impl(data, index);
        return result;
    }

    void Matcher::add_action(const std::string& trigger, const Action& action)
    {
        auto& actions = m_actions[trigger];
        actions.push_back(action);
    }

    MatchResult Matcher::apply_optional_invert(const ParseData& data, int index_old, int index_new, ParseTreeRef tree) const
    {
        // TODO: Proper implementation
        (void)data;
        (void)index_old;
        (void)index_new;
        return { tree, index_new };
    }

    void Matcher::run_actions_for_trigger(const ParseData& data, const std::string& trigger, const ParseTreeRef tree, int index) const
    {
        // TODO: Proper implementation
        (void)data;
        (void)trigger;
        (void)tree;
        (void)index;
    }

    ParseTreeRef Matcher::apply_match_repl(const ParseData& data, ParseTreeRef tree, int index) const
    {
        // TODO: Proper implementation
        (void)data;
        (void)index;
        return tree;
    }

    // -------------------- MATCHER MATCH ANY CHAR -------------------- //
    
    MatchResult MatcherMatchAnyChar::match_impl(const ParseData& data, int index) const
    {
        // TODO: Proper implementation
        (void)data;
        (void)index;
        return { nullptr, index };
    }

    std::string MatcherMatchAnyChar::to_string_impl() const
    {
        // TODO: Proper implementation
        return "MatcherMatchAnyChar";
    }

    std::string MatcherMatchAnyChar::gen_cpp_code() const
    {
        // TODO: Proper implementation
        return "MatcherMatchAnyChar()";
    }

    // -------------------- MATCHER LIST -------------------- //

    MatcherList::MatcherList(const std::vector<MatcherRef>& matchers)
        : m_matchers(matchers)
    {}

    std::string MatcherList::gen_cpp_code_matchers() const
    {
        // TODO: Proper implementation
        return "{}";
    }

    // -------------------- MATCHER MATCH ALL -------------------- //

    MatchResult MatcherMatchAll::match_impl(const ParseData& data, int index) const
    {
        // TODO: Proper imlementation
        (void)data;
        (void)index;
        return { nullptr, index };
    }

    std::string MatcherMatchAll::to_string_impl() const
    {
        // TODO: Proper implementation
        return "MatcherMatchAll";
    }

    std::string MatcherMatchAll::gen_cpp_code() const
    {
        // TODO: Proper implementation
        return "MatcherMatchAll()";
    }

    // -------------------- MATCHER MATCH ANY -------------------- //

    MatchResult MatcherMatchAny::match_impl(const ParseData& data, int index) const
    {
        // TODO: Proper imlementation
        (void)data;
        (void)index;
        return { nullptr, index };
    }

    std::string MatcherMatchAny::to_string_impl() const
    {
        // TODO: Proper implementation
        return "MatcherMatchAny";
    }

    std::string MatcherMatchAny::gen_cpp_code() const
    {
        // TODO: Proper implementation
        return "MatcherMatchAny()";
    }

    // -------------------- MATCHER MATCH RANGE -------------------- //

    MatcherMatchRange::MatcherMatchRange(const std::string& first, const std::string& last)
        : m_first(first), m_last(last)
    {}

    MatchResult MatcherMatchRange::match_impl(const ParseData& data, int index) const
    {
        // TODO: Proper imlementation
        (void)data;
        (void)index;
        return { nullptr, index };
    }

    std::string MatcherMatchRange::to_string_impl() const
    {
        // TODO: Proper implementation
        return "MatcherMatchRange";
    }

    std::string MatcherMatchRange::gen_cpp_code() const
    {
        // TODO: Proper implementation
        return "MatcherMatchRange()";
    }

    // -------------------- MATCHER MATCH EXACT -------------------- //

    MatcherMatchExact::MatcherMatchExact(const std::string& exact)
        : m_exact(exact)
    {}

    MatchResult MatcherMatchExact::match_impl(const ParseData& data, int index) const
    {
        // TODO: Proper imlementation
        (void)data;
        (void)index;
        return { nullptr, index };
    }

    std::string MatcherMatchExact::to_string_impl() const
    {
        // TODO: Proper implementation
        return "MatcherMatchExact";
    }

    std::string MatcherMatchExact::gen_cpp_code() const
    {
        // TODO: Proper implementation
        return "MatcherMatchExact()";
    }

    // -------------------- MATCHER MATCH RULE -------------------- //

    MatcherMatchRule::MatcherMatchRule(const std::string& rule_name)
        : m_rule_name(rule_name)
    {}

    MatchResult MatcherMatchRule::match_impl(const ParseData& data, int index) const
    {
        // TODO: Proper imlementation
        (void)data;
        (void)index;
        return { nullptr, index };
    }

    std::string MatcherMatchRule::to_string_impl() const
    {
        // TODO: Proper implementation
        return "MatcherMatchRule";
    }

    std::string MatcherMatchRule::gen_cpp_code() const
    {
        // TODO: Proper implementation
        return "MatcherMatchRule()";
    }

    // -------------------- MATCHER MATCH STACK -------------------- //

    MatcherMatchStack::MatcherMatchStack(const std::string& stack_name, int index)
        : m_stack_name(stack_name), m_index(index)
    {}

    MatchResult MatcherMatchStack::match_impl(const ParseData& data, int index) const
    {
        // TODO: Proper imlementation
        (void)data;
        (void)index;
        return { nullptr, index };
    }

    std::string MatcherMatchStack::to_string_impl() const
    {
        // TODO: Proper implementation
        return "MatcherMatchStack";
    }

    std::string MatcherMatchStack::gen_cpp_code() const
    {
        // TODO: Proper implementation
        return "MatcherMatchStack()";
    }

} // namespace qrawlr