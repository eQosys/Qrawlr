#include "ParseData.h"

#include <algorithm>

#include "GrammarException.h"

namespace qrawlr
{
    ParseData::ParseData(const std::string& text, const std::string& filename, const std::map<std::string, RuleRef>& rules)
        : m_text(text), m_filename(filename), m_rules(rules),
        m_stacks(), m_stack_histories(),
        m_farthest_match_index(0)
    {
        generate_newline_indices();
    }

    std::set<std::string> ParseData::get_stack_names() const
    {
        std::set<std::string> names;
        for (const auto& pair : m_stacks)
            names.insert(pair.first);
        return names;
    }

    ParseData::Checkpoint ParseData::get_checkpoint() const
    {
        Checkpoint checkpoint;
        for (const auto& pair : m_stack_histories)
            checkpoint.stack_sizes[pair.first] = pair.second.size();
        return checkpoint;
    }

    void ParseData::restore_checkpoint(const Checkpoint& checkpoint)
    {
        for (auto& [name, size] : checkpoint.stack_sizes)
        {
            auto& stack = get_stack(name);
            auto& history = get_stack_history(name);
            while (stack.size() > (size_t)size)
            {
                auto item = history.back();
                history.pop_back();

                if (item.first == "push")
                    stack.pop_back();
                else if (item.first == "pop")
                    stack.push_back(item.second);
                else
                    throw GrammarException("Invalid stack history item");
            }
        }
    }

    Position ParseData::get_position(int index) const
    {
        int line = std::lower_bound(m_newline_indices.begin(), m_newline_indices.end(), index) - m_newline_indices.begin();
        int column = index - m_newline_indices[line - 1];
        return { index, line, column };
    }

    std::string ParseData::get_position_string(int index) const
    {
        Position position = get_position(index);
        return m_filename + ":" + std::to_string(position.line) + ":" + std::to_string(position.column);
    }

    bool ParseData::stacks_are_empty() const
    {
        for (auto& pair : m_stacks)
            if (!pair.second.empty())
                return false;

        return true;
    }

    void ParseData::generate_newline_indices()
    {
        m_newline_indices.clear();
        m_newline_indices.push_back(-1);
        for (size_t i = 0; i < m_text.size(); ++i)
            if (m_text[i] == '\n')
                m_newline_indices.push_back(i);
    }

} // namespace qrawlr