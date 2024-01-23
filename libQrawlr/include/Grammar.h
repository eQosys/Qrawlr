#pragma once

#include <map>
#include <string>

#include "Rule.h"

namespace qrawlr
{
    class Grammar
    {
    protected:
        Grammar();
    public:
        ~Grammar();
    public:
        static Grammar load_from_file(const std::string& filename);
        static Grammar load_from_text(const std::string& text);
    private:
        std::map<std::string, Rule> m_rules;
    };
}; // namespace qrawlr