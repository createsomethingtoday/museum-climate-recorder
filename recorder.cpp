#include <algorithm>
#include <charconv>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <optional>
#include <string>
#include <string_view>

enum class Status { accepted, stale, invalid };

struct Result {
    Status status;
    std::uint32_t sequence{};
    std::uint32_t missing{};
};

class Recorder {
public:
    Result observe(std::string_view line) {
        std::uint32_t value{};
        const char* end = line.data() + line.size();
        auto parsed = std::from_chars(line.data(), end, value);
        if (parsed.ec != std::errc{} || parsed.ptr != end) {
            return {Status::invalid};
        }
        if (previous && value <= *previous) {
            return {Status::stale};
        }
        auto missing = previous ? value - *previous - 1 : 0;
        previous = value;
        return {Status::accepted, value, missing};
    }

private:
    std::optional<std::uint32_t> previous;
};

// The longest report contains two labels, two ten-digit numbers and two newlines.
std::string_view format_result(char (&buffer)[64], Result result) {
    if (result.status == Status::invalid) return "invalid\n";
    if (result.status == Status::stale) return "stale\n";

    char* cursor = buffer;
    auto append = [&](std::string_view label, std::uint32_t value) {
        cursor = std::copy(label.begin(), label.end(), cursor);
        cursor = std::to_chars(cursor, buffer + sizeof(buffer), value).ptr;
        *cursor++ = '\n';
    };
    if (result.missing) append("missing ", result.missing);
    append("accepted ", result.sequence);
    return {buffer, static_cast<std::size_t>(cursor - buffer)};
}

int main(int argc, char** argv) {
    bool bulk = argc == 2 && std::string_view(argv[1]) == "--bulk";
    if (argc > 1 && !bulk) {
        std::cerr << "Usage: recorder [--bulk]\n";
        return 2;
    }

    Recorder recorder;
    char report[64];
    if (bulk) {
        // POSIX getline reuses its allocation and preserves embedded NUL bytes.
        char* data = nullptr;
        std::size_t capacity = 0;
        ssize_t length;
        bool written = true;
        while ((length = ::getline(&data, &capacity, stdin)) >= 0) {
            if (length && data[length - 1] == '\n') --length;
            auto output = format_result(report, recorder.observe({data, static_cast<std::size_t>(length)}));
            if (std::fwrite(output.data(), 1, output.size(), stdout) != output.size()) {
                written = false;
                break;
            }
        }
        std::free(data);
        return written && std::feof(stdin) && !std::ferror(stdin) && std::fflush(stdout) == 0 ? 0 : 1;
    }

    std::string line;
    while (std::getline(std::cin, line)) {
        std::cout << format_result(report, recorder.observe(line));
    }
    return std::cin.bad() || !std::cout.flush() ? 1 : 0;
}
