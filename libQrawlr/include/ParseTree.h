#pragma once

#include <string>
#include <vector>
#include <memory>

#include "Position.h"

namespace qrawlr
{
    typedef int Digraph;

    class ParseTree
    {
    public:
        ParseTree();
        ParseTree(const Position& pos_begin);
        ParseTree(const Position& pos_begin, const Position& pos_end);
        virtual ~ParseTree() = default;
    public:
        Digraph to_digraph(bool verbose) const;
    public:
        const Position& get_pos_begin() const { return m_pos_begin; }
        const Position& get_pos_end() const { return m_pos_end; }
    protected:
        std::string get_optional_verbose_info(bool verbose) const;
    public:
        virtual std::string to_string() const = 0;
    protected:
        virtual void to_digraph_impl(Digraph& graph, bool verbose) const = 0;
    protected:
        int m_id;
        Position m_pos_begin;
        Position m_pos_end;
    private:
        static int s_last_id;
    private:
        friend class ParseTreeNode;
    };

    using ParseTreeRef = std::shared_ptr<ParseTree>;

    class ParseTreeNode : public ParseTree
    {
    public:
        ParseTreeNode() = default;
        ParseTreeNode(const Position& pos_begin);
        virtual ~ParseTreeNode() = default;
    public:
        virtual std::string to_string() const override;
    protected:
        virtual void to_digraph_impl(Digraph& graph, bool verbose) const override;
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

    using ParseTreeNodeRef = std::shared_ptr<ParseTreeNode>;

    class ParseTreeExactMatch : public ParseTree
    {
    public:
        ParseTreeExactMatch();
        ParseTreeExactMatch(const std::string& value, const Position& pos_begin, const Position& pos_end);
        virtual ~ParseTreeExactMatch() = default;
    public:
        virtual std::string to_string() const override;
    protected:
        virtual void to_digraph_impl(Digraph& graph, bool verbose) const override;
    public:
        const std::string& get_value() const { return m_value; }
    public:
        static std::shared_ptr<ParseTreeExactMatch> make(const std::string& value, const Position& pos_begin, const Position& pos_end) { return std::make_shared<ParseTreeExactMatch>(value, pos_begin, pos_end); }
    protected:
        std::string m_value;
    };

    using ParseTreeExactMatchRef = std::shared_ptr<ParseTreeExactMatch>;

} // namespace qrawlr