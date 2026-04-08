#include <cctype>
#include <cstdint>
#include <iostream>
#include <string>
#include <vector>

enum class ParseStatus {
	Ok,
	TooShort,
	LengthMismatch,
	UnknownCommand,
	NonPrintable
};

struct ParseResult {
	ParseStatus status;
	std::uint8_t command;
	std::string payload;
};

bool isAllowedCommand(std::uint8_t command) {
	return command == 0x01 || command == 0x02;
}

ParseResult parsePacket(const std::vector<std::uint8_t>& bytes) {
	if (bytes.size() < 2) {
		return { ParseStatus::TooShort, 0, {} };
	}

	const std::size_t declaredLength = bytes[0];
	const std::uint8_t command = bytes[1];
	const std::size_t actualPayloadLength = bytes.size() - 2;

	if (actualPayloadLength != declaredLength) {
		return { ParseStatus::LengthMismatch, command, {} };
	}

	if (!isAllowedCommand(command)) {
		return { ParseStatus::UnknownCommand, command, {} };
	}

	std::string payload;
	payload.reserve(actualPayloadLength);

	for (std::size_t index = 2; index < bytes.size(); ++index) {
		const unsigned char value = bytes[index];

		if (!std::isprint(value)) {
			return { ParseStatus::NonPrintable, command, {} };
		}

		payload.push_back(static_cast<char>(value));
	}

	return { ParseStatus::Ok, command, payload };
}

const char* toText(ParseStatus status) {
	switch (status) {
	case ParseStatus::Ok:
		return "ok";
	case ParseStatus::TooShort:
		return "too-short";
	case ParseStatus::LengthMismatch:
		return "length-mismatch";
	case ParseStatus::UnknownCommand:
		return "unknown-command";
	case ParseStatus::NonPrintable:
		return "non-printable";
	}

	return "unknown";
}

void runCase(const std::vector<std::uint8_t>& bytes) {
	const ParseResult result = parsePacket(bytes);
	std::cout << "status=" << toText(result.status)
		<< " command=" << static_cast<int>(result.command)
		<< " payload=\"" << result.payload << "\"\n";
}

int main() {
	runCase({ 5, 0x01, 'h', 'e', 'l', 'l', 'o' });
	runCase({ 5, 0x09, 'h', 'e', 'l', 'l', 'o' });
	runCase({ 4, 0x01, 'o', 'k' });
	runCase({ 3, 0x02, 'b', '\n', 'd' });
}

