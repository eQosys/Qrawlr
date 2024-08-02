#include "ParseTree.h"

#include <stdexcept>
#include <sstream>
#include <limits>

#include "EscapeString.h"
#include "GrammarException.h"\

namespace qrawlr
{
    // -------------------- ParseTree -------------------- //

    int ParseTree::s_last_id = 0;

    ParseTree::ParseTree(const Position& pos)
        : ParseTree(pos, pos)
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

    // -------------------- Helpers -------------------- //

    bool is_node(ParseTreeRef tree)
    {
        return get_node(tree) != nullptr;
    }
    
    bool is_node(ParseTreeRef tree, const std::string& name)
    {
        return get_node(tree, name) != nullptr;
    }

    ParseTreeNodeRef get_node(ParseTreeRef tree)
    {
        return std::dynamic_pointer_cast<ParseTreeNode>(tree);
    }

    ParseTreeNodeRef get_node(ParseTreeRef tree, const std::string& name)
    {
        auto node = get_node(tree);
        if (!node)
            return nullptr;
        
        if (node->get_name() != name)
            return nullptr;

        return node;
    }

    ParseTreeNodeRef expect_node(ParseTreeRef tree, std::function<std::string(int)> tree_id_to_name)
    {
        auto node = get_node(tree);
        if (!node)
            throw GrammarException("[*expect_node*]: Expected node in grammar tree", tree->get_pos_begin().to_string(tree_id_to_name));
            
        return node;
    }
    
    ParseTreeNodeRef expect_node(ParseTreeRef tree, const std::string& name, std::function<std::string(int)> tree_id_to_name)
    {
        auto node = get_node(tree, name);
        if (!node)
            throw GrammarException("[*expect_node*]: Expected node with name '" + name + "' in grammar tree", tree->get_pos_begin().to_string(tree_id_to_name));
            
        return node;
    }

    bool is_leaf(ParseTreeRef tree)
    {
        return get_leaf(tree) != nullptr;
    }

    ParseTreeExactMatchRef get_leaf(ParseTreeRef tree)
    {
        return std::dynamic_pointer_cast<ParseTreeExactMatch>(tree);
    }

    ParseTreeExactMatchRef expect_leaf(ParseTreeRef tree, std::function<std::string(int)> tree_id_to_name)
    {
        auto leaf = get_leaf(tree);
        if (!leaf)
            throw GrammarException("[*expect_leaf*]: Expected leaf in grammar tree", tree->get_pos_begin().to_string(tree_id_to_name));
            
        return leaf;
    }

    bool parse_get_child_path_elem(const std::string& elem, std::string& name_out, int& index_out)
    {
        std::size_t selective_index = elem.find('#');
        if (selective_index == elem.npos) // Format is either <identifier> or <index>
        {
            std::stringstream ss(elem);
            ss >> index_out;
            if (ss.fail())
            {
                index_out = 0;
                name_out = elem;
            }
            else
            {
                name_out = "";
            }
        }
        else // Format is <identifier>#<name>
        {
            name_out = elem.substr(0, selective_index);

            std::stringstream ss(elem.substr(selective_index + 1));
            ss >> index_out;
            if (ss.fail())
                return false;
        }

        return true;
    }

    ParseTreeRef find_get_child_child(ParseTreeNodeRef node, const std::string& name, int index)
    {
        if (name.empty()) // Search by index only, child could be either node or leaf
        {
            auto& children = node->get_children();
            if (index < 0) // Select in reverse order
            {
                index = (int)children.size() - index;
                if (index < 0) // Out of bounds
                    return nullptr;
            }
            if (index >= (int)children.size()) // Out of bounds
                return nullptr;

            return children[index];
        }
        else // Search by name and index, child must be node
        {
            for (auto& child : node->get_children())
            {
                auto child_node = get_node(child);
                if (!child_node) // Skip non-nodes
                    continue;

                if (child_node->get_name() != name) // Skip nodes with wrong name
                    continue;

                if (index == 0)
                    return child;

                --index;
            }

            return nullptr; // No matching child found
        }
    }

    // usage example: get_child(tree, "StatementFunctionDeclDef.FunctionHeader.FunctionParameters.FunctionParameter#1.0")
    // Path syntax:
    //   path: <sub1>.<sub2>.<...>
    //   sub: <identifier>
    //        <index>
    //        <identifier>#<index>
    ParseTreeRef expect_child(ParseTreeRef tree, const std::string& path, std::function<std::string(int)> tree_id_to_name)
    {
        std::size_t sub_begin = 0;
        std::size_t sub_end = path.find('.');
        do
        {
            // retrieve a single element from the path (e.g. directory)
            std::string elem = path.substr(sub_begin, sub_end - sub_begin);

            // Convert to node if possible, otherwise throw error
            auto node = get_node(tree);
            if (!node)
                throw GrammarException("Expected node but got leaf in 'get_child'. (path: " + path + ", elem: " + elem + ")", tree->get_pos_begin().to_string(tree_id_to_name));

            // Parse element
            std::string name;
            int index;
            if (!parse_get_child_path_elem(elem, name, index))
                throw GrammarException("Invalid index provided in 'get_child'. (path: " + path + ", elem: " + elem + ")", tree->get_pos_begin().to_string(tree_id_to_name));
            
            auto newTree = find_get_child_child(node, name, index);
            if (!newTree)
                throw GrammarException("Could not find matching child in 'get_child'. (path: " + path + ", elem: " + elem + ")", tree->get_pos_begin().to_string(tree_id_to_name));
            tree = newTree;

            sub_begin = sub_end + 1;
            sub_end = path.find('.', sub_begin);
        } while (sub_begin != 0);

        return tree;
    }
    
    ParseTreeNodeRef expect_child_node(ParseTreeRef tree, const std::string& path, std::function<std::string(int)> tree_id_to_name)
    {
        auto node = get_node(expect_child(tree, path, nullptr));
        if (!node)
            throw GrammarException("Expected node but found leaf matching path '" + path + "'", tree->get_pos_begin().to_string(tree_id_to_name));
        return node;
    }
    
    ParseTreeExactMatchRef expect_child_leaf(ParseTreeRef tree, const std::string& path, std::function<std::string(int)> tree_id_to_name)
    {
        auto leaf = get_leaf(expect_child(tree, path, nullptr));
        if (!leaf)
            throw GrammarException("Expected leaf but found node matching path '" + path + "'", tree->get_pos_begin().to_string(tree_id_to_name));
        return leaf;
    }

    bool has_child(ParseTreeRef tree, const std::string& path)
    {
        try
        {
            expect_child(tree, path, nullptr);
            return true;
        }
        catch (const GrammarException&)
        {
            return false;
        }
    }

    bool has_child_node(ParseTreeRef tree, const std::string& path)
    {
        try
        {
            expect_child_node(tree, path, nullptr);
            return true;
        }
        catch (const GrammarException&)
        {
            return false;
        }
    }

    bool has_child_leaf(ParseTreeRef tree, const std::string& path)
    {
        try
        {
            expect_child_leaf(tree, path, nullptr);
            return true;
        }
        catch (const GrammarException&)
        {
            return false;
        }
    }

} // namespace qrawlr