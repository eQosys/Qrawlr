#include "Action.h"

#include <stdexcept>
#include <iostream>

#include "GrammarException.h"

namespace qrawlr
{
    Action::Action(const std::string& name, const std::vector<Arg>& args)
        : m_name(name), m_args(args), m_func(nullptr)
    {
        if (name == "push")
            m_func = action_push;
        else if (name == "pop")
            m_func = action_pop;
        else if (name == "message")
            m_func = action_message;
        else if (name == "fail")
            m_func = action_fail;
        else
            throw GrammarException("Unknown action name: " + name);
    }

    void Action::run(ParseTreeRef tree, ParseData& data, int index) const
    {
        std::vector<Arg> args = m_args;
        for (auto& arg : args)
        {
            if (arg.type != ArgType::Match)
                continue;

            arg.type = ArgType::String;
            arg.value = tree->to_string();
        }

        m_func(args, data, index);
    }

    void Action::action_push(const std::vector<Arg>& args, ParseData& data, int index)
    {
        (void)index; // Unused

        if (args.size() != 2)
            throw GrammarException("Invalid number of arguments for action_push");

        auto& arg_item = args[0];
        auto& arg_stack_name = args[1];

        if (arg_stack_name.type != ArgType::Identifier)
            throw GrammarException("Invalid type for stack argument in action_push");

        if (arg_item.type != ArgType::String)
            throw GrammarException("Invalid type for item argument in action_push");
        
        auto& stack = data.get_stack(arg_stack_name.value);
        auto& history = data.get_stack_history(arg_stack_name.value);

        stack.push_back(arg_item.value);
        history.push_back(std::make_pair("push", arg_item.value));
    }

    void Action::action_pop(const std::vector<Arg>& args, ParseData& data, int index)
    {
        (void)index; // Unused

        if (args.size() != 1)
            throw GrammarException("Invalid number of arguments for action_pop");

        auto& arg_stack_name = args[0];

        if (arg_stack_name.type != ArgType::Identifier)
            throw GrammarException("Invalid type for stack argument in action_pop");

        auto& stack = data.get_stack(arg_stack_name.value);
        auto& history = data.get_stack_history(arg_stack_name.value);

        if (stack.empty())
            throw GrammarException("Cannot pop from an empty stack");

        history.push_back(std::make_pair("pop", stack.back()));
        stack.pop_back();
    }

    void Action::action_message(const std::vector<Arg>& args, ParseData& data, int index)
    {
        if (args.size() != 1)
            throw GrammarException("Invalid number of arguments for action_message");

        auto& arg_message = args[0];

        if (arg_message.type != ArgType::String)
            throw GrammarException("Invalid type for message argument in action_message");

        std::cout << data.get_position_string(index) << "MSG: " << ": " << arg_message.value << std::endl;
    }

    void Action::action_fail(const std::vector<Arg>& args, ParseData& data, int index)
    {
        if (args.size() != 1)
            throw GrammarException("Invalid number of arguments for action_fail");

        auto& arg_message = args[0];

        if (arg_message.type != ArgType::String)
            throw GrammarException("Invalid type for message argument in action_fail");

        throw GrammarException("FAIL: " + arg_message.value, data.get_position_string(index));
    }
} // namespace qrawlr