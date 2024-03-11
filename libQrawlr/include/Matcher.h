#pragma once

#include <map>
#include <vector>
#include <string>

#include "Flags.h"
#include "Action.h"
#include "ParseTree.h"
#include "ParseData.h"
#include "MatchReplacement.h"

namespace qrawlr
{
    struct MatchResult
    {
        ParseTreeRef tree;
        Position position;
    };

    class Matcher
    {
    public:
        enum class Flags
        {
            Invert = 0,
            LookAhead = 1,
            LookBehind = 2,
            OmitMatch = 3,
        };
    public:
        Matcher();
        Matcher(const qrawlr::Flags<Flags>& flags, int count_min, int count_max, const MatchReplacement& match_repl, const std::map<std::string, std::vector<Action>>& actions);
        Matcher(const Matcher&) = default;
        Matcher(Matcher&&) = default;
        Matcher& operator=(const Matcher&) = default;
        Matcher& operator=(Matcher&&) = default;
        virtual ~Matcher() = default;
    public:
        MatchResult match(ParseData& data, int index) const;
    public:
        qrawlr::Flags<Flags>& get_flags() { return m_flags; }
        const qrawlr::Flags<Flags>& get_flags() const { return m_flags; }
        void set_count_bounds(int count_min, int count_max) { m_count_min = count_min; m_count_max = count_max; }
        void set_match_repl(const MatchReplacement& match_repl) { m_match_repl = match_repl; }
        void add_action(const std::string& trigger, const Action& action);
        std::string to_string() const;
    protected:
        std::string count_range_to_string() const;
        std::string modifiers_to_string() const;
        std::string actions_to_string() const;
        std::string action_list_to_string(const std::vector<Action>& actions) const;
        std::string action_args_to_string(const std::vector<Action::Arg>& args) const;
    private:
        MatchResult apply_invert(const ParseData& data, int index_old, int index_new, ParseTreeRef tree) const;
        ParseTreeRef apply_optional_match_repl(ParseTreeRef tree, ParseData& data, int index) const;
        void run_actions_for_trigger(const std::string& trigger_name, const ParseTreeRef tree, ParseData& data, int index) const;
    protected:
        virtual MatchResult match_impl(ParseData& data, int index) const = 0;
        virtual std::string to_string_impl() const = 0;
    public:
        virtual std::string gen_cpp_code() const = 0;
    protected:
        qrawlr::Flags<Flags> m_flags;
        int m_count_min;
        int m_count_max;
        MatchReplacement m_match_repl;
        std::map<std::string, std::vector<Action>> m_actions;
    };

    using MatcherRef = std::shared_ptr<Matcher>;

    // .
    class MatcherMatchAnyChar : public Matcher
    {
    public:
        MatcherMatchAnyChar() = default;
        virtual ~MatcherMatchAnyChar() = default;
    protected:
        virtual MatchResult match_impl(ParseData& data, int index) const override;
        virtual std::string to_string_impl() const override;
    public:
        virtual std::string gen_cpp_code() const override;
    };

    class MatcherList : public Matcher
    {
    public:
        MatcherList() = default;
        template <typename... Args>
        MatcherList(const std::vector<MatcherRef>& matchers, Args... args)
            : Matcher(args...), m_matchers(matchers)
        {}
        virtual ~MatcherList() = default;
    public:
        void set_matchers(const std::vector<MatcherRef>& matchers) { m_matchers = matchers; }
    protected:
        std::string gen_cpp_code_matchers() const;
    protected:
        std::vector<MatcherRef> m_matchers;
    };

    // (...)
    class MatcherMatchAll : public MatcherList
    {
    public:
        using MatcherList::MatcherList;
        virtual ~MatcherMatchAll() = default;
    protected:
        virtual MatchResult match_impl(ParseData& data, int index) const override;
        virtual std::string to_string_impl() const override;
    public:
        virtual std::string gen_cpp_code() const override;
    };

    // [...]
    class MatcherMatchAny : public MatcherList
    {
    public:
        using MatcherList::MatcherList;
        virtual ~MatcherMatchAny() = default;
    protected:
        virtual MatchResult match_impl(ParseData& data, int index) const override;
        virtual std::string to_string_impl() const override;
    public:
        virtual std::string gen_cpp_code() const override;
    };

    // 'xx'
    class MatcherMatchRange : public Matcher
    {
    public:
        MatcherMatchRange() = delete;
        template <typename... Args>
        MatcherMatchRange(const std::string& first, const std::string& last, Args... args)
            : Matcher(args...), m_first(first), m_last(last)
        {}
        virtual ~MatcherMatchRange() = default;
    protected:
        virtual MatchResult match_impl(ParseData& data, int index) const override;
        virtual std::string to_string_impl() const override;
    public:
        virtual std::string gen_cpp_code() const override;
    private:
        std::string m_first;
        std::string m_last;
    };

    // "..."
    class MatcherMatchExact : public Matcher
    {
    public:
        MatcherMatchExact() = delete;
        template <typename... Args>
        MatcherMatchExact(const std::string& exact, Args... args)
            : Matcher(args...), m_exact(exact)
        {}
        virtual ~MatcherMatchExact() = default;
    protected:
        virtual MatchResult match_impl(ParseData& data, int index) const override;
        virtual std::string to_string_impl() const override;
    public:
        virtual std::string gen_cpp_code() const override;
    private:
        std::string m_exact;
    };

    // ...
    class MatcherMatchRule : public Matcher
    {
    public:
        MatcherMatchRule() = delete;
        template <typename... Args>
        MatcherMatchRule(const std::string& rule_name, Args... args)
            : Matcher(args...), m_rule_name(rule_name)
        {}
        virtual ~MatcherMatchRule() = default;
    protected:
        virtual MatchResult match_impl(ParseData& data, int index) const override;
        virtual std::string to_string_impl() const override;
    public:
        virtual std::string gen_cpp_code() const override;
    private:
        std::string m_rule_name;
    };

    // :xx.xx:
    class MatcherMatchStack : public Matcher
    {
    public:
        MatcherMatchStack() = delete;
        template <typename... Args>
        MatcherMatchStack(const std::string& stack_name, int index, Args... args)
            : Matcher(args...), m_stack_name(stack_name), m_index(index)
        {}
        virtual ~MatcherMatchStack() = default;
    protected:
        virtual MatchResult match_impl(ParseData& data, int index) const override;
        virtual std::string to_string_impl() const override;
    public:
        virtual std::string gen_cpp_code() const override;
    private:
        std::string m_stack_name;
        int m_index;
    };
} // namespace qrawlr