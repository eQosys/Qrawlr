#include <cstdio>
#include <string>

#include "../libQrawlr/include/libQrawlr.h"

void print_help(const char* exe_name)
{
    printf("Usage: %s <mode> <grammar_file>:<entry_point> <input_file> <output_file>\n", exe_name);
    printf("Modes:\n");
    printf("  verify\n");
    printf("  parse\n");
    printf("  render\n");
    printf("  help\n");
}

int main(int argc, char** argv)
{
    if (argc < 2)
    {
        printf("Missing argument <mode>\n");
        print_help(argv[0]);
        return 1;
    }

    std::string mode = argv[1];

    if (mode == "help")
    {
        print_help(argv[0]);
        return 0;
    }

    if (argc != 5)
    {
        printf("Invalid number of arguments\n");
        return 1;
    }

    std::string grammar_input = argv[2];
    size_t colon_pos = grammar_input.find_last_of(':');
    if (colon_pos == std::string::npos)
    {
        printf("Missing argument <entry_point>\n");
        return 1;
    }

    std::string grammar_file = grammar_input.substr(0, colon_pos);
    std::string entry_point = grammar_input.substr(colon_pos + 1);
    std::string input_file = argv[3];
    std::string output_file = argv[4];

    try
    {
        qrawlr::Grammar grammar = qrawlr::Grammar::load_from_file(grammar_file);

        if (mode == "verify")
        {
            printf("TODO: verify\n");
            return 1;
        }
        else if (mode == "parse")
        {
            printf("TODO: parse\n");
            return 1;
        }
        else if (mode == "render")
        {
            printf("TODO: render\n");
            return 1;
        }
        else
        {
            printf("Invalid mode: %s\n", mode.c_str());
            return 1;
        }
    }
    catch (const std::exception& e)
    {
        printf("Error: %s\n", e.what());
        return 1;
    }

    return 0;
}