#include <cctype>
#include <cstdint>
#include <iostream>
#include <string>
#include <string_view>
#include <vector>

enum class ParseStatus {
	Ok,
	TooShort,
	LengthMismatch,
	PayloadTooLarge,
	UnknownCommand,
	NonPrintable
};

struct ParseResult {
	ParseStatus status;
	std::uint8_t command;
	std::string payload;
};

constexpr std::size_t kMaxPayloadBytes = 24;

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

	if (declaredLength > kMaxPayloadBytes) {
		return { ParseStatus::PayloadTooLarge, command, {} };
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
	case ParseStatus::PayloadTooLarge:
		return "payload-too-large";
	case ParseStatus::UnknownCommand:
		return "unknown-command";
	case ParseStatus::NonPrintable:
		return "non-printable";
	}

	return "unknown";
}

const char* commandName(std::uint8_t command) {
	switch (command) {
	case 0x01:
		return "echo";
	case 0x02:
		return "label";
	default:
		return "unknown";
	}
}

std::vector<std::uint8_t> makePacket(std::uint8_t command, std::string_view payload) {
	std::vector<std::uint8_t> bytes;
	bytes.reserve(payload.size() + 2);
	bytes.push_back(static_cast<std::uint8_t>(payload.size()));
	bytes.push_back(command);
	for (char character : payload) {
		bytes.push_back(static_cast<std::uint8_t>(character));
	}
	return bytes;
}

void runCase(const char* label, const std::vector<std::uint8_t>& bytes) {
	const ParseResult result = parsePacket(bytes);
	std::cout << label
		<< " status=" << toText(result.status)
		<< " command=" << static_cast<int>(result.command)
		<< " (" << commandName(result.command) << ")"
		<< " payload=\"" << result.payload << "\"\n";
}

int main() {
	runCase("valid        ", makePacket(0x01, "hello"));
	runCase("unknown cmd  ", makePacket(0x09, "hello"));
	runCase("bad length   ", { 4, 0x01, 'o', 'k' });
	runCase("nonprintable ", { 3, 0x02, 'b', '\n', 'd' });
	runCase("too short    ", { 1 });
	runCase("too large    ", makePacket(0x01, std::string(25, 'A')));
}

