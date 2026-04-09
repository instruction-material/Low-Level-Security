#include <cctype>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <random>
#include <sstream>
#include <string>
#include <vector>

enum class ParseStatus {
	Ok,
	TooShort,
	LengthMismatch,
	UnknownCommand,
	NonPrintable
};

ParseStatus parsePacket(const std::vector<std::uint8_t>& bytes) {
	if (bytes.size() < 2) {
		return ParseStatus::TooShort;
	}

	const std::size_t declaredLength = bytes[0];
	const std::uint8_t command = bytes[1];

	if (bytes.size() - 2 != declaredLength) {
		return ParseStatus::LengthMismatch;
	}

	if (command != 0x01 && command != 0x02) {
		return ParseStatus::UnknownCommand;
	}

	for (std::size_t index = 2; index < bytes.size(); ++index) {
		if (!std::isprint(static_cast<unsigned char>(bytes[index]))) {
			return ParseStatus::NonPrintable;
		}
	}

	return ParseStatus::Ok;
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

struct FuzzStats {
	int ok = 0;
	int tooShort = 0;
	int lengthMismatch = 0;
	int unknownCommand = 0;
	int nonPrintable = 0;
};

void recordStatus(FuzzStats& stats, ParseStatus status) {
	switch (status) {
	case ParseStatus::Ok:
		++stats.ok;
		break;
	case ParseStatus::TooShort:
		++stats.tooShort;
		break;
	case ParseStatus::LengthMismatch:
		++stats.lengthMismatch;
		break;
	case ParseStatus::UnknownCommand:
		++stats.unknownCommand;
		break;
	case ParseStatus::NonPrintable:
		++stats.nonPrintable;
		break;
	}
}

std::string packetToHex(const std::vector<std::uint8_t>& bytes) {
	std::ostringstream stream;
	stream << std::hex << std::setfill('0');
	for (std::size_t index = 0; index < bytes.size(); ++index) {
		if (index != 0) {
			stream << ' ';
		}
		stream << std::setw(2) << static_cast<int>(bytes[index]);
	}
	return stream.str();
}

std::vector<std::uint8_t> mutate(const std::vector<std::uint8_t>& seed, std::mt19937& engine) {
	std::vector<std::uint8_t> candidate = seed;

	// TODO:
	// 1. Flip a random byte.
	// 2. Sometimes perturb the length field.
	// 3. Sometimes perturb the command or payload size.
	(void) engine;
	return candidate;
}

int main() {
	std::mt19937 engine(1337);
	const std::vector<std::uint8_t> seed{ 5, 0x01, 'h', 'e', 'l', 'l', 'o' };

	FuzzStats stats;
	std::vector<std::string> interestingCases;

	for (int round = 0; round < 100; ++round) {
		const std::vector<std::uint8_t> candidate = mutate(seed, engine);
		const ParseStatus status = parsePacket(candidate);
		recordStatus(stats, status);
		if (status != ParseStatus::Ok && interestingCases.size() < 5) {
			interestingCases.push_back(packetToHex(candidate) + " -> " + toText(status));
		}
	}

	std::cout << "ok=" << stats.ok
		<< " too-short=" << stats.tooShort
		<< " length-mismatch=" << stats.lengthMismatch
		<< " unknown-command=" << stats.unknownCommand
		<< " non-printable=" << stats.nonPrintable << "\n";

	std::cout << "interesting cases:\n";
	for (const std::string& entry : interestingCases) {
		std::cout << " - " << entry << "\n";
	}
}

