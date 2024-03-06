#include "ParseTree.h"

namespace qrawlr
{
    // -------------------- ParseTree -------------------- //

    int ParseTree::s_last_id = 0;

    ParseTree::ParseTree()
        : ParseTree(Position())
    {}

    ParseTree::ParseTree(const Position& pos_begin)
        : ParseTree(pos_begin, pos_begin)
    {}

    ParseTree::ParseTree(const Position& pos_begin, const Position& pos_end)
        : m_id(++s_last_id),
        m_pos_begin(pos_begin), m_pos_end(pos_end)
    {}

    Digraph ParseTree::to_digraph(bool verbose) const
    {
        // TODO: Proper implementation
        Digraph graph = 0;
        to_digraph_impl(graph, verbose);
        return graph;
    }

    std::string ParseTree::get_optional_verbose_info(bool verbose) const
    {
        if (!verbose)
            return "";

        std::string info = "\\n";
        info += m_pos_begin.line;
        info += ":";
        info += m_pos_begin.column;
        info += " -> ";
        info += m_pos_end.line;
        info += ":";
        info += m_pos_end.column;

        return info;
    }

    // -------------------- ParseTreeNode -------------------- //

    ParseTreeNode::ParseTreeNode(const Position& pos_begin)
        : ParseTree(pos_begin)
    {}

    std::string ParseTreeNode::to_string() const
    {
        std::string result;

        for (auto& child : m_children)
            result += child->to_string();

        return result;
    }

    void ParseTreeNode::to_digraph_impl(Digraph& graph, bool verbose) const
    {
        // TODO: Proper implementation
        std::string text;
        text += m_name;
        text += get_optional_verbose_info(verbose);
    }

    void ParseTreeNode::add_child(ParseTreeRef child, bool omit_match)
    {
        if (!omit_match)
        {
            if (auto pNode = std::dynamic_pointer_cast<ParseTreeNode>(child); pNode != nullptr && pNode->m_name.empty())
                m_children.insert(m_children.end(), pNode->m_children.begin(), pNode->m_children.end());
            else
                m_children.push_back(child);
        }

        if (m_pos_end.index < child->m_pos_end.index)
            m_pos_end = child->m_pos_end;
    }

    // -------------------- ParseTreeExactMatch -------------------- //

    ParseTreeExactMatch::ParseTreeExactMatch()
        : ParseTree()
    {}

    ParseTreeExactMatch::ParseTreeExactMatch(const std::string& value, const Position& pos_begin, const Position& pos_end)
        : ParseTree(pos_begin, pos_end),
        m_value(value)
    {}

    std::string ParseTreeExactMatch::to_string() const
    {
        return m_value;
    }

    void ParseTreeExactMatch::to_digraph_impl(Digraph& graph, bool verbose) const
    {
        // TODO: Proper implementation
        std::string text;
        text += m_value;
        text += get_optional_verbose_info(verbose);
    }

} // namespace qrawlr