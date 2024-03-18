#include "Rule.h"

#include "GrammarException.h"

namespace qrawlr
{
    Rule::Rule()
    {}

    MatchResult Rule::match_impl(ParseData& data, int index) const
    {
        MatchResult result = MatcherMatchAny::match_impl(data, index);
        if (m_rule_flags.is_set(Flags::FuseChildren))
            fuse_children(result.tree);
        return result;
    }

    std::string Rule::to_string_impl() const
    {
        std::string header_str;

        header_str += m_name;

        {
            std::vector<std::string> flags;
            if (m_rule_flags.is_set(Flags::Anonymous))
                flags.push_back("hidden");
            if (m_rule_flags.is_set(Flags::FuseChildren))
                flags.push_back("fuse");

            if (!flags.empty())
            {
                header_str += "(";
                for (size_t i = 0; i < flags.size(); ++i)
                {
                    if (i > 0)
                        header_str += " ";
                    header_str += flags[i];
                }
                header_str += ")";
            }
        }

        header_str += ": ";
        return header_str + MatcherMatchAny::to_string_impl();
    }

    std::string Rule::gen_cpp_code() const
    {
        throw GrammarException("Rule::gen_cpp_code() not implemented");
    }

    void Rule::fuse_children(ParseTreeRef tree) const
    {
        auto node = std::dynamic_pointer_cast<ParseTreeNode>(tree);

        if (!node)
            return;

        int i = 0;
        std::shared_ptr<ParseTreeExactMatch> prevLeaf;
        while (i < node->get_children().size())
        {
            auto leaf = std::dynamic_pointer_cast<ParseTreeExactMatch>(node->get_children()[i]);
            if (leaf)
            {
                if (!prevLeaf)
                {
                    prevLeaf = leaf;
                }
                else
                {
                    prevLeaf->get_value() += leaf->get_value();
                    if (prevLeaf->get_pos_end().index < leaf->get_pos_end().index)
                        prevLeaf->set_pos_end(leaf->get_pos_end());
                    node->get_children().erase(node->get_children().begin() + i);
                    continue;
                }
            }
            else
            {
                prevLeaf.reset();
            }

            ++i;
        }
    }

} // namespace qrawlr