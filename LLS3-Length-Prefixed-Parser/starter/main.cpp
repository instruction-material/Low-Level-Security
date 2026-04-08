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

ParseResult parsePacket(const std::vector<std::uint8_t>& bytes) {
	if (bytes.size() < 2) {
		return { ParseStatus::TooShort, 0, {} };
	}

	// Packet layout:
	// bytes[0] -> payload length
	// bytes[1] -> command byte (allowed: 0x01 and 0x02)
	// remaining bytes -> printable ASCII payload
	//
	// TODO:
	// 1. Check that the buffer length matches the declared payload length.
	// 2. Reject unknown commands.
	// 3. Reject non-printable payload bytes.
	return { ParseStatus::UnknownCommand, bytes[1], {} };
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

