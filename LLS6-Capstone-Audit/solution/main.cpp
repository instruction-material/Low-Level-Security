#include <array>
#include <cctype>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <string>
#include <string_view>
#include <vector>

enum class HandleStatus {
	Ok,
	TooShort,
	LengthMismatch,
	UnknownCommand,
	NonPrintable,
	LabelTooLong,
	InvalidMode
};

struct HandleResult {
	HandleStatus status;
	std::string note;
};

struct DeviceState {
	std::array<char, 16> label{};
	bool diagnosticMode = false;
};

const char* toText(HandleStatus status) {
	switch (status) {
	case HandleStatus::Ok:
		return "ok";
	case HandleStatus::TooShort:
		return "too-short";
	case HandleStatus::LengthMismatch:
		return "length-mismatch";
	case HandleStatus::UnknownCommand:
		return "unknown-command";
	case HandleStatus::NonPrintable:
		return "non-printable";
	case HandleStatus::LabelTooLong:
		return "label-too-long";
	case HandleStatus::InvalidMode:
		return "invalid-mode";
	}

	return "unknown";
}

bool isAllowedCommand(std::uint8_t command) {
	return command == 0x01 || command == 0x02;
}

bool isPrintablePayload(std::string_view payload) {
	for (char character : payload) {
		if (!std::isprint(static_cast<unsigned char>(character))) {
			return false;
		}
	}

	return true;
}

std::string currentLabel(const DeviceState& state) {
	return state.label.data();
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

HandleResult applyRename(std::string_view payload, DeviceState& state) {
	if (payload.size() >= state.label.size()) {
		return { HandleStatus::LabelTooLong, "label exceeds fixed-size storage" };
	}

	std::array<char, 16> staged{};
	for (std::size_t index = 0; index < payload.size(); ++index) {
		staged[index] = payload[index];
	}
	staged[payload.size()] = '\0';
	state.label = staged;
	return { HandleStatus::Ok, "label updated" };
}

HandleResult handlePacket(const std::vector<std::uint8_t>& bytes, DeviceState& state) {
	if (bytes.size() < 2) {
		return { HandleStatus::TooShort, "header truncated" };
	}

	const std::size_t declaredLength = bytes[0];
	const std::uint8_t command = bytes[1];
	const std::size_t actualPayloadLength = bytes.size() - 2;

	if (actualPayloadLength != declaredLength) {
		return { HandleStatus::LengthMismatch, "declared length does not match buffer" };
	}

	if (!isAllowedCommand(command)) {
		return { HandleStatus::UnknownCommand, "unknown command byte" };
	}

	const std::string payload(bytes.begin() + 2, bytes.end());
	if (!isPrintablePayload(payload)) {
		return { HandleStatus::NonPrintable, "payload must stay printable" };
	}

	if (command == 0x01) {
		return applyRename(payload, state);
	}

	if (payload == "safe") {
		state.diagnosticMode = false;
		return { HandleStatus::Ok, "mode=safe" };
	}
	if (payload == "diag") {
		state.diagnosticMode = true;
		return { HandleStatus::Ok, "mode=diag" };
	}

	return { HandleStatus::InvalidMode, "mode payload must be safe or diag" };
}

void runCase(const char* label, const std::vector<std::uint8_t>& bytes, DeviceState& state) {
	const HandleResult result = handlePacket(bytes, state);
	std::cout << std::left << std::setw(14) << label
		<< " status=" << std::setw(16) << toText(result.status)
		<< " note=" << std::setw(34) << result.note
		<< " label=" << std::setw(12) << currentLabel(state)
		<< " diag=" << state.diagnosticMode << "\n";
}

int main() {
	DeviceState state{};
	state.label[0] = 's';
	state.label[1] = 'e';
	state.label[2] = 'n';
	state.label[3] = 's';
	state.label[4] = 'o';
	state.label[5] = 'r';
	state.label[6] = '-';
	state.label[7] = 'a';
	state.label[8] = '\0';

	runCase("rename", makePacket(0x01, "node-7"), state);
	runCase("too-long", makePacket(0x01, "this-label-is-far-too-long"), state);
	runCase("diag", makePacket(0x02, "diag"), state);
	runCase("safe", makePacket(0x02, "safe"), state);
	runCase("bad-cmd", makePacket(0x09, "noop"), state);
	runCase("bad-char", { 3, 0x01, 'o', '\n', 'k' }, state);
	runCase("bad-len", { 5, 0x02, 'o', 'k' }, state);
}
