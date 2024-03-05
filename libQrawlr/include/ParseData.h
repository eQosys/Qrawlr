#pragma once

#include <set>
#include <map>
#include <string>
#include <vector>

#include "RuleRef.h"
#include "Position.h"

namespace qrawlr
{
    class ParseData
    {
    public:
        struct Checkpoint
        {
            std::map<std::string, int> stack_sizes;
        };
    public:
        ParseData() = default;
        ~ParseData() = default;
    public:
        const std::string& get_text() const { return m_text; }
        RuleRef get_rule(const std::string& name) { return m_rules[name]; }
        std::set<std::string> get_stack_names() const;
        std::vector<std::string>& get_stack(const std::string& name) { return m_stacks[name]; }
        std::vector<std::pair<std::string, std::string>>& get_stack_history(const std::string& name) { return m_stack_histories[name]; }
        bool eof(int index) const { return (size_t)index >= m_text.size(); }
        Checkpoint get_checkpoint() const;
        void restore_checkpoint(const Checkpoint& checkpoint);
        Position get_position(int index) const;
        std::string get_position_string(int index) const;
        bool stacks_are_empty() const;
    private:
        void generate_newline_indices();
    private:
        std::string m_text;
        std::string m_filename;
        std::map<std::string, RuleRef> m_rules;
        std::map<std::string, std::vector<std::string>> m_stacks;
        std::map<std::string, std::vector<std::pair<std::string, std::string>>> m_stack_histories;
        std::vector<int> m_newline_indices;
        int m_farthest_match_index;
    };
} // namespace qrawlr