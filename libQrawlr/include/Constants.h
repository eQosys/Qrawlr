#pragma once

namespace qrawlr
{
    constexpr const char* TRIGGER_ON_MATCH = "onMatch";
    constexpr const char* TRIGGER_ON_FAIL  = "onFail";

    constexpr const char* QUANTIFIER_ZERO_OR_ONE = "?";
    constexpr const char* QUANTIFIER_ZERO_OR_MORE = "*";
    constexpr const char* QUANTIFIER_ONE_OR_MORE = "+";
    constexpr const char* QUANTIFIER_SPECIFY_RANGE = "#";
    constexpr const char* QUANTIFIER_SPECIFY_LOWER_BOUND = ">";
    constexpr const char* QUANTIFIER_SPECIFY_UPPER_BOUND = "<";
} // namespace qrawlr