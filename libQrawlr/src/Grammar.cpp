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
        
        if (result.tree == nullptr || (std::size_t)result.pos_end.index < text.size())
            throw GrammarException("Failed to parse provided grammar file", filename + ":" + std::to_string(result.pos_end.line) + ":" + std::to_string(result.pos_end.column));

        g.load_from_tree(expect_node(result.tree, "Grammar"), filename);

        return g;
    }

    void Grammar::add_rule(RuleRef rule)
    {
        if (m_rules.find(rule->get_name()) != m_rules.end())
            throw GrammarException("Rule '" + rule->get_name() + "' already defined");

        m_rules[rule->get_name()] = rule;
    }

    void Grammar::load_from_tree(const ParseTreeNodeRef root, const std::string& filename) // "Grammar"
    {
        if (root->get_name() != "Grammar")
            make_exception("Expected node with name 'Grammar', but got '" + root->get_name() + "'", root->get_pos_begin());

        m_filename = filename;
        m_rules.clear();

        for (auto& child : root->get_children())
        {
            if (is_node(child, "RuleDefinition"))
            {
                RuleRef rule = load_rule_definition_from_tree(get_node(child));
                m_rules[rule->get_name()] = rule;
            }
            else if (is_node(child, "Comment"))
                ; // Ignore comments
            else if (is_node(child))
                make_exception("[*load_from_tree*]: Unexpected node in grammar tree", child->get_pos_begin());
            else
                make_exception("[*load_from_tree*]: Expected node in grammar tree", child->get_pos_begin());
        }
    }

    RuleRef Grammar::load_rule_definition_from_tree(ParseTreeNodeRef node) // "RuleDefinition"
    {
        if (node->get_name() != "RuleDefinition")
            make_exception("Expected node with name 'RuleDefinition', but got '" + node->get_name() + "'", node->get_pos_begin());

        RuleRef rule = load_rule_header_from_tree(expect_child_node(node, "RuleHeader"));
        rule->set_matchers(load_rule_body_from_tree(expect_child_node(node, "RuleBody")));
        return rule;
    }

    RuleRef Grammar::load_rule_header_from_tree(ParseTreeNodeRef node) // "RuleHeader"
    {
        if (node->get_name() != "RuleHeader")
            make_exception("Expected node with name 'RuleHeader', but got '" + node->get_name() + "'", node->get_pos_begin());

        auto rule = std::make_shared<Rule>();

        rule->set_name(get_leaf(get_node(node->get_children()[0])->get_children()[0])->get_value());

        rule->set_name(expect_child_leaf(node, "Identifier.0")->get_value());

        if (m_rules.find(rule->get_name()) != m_rules.end())
            throw make_exception("Rule '" + rule->get_name() + "' already defined", node->get_pos_begin());

        auto children = node->get_children();
        children.erase(children.begin());

        for (auto child : children)
            load_rule_modifier_from_tree(rule, expect_node(child, "RuleModifier"));

        return rule;
    }

    void Grammar::load_rule_modifier_from_tree(RuleRef rule, ParseTreeNodeRef node) // "RuleModifier"
    {
        if (node->get_name() != "RuleModifier")
            make_exception("Expected node with name 'RuleModifier', but got '" + node->get_name() + "'", node->get_pos_begin());

        auto modifier_name = expect_child_leaf(node, "0")->get_value();

        if (modifier_name == "hidden")
            rule->get_rule_flags().set(Rule::Flags::Anonymous);
        else if (modifier_name == "fuse")
            rule->get_rule_flags().set(Rule::Flags::FuseChildren);
        else if (modifier_name == "collapse")
            rule->get_rule_flags().set(Rule::Flags::Collapse);
        else
            throw make_exception("Unknown rule modifier '" + modifier_name + "'", node->get_pos_begin());
    }

    std::vector<MatcherRef> Grammar::load_rule_body_from_tree(ParseTreeNodeRef node) // "RuleBody"
    {
        if (node->get_name() != "RuleBody")
            make_exception("Expected node with name 'RuleBody', but got '" + node->get_name() + "'", node->get_pos_begin());
        
        std::vector<MatcherRef> matchers;

        for (auto& child : node->get_children())
        {
            if (is_node(child, "RuleOptionDefinition"))
                matchers.push_back(load_rule_option_definition_from_tree(get_node(child)));
            else if (is_node(child, "Comment"))
                ; // Ignore comments
            else if (is_node(child))
                make_exception("[*load_rule_body_from_tree*]: Unexpected node in grammar tree", child->get_pos_begin());
            else
                throw make_exception("Expected node in grammar tree", child->get_pos_begin());
        }

        return matchers;
    }

    MatcherRef Grammar::load_rule_option_definition_from_tree(ParseTreeNodeRef node) // "RuleOptionDefinition"
    {
        if (node->get_name() != "RuleOptionDefinition")
            make_exception("Expected node with name 'RuleOptionDefinition', but got '" + node->get_name() + "'", node->get_pos_begin());

        std::vector<MatcherRef> matchers;
        for (auto& child : node->get_children())
            matchers.push_back(load_full_matcher_from_tree(expect_node(child, "FullMatcher")));

        auto option = std::make_shared<MatcherMatchAll>(matchers);

        return option;
    }

    MatcherRef Grammar::load_full_matcher_from_tree(ParseTreeNodeRef node) // "FullMatcher"
    {
        if (node->get_name() != "FullMatcher")
            make_exception("Expected node with name 'FullMatcher', but got '" + node->get_name() + "'", node->get_pos_begin());

        auto matcher = load_matcher_from_tree(expect_child_node(node, "0"));
        load_matcher_modifiers_from_tree(matcher, expect_child_node(node, "MatcherModifiers"));
        load_matcher_actions_from_tree(matcher, expect_child_node(node, "MatcherActions"));
        return matcher;
    }

    MatcherRef Grammar::load_matcher_from_tree(ParseTreeNodeRef node)
    {
        if (node->get_name() == "MatchAnyChar")
            return std::make_shared<MatcherMatchAnyChar>();
        else if (node->get_name() == "MatchAll")
        {
            std::vector<MatcherRef> matchers;
            for (auto& child : node->get_children())
                matchers.push_back(load_full_matcher_from_tree(expect_node(child, "FullMatcher")));
            
            auto matcher = std::make_shared<MatcherMatchAll>();
            matcher->set_matchers(matchers);
            return matcher;
        }
        else if (node->get_name() == "MatchAny")
        {
            std::vector<MatcherRef> matchers;
            for (auto& child : node->get_children())
                matchers.push_back(load_full_matcher_from_tree(expect_node(child, "FullMatcher")));
            
            auto matcher = std::make_shared<MatcherMatchAny>(matchers);
            matcher->set_matchers(matchers);
            return matcher;
        }
        else if (node->get_name() == "MatchRange")
        {
            auto& first = expect_child_leaf(node, "MatchRangeChar#0.0")->get_value();
            auto& last = expect_child_leaf(node, "MatchRangeChar#1.0")->get_value();
            return std::make_shared<MatcherMatchRange>(first, last);
        }
        else if (node->get_name() == "MatchExact")
        {
            auto value = load_string_from_tree(expect_child_node(node, "String"));
            return std::make_shared<MatcherMatchExact>(value);
        }
        else if (node->get_name() == "MatchRule")
        {
            auto& rule_name = expect_child_leaf(node, "Identifier.0")->get_value();
            return std::make_shared<MatcherMatchRule>(rule_name);
        }
        else if (node->get_name() == "MatchStack")
        {
            auto& stack_name = expect_child_leaf(node, "Identifier.0")->get_value();
            auto index = load_integer_from_tree(expect_child_node(node, "Integer"));
            return std::make_shared<MatcherMatchStack>(stack_name, index);
        }
        else
        {
            throw make_exception("Unknown matcher type '" + node->get_name() + "'", node->get_pos_begin());
        }
    }

    void Grammar::load_matcher_modifiers_from_tree(MatcherRef matcher, ParseTreeNodeRef node) // "MatcherModifiers"
    {
        if (node->get_name() != "MatcherModifiers")
            make_exception("Expected node with name 'MatcherModifiers', but got '" + node->get_name() + "'", node->get_pos_begin());

        for (auto& child : node->get_children())
        {
            if (is_node(child, "MatcherModifierInvert"))
                matcher->get_flags().set(Matcher::Flags::Invert);
            else if (is_node(child, "MatcherModifierQuantifier"))
                load_matcher_modifier_quantifier_from_tree(matcher, get_node(child));
            else if (is_node(child, "MatcherModifierLookAhead"))
                matcher->get_flags().set(Matcher::Flags::LookAhead);
            else if (is_node(child, "MatcherModifierLookBehind"))
                matcher->get_flags().set(Matcher::Flags::LookBehind);
            else if (is_node(child, "MatcherModifierOmitMatch"))
                matcher->get_flags().set(Matcher::Flags::OmitMatch);
            else if (is_node(child, "MatcherModifierReplaceMatch"))
                load_matcher_modifier_replace_match_from_tree(matcher, get_node(child));
            else if (is_node(child))
                throw make_exception("Unexpected node in matcher modifiers", child->get_pos_begin());
            else
                throw make_exception("Expected node in matcher modifiers", child->get_pos_begin());
        }
    }

    void Grammar::load_matcher_modifier_quantifier_from_tree(MatcherRef matcher, ParseTreeNodeRef node) // MatcherModifierQuantifier
    {
        if (node->get_name() != "MatcherModifierQuantifier")
            make_exception("Expected node with name 'MatcherModifierQuantifier', but got '" + node->get_name() + "'", node->get_pos_begin());

        node = expect_child_node(node, "0");

        if (node->get_name() == "QuantifierSymbolic")
        {
            auto& value = expect_child_leaf(node, "0")->get_value();
            if (value == QUANTIFIER_ZERO_OR_ONE)
                matcher->set_count_bounds(0, 1);
            else if (value == QUANTIFIER_ZERO_OR_MORE)
                matcher->set_count_bounds(0, -1);
            else if (value == QUANTIFIER_ONE_OR_MORE)
                matcher->set_count_bounds(1, -1);
            else
                throw make_exception("Unknown quantifier '" + value + "'", node->get_pos_begin());
        }
        else if (node->get_name() == "QuantifierRange")
        {
            matcher->set_count_bounds(
                load_integer_from_tree(expect_child_node(node, "Integer#0")),
                load_integer_from_tree(expect_child_node(node, "Integer#1"))
            );
        }
        else if (node->get_name() == "QuantifierExact")
        {
            int count = load_integer_from_tree(expect_child_node(node, "Integer"));
            matcher->set_count_bounds(count, count);
        }
        else if (node->get_name() == "QuantifierLowerBound")
        {
            matcher->set_count_bounds(
                load_integer_from_tree(expect_child_node(node, "Integer")) + 1,
                -1
            );
        }
        else if (node->get_name() == "QuantifierUpperBound")
        {
            matcher->set_count_bounds(
                0,
                load_integer_from_tree(expect_child_node(node, "Integer")) - 1
            );
        }
        else
            throw make_exception("Unknown quantifier type", node->get_pos_begin());
    }

    void Grammar::load_matcher_modifier_replace_match_from_tree(MatcherRef matcher, ParseTreeNodeRef node) // "MatcherModifierReplaceMatch"
    {
        if (node->get_name() != "MatcherModifierReplaceMatch")
            make_exception("Expected node with name 'MatcherModifierReplaceMatch', but got '" + node->get_name() + "'", node->get_pos_begin());

        node = expect_child_node(node, "0");

        if (is_node(node, "Identifier"))
            matcher->set_match_repl({ MatchReplacement::Type::Identifier, expect_child_leaf(node, "0")->get_value() });
        else if (is_node(node, "String"))
            matcher->set_match_repl({ MatchReplacement::Type::String, load_string_from_tree(node) });
        else if (is_node(node, "MatchStack"))
            matcher->set_match_repl(
                {
                    MatchReplacement::Type::Stack,
                    expect_child_leaf(node, "Identifier.0")->get_value()
                    + "." +
                    std::to_string(load_integer_from_tree(expect_child_node(node, "Integer")))
                }
            );
        else
            throw make_exception("Unknown match replace type", node->get_pos_begin());
    }

    void Grammar::load_matcher_actions_from_tree(MatcherRef matcher, ParseTreeNodeRef node) // "MatcherActions"
    {
        if (node->get_name() != "MatcherActions")
            make_exception("Expected node with name 'MatcherActions', but got '" + node->get_name() + "'", node->get_pos_begin());

        for (auto child : node->get_children())
            load_matcher_trigger_from_tree(matcher, expect_node(child, "MatcherTrigger"));
    }

    void Grammar::load_matcher_trigger_from_tree(MatcherRef matcher, ParseTreeNodeRef node) // "MatcherTrigger"
    {
        if (node->get_name() != "MatcherTrigger")
            make_exception("Expected node with name 'MatcherTrigger', but got '" + node->get_name() + "'", node->get_pos_begin());

        auto trigger_name = expect_child_leaf(node, "Identifier.0")->get_value();

        auto children = expect_child_node(node, "MatcherActionList")->get_children();

        for (auto child : children)
            matcher->add_action(trigger_name, load_matcher_action_from_tree(expect_node(child, "MatcherAction")));
    }

    Action Grammar::load_matcher_action_from_tree(ParseTreeNodeRef node) // MatcherAction
    {
        if (node->get_name() != "MatcherAction")
            make_exception("Expected node with name 'MatcherAction', but got '" + node->get_name() + "'", node->get_pos_begin());

        auto action_name = expect_child_leaf(node, "Identifier.0")->get_value();

        Action action(action_name, {});

        for (auto child : expect_child_node(node, "MatcherActionArgumentList")->get_children())
        {
            if (is_node(child, "Identifier"))
                action.add_arg(Action::ArgType::Identifier, expect_child_leaf(child, "0")->get_value());
            else if (is_node(child, "String"))
                action.add_arg(Action::ArgType::String, load_string_from_tree(get_node(child)));
            else if (is_node(child, "MatchedText"))
                action.add_arg(Action::ArgType::Match, "");
            else
                throw make_exception("Unknown action argument type", child->get_pos_begin());
        }

        return action;
    }

    std::string Grammar::load_string_from_tree(ParseTreeNodeRef node) // "String"
    {
        if (node->get_name() != "String")
            make_exception("Expected node with name 'String', but got '" + node->get_name() + "'", node->get_pos_begin());

        std::string result;

        for (auto& child : node->get_children())
        {
            if (is_leaf(child))
                result += get_leaf(child)->get_value();
            else if (is_node(child, "EscapeSequence"))
                result += load_escape_sequence_from_tree(get_node(child));
            else
                throw make_exception("Expected leaf or node with name 'EscapeSequence' in string", child->get_pos_begin());
        }

        return result;
    }

    std::string Grammar::load_escape_sequence_from_tree(ParseTreeNodeRef node) // "EscapeSequence"
    {
        static const std::map<char, char> short_escapes = {
            {'a',  '\a'}, {'b',  '\b'},
            {'e',  '\e'}, {'f',  '\f'},
            {'n',  '\n'}, {'r',  '\r'},
            {'t',  '\t'}, {'v',  '\v'},
            {'\\', '\\'}, {'\'', '\''},
            {'\"', '\"'}
        };

        if (node->get_name() != "EscapeSequence")
            make_exception("Expected node with name 'EscapeSequence', but got '" + node->get_name() + "'", node->get_pos_begin());

        auto& value = expect_child_leaf(node, "0")->get_value();

        if (value.find('x') == 0)
            return std::string(1, (char)std::stoi(value.substr(1), nullptr, 16));

        if (value.size() != 1 || short_escapes.find(value[0]) == short_escapes.end())
            throw make_exception("Unknown escape sequence '" + escape_string(value) + "'", node->get_pos_begin());

        return std::string(1, short_escapes.at(value[0]));
    }

    int Grammar::load_integer_from_tree(ParseTreeNodeRef node) // "Integer"
    {
        if (node->get_name() != "Integer")
            make_exception("Expected node with name 'Integer', but got '" + node->get_name() + "'", node->get_pos_begin());

        auto& base_str = expect_child_node(node, "1")->get_name();

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

        return std::stoi(expect_child_leaf(node, "0")->get_value(), nullptr, base);
    }

    GrammarException Grammar::make_exception(const std::string& message, const Position& pos)
    {
        return GrammarException(message, m_filename + ":" + std::to_string(pos.line) + ":" + std::to_string(pos.column));
    }
} // namespace qrawlr