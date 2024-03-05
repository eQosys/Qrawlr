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
    protected:
        std::string get_optional_verbose_info(bool verbose) const;
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
    protected:
        virtual void to_digraph_impl(Digraph& graph, bool verbose) const override;
    public:
        void add_child(ParseTreeRef child, bool omit_match = false);
    protected:
        std::string m_name;
        std::vector<ParseTreeRef> m_children;
    };

    class ParseTreeExactMatch : public ParseTree
    {
    public:
        ParseTreeExactMatch();
        ParseTreeExactMatch(const std::string& value, const Position& pos_begin, const Position& pos_end);
        virtual ~ParseTreeExactMatch() = default;
    protected:
        virtual void to_digraph_impl(Digraph& graph, bool verbose) const override;
    protected:
        std::string m_value;
    };

} // namespace qrawlr