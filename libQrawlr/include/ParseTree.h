#pragma once

#include <string>
#include <vector>
#include <memory>

#include "Position.h"

namespace qrawlr
{
    typedef std::shared_ptr<class ParseTree> ParseTreeRef;
    typedef std::shared_ptr<class ParseTreeNode> ParseTreeNodeRef;
    typedef std::shared_ptr<class ParseTreeExactMatch> ParseTreeExactMatchRef;

    class ParseTree
    {
    public:
        ParseTree() = delete;
        ParseTree(const Position& pos);
        ParseTree(const Position& pos_begin, const Position& pos_end);
        virtual ~ParseTree() = default;
    public:
        std::string to_digraph_str(bool verbose) const;
    public:
        const Position& get_pos_begin() const { return m_pos_begin; }
        const Position& get_pos_end() const { return m_pos_end; }
        void set_pos_end(const Position& pos_end) { m_pos_end = pos_end; }
    protected:
        std::string get_optional_verbose_info(bool verbose) const;
    public:
        virtual std::string to_string() const = 0;
    protected:
        virtual void to_digraph_impl(std::string& graph, bool verbose) const = 0;
    protected:
        int m_node_id;
        Position m_pos_begin;
        Position m_pos_end;
    private:
        static int s_last_node_id;
    private:
        friend class ParseTreeNode;
    };

    class ParseTreeNode : public ParseTree
    {
    public:
        ParseTreeNode() = delete;
        ParseTreeNode(const Position& pos_begin);
        virtual ~ParseTreeNode() = default;
    public:
        virtual std::string to_string() const override;
    protected:
        virtual void to_digraph_impl(std::string& graph, bool verbose) const override;
    public:
        void add_child(ParseTreeRef child, bool omit_match = false);
        void set_name(const std::string& name) { m_name = name; }
        const std::string& get_name() const { return m_name; }
        std::vector<ParseTreeRef>& get_children() { return m_children; }
        const std::vector<ParseTreeRef>& get_children() const { return m_children; }
    public:
        static std::shared_ptr<ParseTreeNode> make(const Position& pos_begin) { return std::make_shared<ParseTreeNode>(pos_begin);}
    protected:
        std::string m_name;
        std::vector<ParseTreeRef> m_children;
    };

    class ParseTreeExactMatch : public ParseTree
    {
    public:
        ParseTreeExactMatch() = delete;
        ParseTreeExactMatch(const std::string& value, const Position& pos_begin, const Position& pos_end);
        virtual ~ParseTreeExactMatch() = default;
    public:
        virtual std::string to_string() const override;
    protected:
        virtual void to_digraph_impl(std::string& graph, bool verbose) const override;
    public:
        std::string& get_value() { return m_value; }
        const std::string& get_value() const { return m_value; }
    public:
        static std::shared_ptr<ParseTreeExactMatch> make(const std::string& value, const Position& pos_begin, const Position& pos_end) { return std::make_shared<ParseTreeExactMatch>(value, pos_begin, pos_end); }
    protected:
        std::string m_value;
    };

    bool is_node(ParseTreeRef tree);
    bool is_node(ParseTreeRef tree, const std::string& name);
    ParseTreeNodeRef get_node(ParseTreeRef tree);
    ParseTreeNodeRef get_node(ParseTreeRef tree, const std::string& name);
    ParseTreeNodeRef expect_node(ParseTreeRef tree);
    ParseTreeNodeRef expect_node(ParseTreeRef tree, const std::string& name);
    bool is_leaf(ParseTreeRef tree);
    ParseTreeExactMatchRef get_leaf(ParseTreeRef tree);
    ParseTreeExactMatchRef expect_leaf(ParseTreeRef tree);

    ParseTreeRef expect_child(ParseTreeRef tree, const std::string& path);
    ParseTreeNodeRef expect_child_node(ParseTreeRef tree, const std::string& path);
    ParseTreeExactMatchRef expect_child_leaf(ParseTreeRef tree, const std::string& path);
    bool has_child(ParseTreeRef tree, const std::string& path);
    bool has_child_node(ParseTreeRef tree, const std::string& path);
    bool has_child_leaf(ParseTreeRef tree, const std::string& path);

} // namespace qrawlr