#pragma once

#include <string>
#include <vector>

#include "ParseTree.h"
#include "ParseData.h"

namespace qrawlr
{
    class Action
    {
    public:
        enum class ArgType
        {
            None = 0,
            Identifier,
            String,
            Match
        };
        struct Arg
        {
            ArgType type;
            std::string value;
        };
    public:
        typedef void (*Func)(const std::vector<Arg>& args, ParseData& data, int index);
    public:
        Action() = delete;
        Action(const std::string& name, const std::vector<Arg>& args);
        ~Action() = default;
    public:
        void run(ParseTreeRef tree, ParseData& data, int index) const;
    public:
        const std::string& get_name() const { return m_name; }
        const std::vector<Arg>& get_args() const { return m_args; }
        void add_arg(ArgType type, const std::string& value) { m_args.push_back({type, value}); }
    public:
        static void action_push(const std::vector<Arg>& args, ParseData& data, int index);
        static void action_pop(const std::vector<Arg>& args, ParseData& data, int index);
        static void action_message(const std::vector<Arg>& args, ParseData& data, int index);
        static void action_fail(const std::vector<Arg>& args, ParseData& data, int index);
    private:
        std::string m_name;
        std::vector<Arg> m_args;
        Func m_func;
    };
} // namespace qrawlr