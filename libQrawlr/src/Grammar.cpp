#include "Grammar.h"

#include "Constants.h"
#include "FileReader.h"
#include "EscapeString.h"
#include "GrammarException.h"

namespace qrawlr
{
    MatchResult Grammar::apply_to(const std::string& text, const std::string& rule_name, const std::string& filename) const
    {
        auto it = m_rules.find(rule_name);
        if (it == m_rules.end())
            throw GrammarException("Rule '" + rule_name + "' not found in grammar");

        ParseData data(text, filename, m_rules);

        auto result = it->second->match(data, 0);
        result.pos_end = data.get_position(data.get_farthest_match_index());

        if (auto node = get_node(result.tree); node != nullptr)
            node->set_name(rule_name);
        
        if (!data.stacks_are_empty())
        {
            std::string data_str;
            for (const auto& stack_name : data.get_stack_names())
            {
                data_str += "  Stack '" + stack_name + "':\n";
                for (const auto& item : data.get_stack(stack_name))
                    data_str += "    -> " + item + " <-\n";
            }
            throw GrammarException("Stacks not empty after parsing. Data: " + data_str, data.get_position_string(result.pos_end.index));
        }

        return result;
    }

    std::string Grammar::to_string() const
    {
        std::string result;

        for (const auto& rule : m_rules)
            result += rule.second->to_string() + "\n";

        return result;
    }

    Grammar Grammar::load_from_file(const std::string& filename)
    {
        std::string text = read_file(filename);
        return load_from_text(text, filename);
    }

    Grammar Grammar::load_from_text(const std::string& text, const std::string& filename)
    {
        Grammar g = load_internal_grammar();

        auto result = g.apply_to(text, "Grammar", filename);
        
        if (result.tree == nullptr || (size_t)result.pos_end.index < text.size())
            throw GrammarException("Failed to parse provided grammar file", filename + ":" + std::to_string(result.pos_end.line) + ":" + std::to_string(result.pos_end.column));

        g.load_from_tree(result.tree, filename);

        return g;
    }

    void Grammar::add_rule(RuleRef rule)
    {
        if (m_rules.find(rule->get_name()) != m_rules.end())
            throw GrammarException("Rule '" + rule->get_name() + "' already defined");

        m_rules[rule->get_name()] = rule;
    }

    void Grammar::load_from_tree(const ParseTreeRef tree, const std::string& filename)
    {
        m_filename = filename;
        m_rules.clear();

        ParseTreeNodeRef root = expect_node(tree);

        for (auto& child : root->get_children())
        {
            if (is_node(child, "RuleDefinition"))
            {
                RuleRef rule = load_rule_definition_from_tree(child);
                m_rules[rule->get_name()] = rule;
            }
            else if (is_node(child, "Comment"))
                ; // Ignore comments
            else if (is_node(child))
                throw GrammarException("[*load_from_tree*]: Unexpected node in grammar tree");
            else
                throw GrammarException("[*load_from_tree*]: Expected node in grammar tree");
        }
    }

    RuleRef Grammar::load_rule_definition_from_tree(const ParseTreeRef tree)
    {
        auto node = expect_node(tree, "RuleDefinition");

        RuleRef rule = load_rule_header_from_tree(node->get_children()[0]);
        rule->set_matchers(load_rule_body_from_tree(node->get_children()[1]));
        return rule;
    }

    RuleRef Grammar::load_rule_header_from_tree(const ParseTreeRef tree)
    {
        auto node = expect_node(tree, "RuleHeader");

        auto rule = std::make_shared<Rule>();

        rule->set_name(get_leaf(get_node(node->get_children()[0])->get_children()[0])->get_value());

        if (m_rules.find(rule->get_name()) != m_rules.end())
            throw make_exception("Rule '" + rule->get_name() + "' already defined", node->get_pos_begin());

        auto children = node->get_children();
        children.erase(children.begin());

        for (auto child : children)
        {
            if (is_node(child, "RuleModifier"))
                load_rule_modifier_from_tree(rule, child);
            else
                throw make_exception("Expected node with name 'RuleModifier' in rule header", child->get_pos_begin());
        }

        return rule;
    }

    void Grammar::load_rule_modifier_from_tree(RuleRef rule, const ParseTreeRef tree)
    {
        auto node = expect_node(tree, "RuleModifier");

        auto modifier_name = get_leaf(node->get_children()[0])->get_value();

        if (modifier_name == "hidden")
            rule->get_rule_flags().set(Rule::Flags::Anonymous);
        else if (modifier_name == "fuse")
            rule->get_rule_flags().set(Rule::Flags::FuseChildren);
        else
            throw make_exception("Unknown rule modifier '" + modifier_name + "'", node->get_pos_begin());
    }

    std::vector<MatcherRef> Grammar::load_rule_body_from_tree(const ParseTreeRef tree)
    {
        auto node = expect_node(tree, "RuleBody");

        std::vector<MatcherRef> matchers;

        for (auto& child : node->get_children())
        {
            if (is_node(child, "RuleOptionDefinition"))
                matchers.push_back(load_rule_option_definition_from_tree(child));
            else if (is_node(child, "Comment"))
                ; // Ignore comments
            else if (is_node(child))
                throw GrammarException("[*load_rule_body_from_tree*]: Unexpected node in grammar tree");
            else
                throw make_exception("Expected node in grammar tree", child->get_pos_begin());
        }

        return matchers;
    }

    MatcherRef Grammar::load_rule_option_definition_from_tree(const ParseTreeRef tree)
    {
        auto node = expect_node(tree, "RuleOptionDefinition");

        std::vector<MatcherRef> matchers;
        for (auto& child : node->get_children())
            matchers.push_back(load_full_matcher_from_tree(child));

        auto option = std::make_shared<MatcherMatchAll>(matchers);

        return option;
    }

    MatcherRef Grammar::load_full_matcher_from_tree(const ParseTreeRef tree)
    {
        auto node = expect_node(tree, "FullMatcher");

        auto matcher = load_matcher_from_tree(node->get_children()[0]);
        load_matcher_modifiers_from_tree(matcher, node->get_children()[1]);
        load_matcher_actions_from_tree(matcher, node->get_children()[2]);
        return matcher;
    }

    MatcherRef Grammar::load_matcher_from_tree(const ParseTreeRef tree)
    {
        auto node = expect_node(tree);
        
        if (node->get_name() == "MatchAnyChar")
            return std::make_shared<MatcherMatchAnyChar>();
        else if (node->get_name() == "MatchAll")
        {
            std::vector<MatcherRef> matchers;
            for (auto& child : node->get_children())
                matchers.push_back(load_full_matcher_from_tree(child));
            
            auto matcher = std::make_shared<MatcherMatchAll>();
            matcher->set_matchers(matchers);
            return matcher;
        }
        else if (node->get_name() == "MatchAny")
        {
            std::vector<MatcherRef> matchers;
            for (auto& child : node->get_children())
                matchers.push_back(load_full_matcher_from_tree(child));
            
            auto matcher = std::make_shared<MatcherMatchAny>(matchers);
            matcher->set_matchers(matchers);
            return matcher;
        }
        else if (node->get_name() == "MatchRange")
        {
            auto& first = get_leaf(get_node(node->get_children()[0])->get_children()[0])->get_value();
            auto& last = get_leaf(get_node(node->get_children()[1])->get_children()[0])->get_value();
            return std::make_shared<MatcherMatchRange>(first, last);
        }
        else if (node->get_name() == "MatchExact")
        {
            auto value = load_string_from_tree(node->get_children()[0]);
            return std::make_shared<MatcherMatchExact>(value);
        }
        else if (node->get_name() == "MatchRule")
        {
            auto& rule_name = get_leaf(get_node(node->get_children()[0])->get_children()[0])->get_value();
            return std::make_shared<MatcherMatchRule>(rule_name);
        }
        else if (node->get_name() == "MatchStack")
        {
            auto& stack_name = get_leaf(get_node(node->get_children()[0])->get_children()[0])->get_value();
            auto index = load_integer_from_tree(node->get_children()[1]);
            return std::make_shared<MatcherMatchStack>(stack_name, index);
        }
        else
        {
            throw make_exception("Unknown matcher type '" + node->get_name() + "'", node->get_pos_begin());
        }
    }

    void Grammar::load_matcher_modifiers_from_tree(MatcherRef matcher, const ParseTreeRef tree)
    {
        auto node = expect_node(tree, "MatcherModifiers");

        for (auto& child : node->get_children())
        {
            if (is_node(child, "MatcherModifierInvert"))
                matcher->get_flags().set(Matcher::Flags::Invert);
            else if (is_node(child, "MatcherModifierQuantifier"))
                load_matcher_modifier_quantifier_from_tree(matcher, child);
            else if (is_node(child, "MatcherModifierLookAhead"))
                matcher->get_flags().set(Matcher::Flags::LookAhead);
            else if (is_node(child, "MatcherModifierLookBehind"))
                matcher->get_flags().set(Matcher::Flags::LookBehind);
            else if (is_node(child, "MatcherModifierOmitMatch"))
                matcher->get_flags().set(Matcher::Flags::OmitMatch);
            else if (is_node(child, "MatcherModifierReplaceMatch"))
                load_matcher_modifier_replace_match_from_tree(matcher, child);
            else if (is_node(child))
                throw make_exception("Unexpected node in matcher modifiers", child->get_pos_begin());
            else
                throw make_exception("Expected node in matcher modifiers", child->get_pos_begin());
        }
    }

    void Grammar::load_matcher_modifier_quantifier_from_tree(MatcherRef matcher, const ParseTreeRef tree)
    {
        auto node = expect_node(tree, "MatcherModifierQuantifier");
        node = get_node(node->get_children()[0]);

        if (!node)
            throw make_exception("Expected node in matcher quantifier", tree->get_pos_begin());

        if (is_node(node, "QuantifierSymbolic"))
        {
            const std::string& value = get_leaf(node->get_children()[0])->get_value();
            if (value == QUANTIFIER_ZERO_OR_ONE)
                matcher->set_count_bounds(0, 1);
            else if (value == QUANTIFIER_ZERO_OR_MORE)
                matcher->set_count_bounds(0, -1);
            else if (value == QUANTIFIER_ONE_OR_MORE)
                matcher->set_count_bounds(1, -1);
            else
                throw make_exception("Unknown quantifier '" + value + "'", node->get_pos_begin());
        }
        else if (is_node(node, "QuantifierRange"))
        {
            matcher->set_count_bounds(
                load_integer_from_tree(node->get_children()[0]),
                load_integer_from_tree(node->get_children()[1])
            );
        }
        else if (is_node(node, "QuantifierExact"))
        {
            int count = load_integer_from_tree(node->get_children()[0]);
            matcher->set_count_bounds(count, count);
        }
        else if (is_node(node, "QuantifierLowerBound"))
        {
            matcher->set_count_bounds(
                load_integer_from_tree(node->get_children()[0]) + 1,
                -1
            );
        }
        else if (is_node(node, "QuantifierUpperBound"))
        {
            matcher->set_count_bounds(
                0,
                load_integer_from_tree(node->get_children()[0]) - 1
            );
        }
        else
            throw make_exception("Unknown quantifier type", node->get_pos_begin());
    }

    void Grammar::load_matcher_modifier_replace_match_from_tree(MatcherRef matcher, const ParseTreeRef tree)
    {
        auto node = expect_node(tree, "MatcherModifierReplaceMatch");
        node = get_node(node->get_children()[0]);

        if (is_node(node, "Identifier"))
            matcher->set_match_repl({ MatchReplacement::Type::Identifier, get_leaf(node->get_children()[0])->get_value() });
        else if (is_node(node, "String"))
            matcher->set_match_repl({ MatchReplacement::Type::String, load_string_from_tree(node) });
        else if (is_node(node, "MatchStack"))
            matcher->set_match_repl(
                {
                    MatchReplacement::Type::Stack,
                    get_leaf(get_node(node->get_children()[0])->get_children()[0])->get_value()
                    + "." +
                    std::to_string(load_integer_from_tree(node->get_children()[1]))
                }
            );
        else
            throw make_exception("Unknown match replace type", node->get_pos_begin());
    }

    void Grammar::load_matcher_actions_from_tree(MatcherRef matcher, const ParseTreeRef tree)
    {
        auto node = expect_node(tree, "MatcherActions");

        for (auto child : node->get_children())
            load_matcher_trigger_from_tree(matcher, child);
    }

    void Grammar::load_matcher_trigger_from_tree(MatcherRef matcher, const ParseTreeRef tree)
    {
        auto node = expect_node(tree, "MatcherTrigger");

        auto trigger_name = get_leaf(get_node(node->get_children()[0])->get_children()[0])->get_value();

        auto children = get_node(node->get_children()[1])->get_children();

        for (auto child : children)
            matcher->add_action(trigger_name, load_matcher_action_from_tree(child));
    }

    Action Grammar::load_matcher_action_from_tree(const ParseTreeRef tree)
    {
        auto node = expect_node(tree, "MatcherAction");

        auto action_name = get_leaf(get_node(node->get_children()[0])->get_children()[0])->get_value();

        Action action(action_name, {});

        for (auto child : get_node(node->get_children()[1])->get_children())
        {
            if (is_node(child, "Identifier"))
                action.add_arg(Action::ArgType::Identifier, get_leaf(get_node(child)->get_children()[0])->get_value());
            else if (is_node(child, "String"))
                action.add_arg(Action::ArgType::String, load_string_from_tree(child));
            else if (is_node(child, "MatchedText"))
                action.add_arg(Action::ArgType::Match, "");
            else
                throw make_exception("Unknown action argument type", child->get_pos_begin());
        }

        return action;
    }

    std::string Grammar::load_string_from_tree(const ParseTreeRef tree)
    {
        auto node = expect_node(tree, "String");
        std::string result;

        for (auto& child : node->get_children())
        {
            if (is_leaf(child))
                result += get_leaf(child)->get_value();
            else if (is_node(child, "EscapeSequence"))
                result += load_escape_sequence_from_tree(child);
            else
                throw make_exception("Expected leaf or node with name 'EscapeSequence' in string", child->get_pos_begin());
        }

        return result;
    }

    std::string Grammar::load_escape_sequence_from_tree(const ParseTreeRef tree)
    {
        static const std::map<char, char> short_escapes = {
            {'a',  '\a'}, {'b',  '\b'},
            {'e',  '\e'}, {'f',  '\f'},
            {'n',  '\n'}, {'r',  '\r'},
            {'t',  '\t'}, {'v',  '\v'},
            {'\\', '\\'}, {'\'', '\''},
            {'\"', '\"'}
        };

        auto node = expect_node(tree, "EscapeSequence");
        auto& value = get_leaf(node->get_children()[0])->get_value();

        if (value.find('x') == 0)
            return std::string(1, (char)std::stoi(value.substr(1), nullptr, 16));

        if (value.size() != 1 || short_escapes.find(value[0]) == short_escapes.end())
            throw make_exception("Unknown escape sequence '" + escape_string(value) + "'", node->get_pos_begin());

        return std::string(1, short_escapes.at(value[0]));
    }

    int Grammar::load_integer_from_tree(const ParseTreeRef tree)
    {
        auto node = expect_node(tree, "Integer");
        const std::string& base_str = get_node(node->get_children()[1])->get_name();
        int base;
        if (base_str == "FormatBin")
            base = 2;
        else if (base_str == "FormatOct")
            base = 8;
        else if (base_str == "FormatDec")
            base = 10;
        else if (base_str == "FormatHex")
            base = 16;
        else
            throw make_exception("Unknown integer base format '" + base_str + "'", node->get_pos_begin());

        return std::stoi(get_leaf(node->get_children()[0])->get_value(), nullptr, base);
    }

    GrammarException Grammar::make_exception(const std::string& message, const Position& pos)
    {
        return GrammarException(message, m_filename + ":" + std::to_string(pos.line) + ":" + std::to_string(pos.column));
    }
} // namespace qrawlr