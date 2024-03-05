#include "ParseTree.h"

namespace qrawlr
{
    int ParseTree::s_last_id = 0;

    ParseTree::ParseTree()
        : ParseTree(Position(), Position())
    {}

    ParseTree::ParseTree(const Position& pos_begin, const Position& pos_end)
        : m_id(++s_last_id),
        m_pos_begin(pos_begin), m_pos_end(pos_end)
    {}

    ParseTree::~ParseTree()
    {}
} // namespace qrawlr