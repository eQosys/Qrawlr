#include <cstdio>
#include <string>

#include "../libQrawlr/include/libQrawlr.h"

void print_help(const char* exe_name)
{
    printf("Usage: %s <mode> <grammar_file>:<entry_point> <input_file> <output_file>\n", exe_name);
    printf("Modes:\n");
    printf("  verify\n");
    printf("  parse\n");
    printf("  graph\n");
    printf("  render\n");
    printf("  help\n");
    printf("Mode 'help' does not require any other arguments\n");
}

std::string get_dot_command_str(const std::string& input_file, const std::string& output_file)
{
    std::string command;
    command += "dot -Tpdf";
    command += " -o \"" + qrawlr::escape_string(output_file) + "\"";
    command += " \"" + qrawlr::escape_string(input_file) + "\"";
    return command;
}

std::string gen_temp_file_path()
{
    return "/tmp/qrawlr-" + std::to_string(std::rand()) + ".tmp";
}

qrawlr::MatchResult apply_grammar_to_file(const std::string& grammar_file, const std::string& entry_point, const std::string& input_file, int* p_text_length = nullptr)
{
    printf("Reading input file...\n");
    auto text = qrawlr::read_file(input_file);

    if (p_text_length != nullptr)
        *p_text_length = text.size();

    printf("Loading grammar...\n");
    auto grammar = qrawlr::Grammar::load_from_file(grammar_file);

    printf("Parsing text...\n");
    return grammar.apply_to(text, entry_point, input_file);
}

void mode_verify(const std::string& grammar_file, const std::string& entry_point, const std::string& input_file)
{
    int text_length;

    auto result = apply_grammar_to_file(grammar_file, entry_point, input_file, &text_length);

    printf("Verifying result...\n");
    if (result.tree == nullptr)
        throw std::runtime_error("Failed to parse input file");

    if (result.pos_end.index < text_length)
        throw std::runtime_error("Failed to parse entire input file");
}

void mode_graph(const std::string& grammar_file, const std::string& entry_point, const std::string& input_file, const std::string& output_file)
{
    auto result = apply_grammar_to_file(grammar_file, entry_point, input_file);

    printf("Writing output file...\n");
    qrawlr::write_file(output_file, result.tree->to_digraph_str(true));
}

void mode_render(const std::string& grammar_file, const std::string& entry_point, const std::string& input_file, const std::string& output_file)
{
    auto temp_file = gen_temp_file_path();

    auto command = get_dot_command_str(temp_file, output_file);
    mode_graph(grammar_file, entry_point, input_file, temp_file);

    printf("Rendering to output file...\n");
    if (std::system(command.c_str()))
        throw std::runtime_error("Failed to execute dot command");
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
            mode_verify(grammar_file, entry_point, input_file);
            printf("Done\n");
            return 0;
        }
        else if (mode == "graph")
        {
            mode_graph(grammar_file, entry_point, input_file, output_file);
            printf("Done\n");
            return 0;
        }
        else if (mode == "render")
        {
            mode_render(grammar_file, entry_point, input_file, output_file);
            printf("Done\n");
            return 0;
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