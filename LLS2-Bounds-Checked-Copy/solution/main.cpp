#include <algorithm>
#include <array>
#include <iostream>
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

CopyResult copyUserLabel(std::string_view input, std::array<char, 16>& destination) {
	destination.fill('\0');

	if (input.find('\0') != std::string_view::npos) {
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

void runCase(std::string_view input) {
	std::array<char, 16> destination{};
	const CopyResult result = copyUserLabel(input, destination);
	std::cout << "input=\"" << input << "\" status=" << toText(result.status)
		<< " written=" << result.written
		<< " output=\"" << destination.data() << "\"\n";
}

int main() {
	runCase("Ada");
	runCase("SixteenCharText");
	runCase("A very long label that should not fit");
	runCase("");
}

