#include <charconv>
#include <cstdint>
#include <iostream>
#include <optional>
#include <string>
#include <system_error>

int main() {
    std::optional<std::uint32_t> previous;
    std::string line;
    while (std::getline(std::cin, line)) {
        std::uint32_t sequence{};
        const char* end = line.data() + line.size();
        auto parsed = std::from_chars(line.data(), end, sequence);
        if (parsed.ec != std::errc{} || parsed.ptr != end) {
            std::cout << "invalid\n";
            continue;
        }
        if (previous && sequence <= *previous) {
            std::cout << "stale\n";
            continue;
        }
        if (previous && sequence - *previous > 1) {
            std::cout << "missing " << sequence - *previous - 1 << '\n';
        }
        previous = sequence;
        std::cout << "accepted " << sequence << '\n';
    }
    return std::cin.bad() || !std::cout.flush() ? 1 : 0;
}
