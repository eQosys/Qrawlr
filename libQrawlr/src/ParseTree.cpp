#include "ParseTree.h"

#include <stdexcept>

#include "EscapeString.h"

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

    std::string ParseTree::to_digraph_str(bool verbose) const
    {
        std::string graph;
        
        graph += "digraph {\n\tgraph [rankdir=LR]\n";
        to_digraph_impl(graph, verbose);
        graph += "}\n";

        return graph;
    }

    std::string ParseTree::get_optional_verbose_info(bool verbose) const
    {
        if (!verbose)
            return "";

        std::string info = "\n";
        info += std::to_string(m_pos_begin.line);
        info += ":";
        info += std::to_string(m_pos_begin.column);
        info += " -> ";
        info += std::to_string(m_pos_end.line);
        info += ":";
        info += std::to_string(m_pos_end.column);

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

    void ParseTreeNode::to_digraph_impl(std::string& graph, bool verbose) const
    {
        std::string text;
        text += m_name;
        text += get_optional_verbose_info(verbose);

        graph += "\t";
        graph += std::to_string(m_id);
        graph += " [label=\"";
        graph += escape_string(text);
        graph += "\" shape=ellipse]\n";

        for (auto& child : m_children)
        {
            child->to_digraph_impl(graph, verbose);
            graph += "\t";
            graph += std::to_string(m_id);
            graph += " -> ";
            graph += std::to_string(child->m_id);
            graph += "\n";
        }
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

    void ParseTreeExactMatch::to_digraph_impl(std::string& graph, bool verbose) const
    {
        std::string text;
        text += "\"";
        text += escape_string(m_value);
        text += "\"";
        text += get_optional_verbose_info(verbose);

        graph += "\t";
        graph += std::to_string(m_id);
        graph += " [label=\"";
        graph += escape_string(text);
        graph += "\" shape=plaintext]\n";
    }

    bool is_node(const ParseTreeRef tree)
    {
        return get_node(tree) != nullptr;
    }
    
    bool is_node(const ParseTreeRef tree, const std::string& name)
    {
        return get_node(tree, name) != nullptr;
    }

    ParseTreeNodeRef get_node(const ParseTreeRef tree)
    {
        return std::dynamic_pointer_cast<ParseTreeNode>(tree);
    }

    ParseTreeNodeRef get_node(const ParseTreeRef tree, const std::string& name)
    {
        auto node = get_node(tree);
        if (!node)
            return nullptr;
        
        if (node->get_name() != name)
            return nullptr;

        return node;
    }

    ParseTreeNodeRef expect_node(const ParseTreeRef tree)
    {
        auto node = get_node(tree);
        if (!node)
            throw std::runtime_error("[*expect_node*]: Expected node in grammar tree");
            
        return node;
    }
    
    ParseTreeNodeRef expect_node(const ParseTreeRef tree, const std::string& name)
    {
        auto node = get_node(tree, name);
        if (!node)
            throw std::runtime_error("[*expect_node*]: Expected node with name '" + name + "' in grammar tree");
            
        return node;
    }

    bool is_leaf(const ParseTreeRef tree)
    {
        return get_leaf(tree) != nullptr;
    }

    ParseTreeExactMatchRef get_leaf(const ParseTreeRef tree)
    {
        return std::dynamic_pointer_cast<ParseTreeExactMatch>(tree);
    }

    ParseTreeExactMatchRef expect_leaf(const ParseTreeRef tree)
    {
        auto leaf = get_leaf(tree);
        if (!leaf)
            throw std::runtime_error("[*expect_leaf*]: Expected leaf in grammar tree");
            
        return leaf;
    }

    ParseTreeRef get_child(const ParseTreeRef tree, const std::string& path)
    {
        // TODO: Proper implementation
        return nullptr;
    }
    
    ParseTreeNodeRef get_child_node(const ParseTreeRef tree, const std::string& path)
    {
        return get_node(get_child(tree, path));
    }
    
    ParseTreeExactMatchRef get_child_leaf(const ParseTreeRef tree, const std::string& path)
    {
        return get_leaf(get_child(tree, path));
    }

} // namespace qrawlr