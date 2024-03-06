#include "Matcher.h"

#include "Rule.h"
#include "Constants.h"
#include "EscapeString.h"
#include "GrammarException.h"

namespace qrawlr
{
    // -------------------- MATCHER -------------------- //
    Matcher::Matcher()
        : m_flags(),
        m_count_min(1), m_count_max(1),
        m_match_repl(), m_actions()
    {}

    MatchResult Matcher::match(ParseData& data, int index) const
    {
        int index_old = index;
        int match_count = 0;
        auto checkpoint = data.get_checkpoint();

        MatchResult sub_result;
        auto base_tree = ParseTreeNode::make(data.get_position(index));
        while (true)
        {
            sub_result = match_impl(data, index);
            if (m_flags.is_set(Flags::Invert))
                sub_result = apply_invert(data, index_old, sub_result.position.index, sub_result.tree);

            index = sub_result.position.index;

            if (!sub_result.tree)
                break;

            ++match_count;

            base_tree->add_child(sub_result.tree, m_flags.is_set(Flags::OmitMatch));

            if (match_count >= m_count_max)
                break;
        }
        ParseTreeRef tree = base_tree;

        if (match_count < m_count_min)
        {
            run_actions_for_trigger(TRIGGER_ON_FAIL, nullptr, data, index_old);
            data.restore_checkpoint(checkpoint);
            return { nullptr, { index_old, 0, 0 } };
        }

        if (data.get_farthest_match_index() < index)
            data.set_farthest_match_index(index);

        if (m_flags.is_set(Flags::LookAhead))
            index = index_old;

        run_actions_for_trigger(TRIGGER_ON_MATCH, tree, data, index_old);

        tree = apply_optional_match_repl(tree, data, index_old);

        return { tree, { index, 0, 0 } };
    }

    void Matcher::add_action(const std::string& trigger, const Action& action)
    {
        auto& actions = m_actions[trigger];
        actions.push_back(action);
    }

    std::string Matcher::to_string() const
    {
        return to_string_impl() + modifiers_to_string() + actions_to_string();
    }

    std::string Matcher::count_range_to_string() const
    {
        if (m_count_min == 0 &&
            m_count_max == 1)
            return QUANTIFIER_ZERO_OR_ONE;
        if (m_count_min == 0 &&
            m_count_max == -1)
            return QUANTIFIER_ZERO_OR_MORE;
        if (m_count_min == 1 &&
            m_count_max == -1)
            return QUANTIFIER_ONE_OR_MORE;
        if (m_count_min == 1 &&
            m_count_max == 1)
            return "";

        std::string result = QUANTIFIER_SPECIFY_RANGE;
        if (m_count_min == 0)
            result += QUANTIFIER_SPECIFY_UPPER_BOUND + std::to_string(m_count_max + 1);
        else if (m_count_max == -1)
            result += QUANTIFIER_SPECIFY_LOWER_BOUND + std::to_string(m_count_min - 1);
        else
            result += std::to_string(m_count_min) + "-" + std::to_string(m_count_max);

        return result;
    }

    std::string Matcher::modifiers_to_string() const
    {
        std::string result = "";

        if (m_flags.is_set(Flags::Invert))
            result += "!";

        result += count_range_to_string();

        if (m_flags.is_set(Flags::LookAhead))
            result += "~";
        if (m_flags.is_set(Flags::LookBehind))
            throw GrammarException("LookBehind not implemented");
        if (m_flags.is_set(Flags::OmitMatch))
            result += "_";

        if (m_match_repl.type != MatchReplacement::Type::None)
        {
            result += "->";
            if (m_match_repl.type == MatchReplacement::Type::String)
                result += "\"" + escape_string(m_match_repl.value) + "\"";
            else if (m_match_repl.type == MatchReplacement::Type::Stack)
                result += ":" + m_match_repl.value + ":";
            else if (m_match_repl.type == MatchReplacement::Type::Identifier)
                result += m_match_repl.value;
            else
                throw GrammarException("Invalid match replacement type");
        }

        return result;
    }

    std::string Matcher::actions_to_string() const
    {
        if (m_actions.empty())
            return "";

        std::string result = "{";

        for (const auto& [trigger, actions] : m_actions)
            result += trigger + ":" + action_list_to_string(actions) + ",";

        if (!m_actions.empty())
            result.pop_back();

        result += "}";

        return result;
    }

    std::string Matcher::action_list_to_string(const std::vector<Action>& actions) const
    {
        std::string result = "[";

        for (const auto& action : actions)
            result += action.get_name() + action_args_to_string(action.get_args()) + ",";

        if (!actions.empty())
            result.pop_back();

        result += "]";

        return result;
    }

    std::string Matcher::action_args_to_string(const std::vector<Action::Arg>& args) const
    {
        std::string result;

        for (const auto& arg : args)
        {
            if (arg.type == Action::ArgType::None)
                throw GrammarException("Cannot convert action argument of type None to string");
            else if (arg.type == Action::ArgType::Identifier)
                result += arg.value + ",";
            else if (arg.type == Action::ArgType::String)
                result += "\"" + escape_string(arg.value) + "\",";
            else if (arg.type == Action::ArgType::Match)
                result += "_,";
            else
                throw GrammarException("Invalid action argument type");
        }

        if (!args.empty())
            result.pop_back();

        return result;
    }

    MatchResult Matcher::apply_invert(const ParseData& data, int index_old, int index_new, ParseTreeRef tree) const
    {
        int index_next = index_new;

        if (tree == nullptr && !data.eof(index_old))
            return { ParseTreeExactMatch::make(data.get_text().substr(index_old, 1), data.get_position(index_old), data.get_position(index_next)), { index_next, 0, 0 } };

        return { tree, { index_old, 0, 0 } };
    }

    ParseTreeRef Matcher::apply_optional_match_repl(ParseTreeRef tree, ParseData& data, int index) const
    {
        if (m_match_repl.type == MatchReplacement::Type::None)
            return tree;

        if (m_match_repl.type == MatchReplacement::Type::String)
            return ParseTreeExactMatch::make(m_match_repl.value, data.get_position(index), data.get_position(index));

        if (m_match_repl.type == MatchReplacement::Type::Identifier)
        {
            auto node = std::dynamic_pointer_cast<ParseTreeNode>(tree);
            if (node)
                node->set_name(m_match_repl.value);

            return tree;
        }

        if (m_match_repl.type == MatchReplacement::Type::Stack)
        {
            int dot_index = m_match_repl.value.find('.');
            std::string stack_name = m_match_repl.value.substr(0, dot_index);
            int stack_index = std::stoi(m_match_repl.value.substr(dot_index + 1));

            auto& stack = data.get_stack(stack_name);

            std::string value = ((size_t)stack_index < stack.size()) ? stack[stack.size() - stack_index - 1] : "";

            return ParseTreeExactMatch::make(value, data.get_position(index), data.get_position(index));
        }

        throw GrammarException("Invalid match replacement type");

        return tree;
    }

    void Matcher::run_actions_for_trigger(const std::string& trigger_name, const ParseTreeRef tree, ParseData& data, int index) const
    {
        auto& trigger = m_actions.at(trigger_name);

        for (const auto& action : trigger)
            action.run(tree, data, index);
    }

    // -------------------- MATCHER MATCH ANY CHAR -------------------- //
    
    MatchResult MatcherMatchAnyChar::match_impl(ParseData& data, int index) const
    {
        if (data.eof(index))
            return { nullptr, { index, 0, 0 } };

        int index_next = index + 1;

        return { ParseTreeExactMatch::make(data.get_text().substr(index, 1), data.get_position(index), data.get_position(index_next)), { index_next, 0, 0 } };
    }

    std::string MatcherMatchAnyChar::to_string_impl() const
    {
        return ".";
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
        std::string code = "{";
        for (const auto& matcher : m_matchers)
            code += matcher->gen_cpp_code() + ", ";
        
        if (!m_matchers.empty())
            code.pop_back();
        
        code += "}";

        return code;
    }

    // -------------------- MATCHER MATCH ALL -------------------- //

    MatchResult MatcherMatchAll::match_impl(ParseData& data, int index) const
    {
        int index_old = index;

        std::vector<ParseTreeRef> children;

        for (const auto& matcher : m_matchers)
        {
            auto result = matcher->match(data, index);
            if (!result.tree)
                return { nullptr, { index_old, 0, 0 } };
            children.push_back(result.tree);
            index = result.position.index;
        }

        auto node = ParseTreeNode::make(data.get_position(index_old));
        for (const auto& child : children)
            node->add_child(child, m_flags.is_set(Flags::OmitMatch));

        return { node, { index, 0, 0 } };
    }

    std::string MatcherMatchAll::to_string_impl() const
    {
        if (m_matchers.size() == 1)
            return m_matchers[0]->to_string();
        
        std::string result = "(";
        for (const auto& matcher : m_matchers)
            result += matcher->to_string() + " ";
        
        if (!m_matchers.empty())
            result.pop_back();
        result += ")";

        return result;

    }

    std::string MatcherMatchAll::gen_cpp_code() const
    {
        // TODO: Proper implementation
        return "MatcherMatchAll()";
    }

    // -------------------- MATCHER MATCH ANY -------------------- //

    MatchResult MatcherMatchAny::match_impl(ParseData& data, int index) const
    {
        for (const auto& matcher : m_matchers)
        {
            auto result = matcher->match(data, index);
            if (result.tree)
                return result;
            index = result.position.index;
        }

        return { nullptr, { index, 0, 0 } };
    }

    std::string MatcherMatchAny::to_string_impl() const
    {
        if (m_matchers.size() == 1)
            return m_matchers[0]->to_string();
        
        std::string result = "[";
        for (const auto& matcher : m_matchers)
            result += matcher->to_string() + " ";
        
        if (!m_matchers.empty())
            result.pop_back();
        result += "]";

        return result;
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

    MatchResult MatcherMatchRange::match_impl(ParseData& data, int index) const
    {
        if (data.eof(index))
            return { nullptr, { index, 0, 0 } };

        int index_next = index + 1;

        std::string text = data.get_text().substr(index, 1);

        if (text < m_first || text > m_last)
            return { nullptr, { index, 0, 0 } };

        return { ParseTreeExactMatch::make(text, data.get_position(index), data.get_position(index_next)), { index_next, 0, 0 } };
    }

    std::string MatcherMatchRange::to_string_impl() const
    {
        return "'" + escape_string(m_first) + escape_string(m_last) + "'";
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

    MatchResult MatcherMatchExact::match_impl(ParseData& data, int index) const
    {
        if (data.eof(index))
            return { nullptr, { index, 0, 0 } };

        if (data.get_text().substr(index, m_exact.size()) != m_exact)
            return { nullptr, { index, 0, 0 } };

        int index_next = index + m_exact.size();

        return { ParseTreeExactMatch::make(m_exact, data.get_position(index), data.get_position(index_next)), { index_next, 0, 0 } };
    }

    std::string MatcherMatchExact::to_string_impl() const
    {
        return "\"" + escape_string(m_exact) + "\"";
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

    MatchResult MatcherMatchRule::match_impl(ParseData& data, int index) const
    {
        auto rule = data.get_rule(m_rule_name);
        if (!rule)
            throw GrammarException("Rule '" + m_rule_name + "' not found");
        
        auto result = rule->match(data, index);
        if (auto node = std::dynamic_pointer_cast<ParseTreeNode>(result.tree); node != nullptr && !rule->m_rule_flags.is_set(Rule::Flags::Anonymous))
            node->set_name(m_rule_name);
        
        return result;
    }

    std::string MatcherMatchRule::to_string_impl() const
    {
        return m_rule_name;
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

    MatchResult MatcherMatchStack::match_impl(ParseData& data, int index) const
    {
        auto& stack = data.get_stack(m_stack_name);
        std::string value_to_match = ((size_t)m_index < stack.size()) ? stack[stack.size() - m_index - 1] : "";

        if (data.get_text().substr(index, value_to_match.size()) != value_to_match)
            return { nullptr, { index, 0, 0 } };

        int index_next = index + value_to_match.size();
        return { ParseTreeExactMatch::make(value_to_match, data.get_position(index), data.get_position(index_next)), { index_next, 0, 0 } };
    }

    std::string MatcherMatchStack::to_string_impl() const
    {
        return ":" + m_stack_name + "." + std::to_string(m_index) + ":";
    }

    std::string MatcherMatchStack::gen_cpp_code() const
    {
        // TODO: Proper implementation
        return "MatcherMatchStack()";
    }

} // namespace qrawlr