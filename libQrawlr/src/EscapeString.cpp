#include "EscapeString.h"

namespace qrawlr
{
    std::string escape_string(const std::string& str)
    {
        std::string result;

        for (size_t i = 0; i < str.size(); ++i)
        {
            char c = str[i];

            switch (c)
            {
            case '\a':
                result += "\\a";
                break;
            case '\b':
                result += "\\b";
                break;
            case '\e':
                result += "\\e";
                break;
            case '\f':
                result += "\\f";
                break;
            case '\n':
                result += "\\n";
                break;
            case '\r':
                result += "\\r";
                break;
            case '\t':
                result += "\\t";
                break;
            case '\v':
                result += "\\v";
                break;
            case '\\':
                result += "\\\\";
                break;
            case '\'':
                result += "\\'";
                break;
            case '\"':
                result += "\\\"";
                break;
            default:
                result += c;
                break;
            }
        }

        return result;
    }
} // namespace qrawlr