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
        void load_from_tree(ParseTreeNodeRef tree, const std::string& filename);
    private:
        RuleRef load_rule_definition_from_tree(ParseTreeNodeRef node);
        RuleRef load_rule_header_from_tree(ParseTreeNodeRef node);
        void load_rule_modifier_from_tree(RuleRef rule, ParseTreeNodeRef node);
        std::vector<MatcherRef> load_rule_body_from_tree(ParseTreeNodeRef node);
        MatcherRef load_rule_option_definition_from_tree(ParseTreeNodeRef node);
        MatcherRef load_full_matcher_from_tree(ParseTreeNodeRef node);
        MatcherRef load_matcher_from_tree(ParseTreeNodeRef node);
        void load_matcher_modifiers_from_tree(MatcherRef matcher, ParseTreeNodeRef node);
        void load_matcher_modifier_quantifier_from_tree(MatcherRef matcher, ParseTreeNodeRef node);
        void load_matcher_modifier_replace_match_from_tree(MatcherRef matcher, ParseTreeNodeRef node);
        void load_matcher_actions_from_tree(MatcherRef matcher, ParseTreeNodeRef node);
        void load_matcher_trigger_from_tree(MatcherRef matcher, ParseTreeNodeRef node);
        Action load_matcher_action_from_tree(ParseTreeNodeRef node);

        std::string load_string_from_tree(ParseTreeNodeRef node);
        std::string load_escape_sequence_from_tree(ParseTreeNodeRef node);
        int load_integer_from_tree(ParseTreeNodeRef node);
    private:
        GrammarException make_node_exception(const std::string& message, ParseTreeRef node);
    private:
        std::map<std::string, RuleRef> m_rules;
        std::string m_filename;
    private:
        static Grammar load_internal_grammar();
    };
}; // namespace qrawlr