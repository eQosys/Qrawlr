#pragma once

#include <map>
#include <string>
#include <vector>

namespace qrawlr
{
    class ParseData
    {
    public:
        ParseData();
        ~ParseData();
    public:
        ;
    private:
        std::string m_text;
        std::string m_filename;
        std::map<std::string, class Rule> m_rules;
        std::map<std::string, std::vector<std::string>> m_stacks;
        std::map<std::string, std::vector<std::pair<std::string, std::string>>> m_stack_histories;
        int m_farthest_match_index;
    };
} // namespace qrawlr