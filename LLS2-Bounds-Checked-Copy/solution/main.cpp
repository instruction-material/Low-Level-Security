#include <algorithm>
#include <array>
#include <cctype>
#include <iomanip>
#include <iostream>
#include <string>
#include <string_view>

enum class CopyStatus {
	Ok,
	Truncated,
	InvalidInput
};

struct CopyResult {
	CopyStatus status;
	std::size_t written;
};

bool containsDisallowedCharacters(std::string_view input) {
	for (char character : input) {
		const auto value = static_cast<unsigned char>(character);
		if (value == '\0' || !std::isprint(value)) {
			return true;
		}
	}

	return false;
}

CopyResult copyUserLabel(std::string_view input, std::array<char, 16>& destination) {
	destination.fill('\0');

	if (containsDisallowedCharacters(input)) {
		return { CopyStatus::InvalidInput, 0 };
	}

	const std::size_t maxVisibleChars = destination.size() - 1;
	const std::size_t amountToCopy = std::min(input.size(), maxVisibleChars);

	for (std::size_t index = 0; index < amountToCopy; ++index) {
		destination[index] = input[index];
	}

	destination[amountToCopy] = '\0';

	return {
		input.size() > maxVisibleChars ? CopyStatus::Truncated : CopyStatus::Ok,
		amountToCopy
	};
}

const char* toText(CopyStatus status) {
	switch (status) {
	case CopyStatus::Ok:
		return "ok";
	case CopyStatus::Truncated:
		return "truncated";
	case CopyStatus::InvalidInput:
		return "invalid-input";
	}

	return "unknown";
}

void printBytes(const std::array<char, 16>& destination) {
	std::cout << " bytes=[";
	for (std::size_t index = 0; index < destination.size(); ++index) {
		if (index != 0) {
			std::cout << ' ';
		}
		std::cout << static_cast<int>(static_cast<unsigned char>(destination[index]));
	}
	std::cout << "]";
}

struct TestCase {
	std::string_view input;
	CopyStatus expected;
};

void runCase(const TestCase& testCase) {
	std::array<char, 16> destination{};
	const CopyResult result = copyUserLabel(testCase.input, destination);
	std::cout << "input=" << std::quoted(std::string(testCase.input))
		<< " expected=" << toText(testCase.expected)
		<< " actual=" << toText(result.status)
		<< " written=" << result.written
		<< " output=" << std::quoted(std::string(destination.data()));
	printBytes(destination);
	std::cout << "\n";
}

int main() {
	runCase({ "Ada", CopyStatus::Ok });
	runCase({ "SixteenCharText", CopyStatus::Ok });
	runCase({ "A very long label that should not fit", CopyStatus::Truncated });
	runCase({ "", CopyStatus::Ok });
	runCase({ "Line\nBreak", CopyStatus::InvalidInput });
}

