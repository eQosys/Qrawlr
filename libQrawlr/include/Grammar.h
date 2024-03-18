#pragma once

#include <map>
#include <string>

#include "Rule.h"
#include "GrammarException.h"

namespace qrawlr
{
    class Grammar
    {
    protected:
        Grammar() = default;
    public:
        ~Grammar() = default;
    public:
        MatchResult apply_to(const std::string& text, const std::string& rule_name, const std::string& filename) const;
        std::string to_string() const;
    public:
        static Grammar load_from_file(const std::string& filename);
        static Grammar load_from_text(const std::string& text, const std::string& filename);
    public:
        void add_rule(RuleRef rule);
    private:
        void load_from_tree(const ParseTreeRef tree, const std::string& filename);
    private:
        RuleRef load_rule_definition_from_tree(const ParseTreeRef tree);
        RuleRef load_rule_header_from_tree(const ParseTreeRef tree);
        void load_rule_modifier_from_tree(RuleRef rule, const ParseTreeRef tree);
        std::vector<MatcherRef> load_rule_body_from_tree(const ParseTreeRef tree);
        MatcherRef load_rule_option_definition_from_tree(const ParseTreeRef tree);
        MatcherRef load_full_matcher_from_tree(const ParseTreeRef tree);
        MatcherRef load_matcher_from_tree(const ParseTreeRef tree);
        void load_matcher_modifiers_from_tree(MatcherRef matcher, const ParseTreeRef tree);
        void load_matcher_modifier_quantifier_from_tree(MatcherRef matcher, const ParseTreeRef tree);
        void load_matcher_modifier_replace_match_from_tree(MatcherRef matcher, const ParseTreeRef tree);
        void load_matcher_actions_from_tree(MatcherRef matcher, const ParseTreeRef tree);
        void load_matcher_trigger_from_tree(MatcherRef matcher, const ParseTreeRef tree);
        Action load_matcher_action_from_tree(const ParseTreeRef tree);

        std::string load_string_from_tree(const ParseTreeRef tree);
        std::string load_escape_sequence_from_tree(const ParseTreeRef tree);
        int load_integer_from_tree(const ParseTreeRef tree);
    private:
        static bool is_node(const ParseTreeRef tree) { return get_node(tree) != nullptr;}
        static bool is_node(const ParseTreeRef tree, const std::string& name) { return get_node(tree, name) != nullptr; }
        static ParseTreeNodeRef get_node(const ParseTreeRef tree);
        static ParseTreeNodeRef get_node(const ParseTreeRef tree, const std::string& name);
        static ParseTreeNodeRef expect_node(const ParseTreeRef tree);
        static ParseTreeNodeRef expect_node(const ParseTreeRef tree, const std::string& name);
        static bool is_leaf(const ParseTreeRef tree) { return get_leaf(tree) != nullptr; }
        static ParseTreeExactMatchRef get_leaf(const ParseTreeRef tree);
        static ParseTreeExactMatchRef expect_leaf(const ParseTreeRef tree);
    private:
        static Grammar load_internal_grammar();
    private:
        GrammarException make_exception(const std::string& message, const Position& pos);
    private:
        std::map<std::string, RuleRef> m_rules;
        std::string m_filename;
    private:
        friend Grammar load_internal_grammar();
    };
}; // namespace qrawlr