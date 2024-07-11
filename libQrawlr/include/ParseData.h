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
        ParseData() = delete;
        ParseData(const std::string& text, const std::string& filename, const std::map<std::string, RuleRef>& rules);
        ~ParseData() = default;
    public:
        int get_tree_id() const { return m_tree_id; }
        const std::string& get_text() const { return m_text; }
        RuleRef get_rule(const std::string& name) const { return m_rules.find(name)->second; }
        std::set<std::string> get_stack_names() const;
        std::vector<std::string>& get_stack(const std::string& name) { return m_stacks[name]; }
        std::vector<std::pair<std::string, std::string>>& get_stack_history(const std::string& name) { return m_stack_histories[name]; }
        bool eof(int index) const { return (std::size_t)index >= m_text.size(); }
        Checkpoint get_checkpoint() const;
        void restore_checkpoint(const Checkpoint& checkpoint);
        Position get_position(int index) const;
        std::string get_position_string(int index) const;
        bool stacks_are_empty() const;
        int get_farthest_match_index() const { return m_farthest_match_index; }
        void set_farthest_match_index(int index) { m_farthest_match_index = index; }
    private:
        void generate_newline_indices();
    private:
        const int m_tree_id;
        std::string m_text;
        std::string m_filename;
        const std::map<std::string, RuleRef>& m_rules;
        std::map<std::string, std::vector<std::string>> m_stacks;
        std::map<std::string, std::vector<std::pair<std::string, std::string>>> m_stack_histories;
        std::vector<int> m_newline_indices;
        int m_farthest_match_index;
    private:
        static inline int s_tree_id = 0;
    };
} // namespace qrawlr