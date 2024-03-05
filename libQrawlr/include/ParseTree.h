#pragma once

#include <memory>

#include "Position.h"

namespace qrawlr
{
    class ParseTree
    {
    public:
        ParseTree();
        ParseTree(const Position& pos_begin, const Position& pos_end);
        ~ParseTree();
    protected:
        int m_id;
        Position m_pos_begin;
        Position m_pos_end;
    private:
        static int s_last_id;
    };

    using ParseTreeRef = std::shared_ptr<ParseTree>;

} // namespace qrawlr