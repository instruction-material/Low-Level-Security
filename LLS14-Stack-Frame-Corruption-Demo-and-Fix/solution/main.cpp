#include <array>
#include <algorithm>
#include <iostream>
#include <string_view>

constexpr std::size_t kBufferBytes = 12;
constexpr std::size_t kShadowBytes = 8;
constexpr std::size_t kFrameBytes = kBufferBytes + kShadowBytes;

struct ToyFrame {
	std::array<char, kFrameBytes> bytes{};
};

ToyFrame makeFrame() {
	ToyFrame frame{};
	frame.bytes.fill('.');
	const std::string_view savedReturn = "RETADDR!";
	for (std::size_t index = 0; index < savedReturn.size(); ++index) {
		frame.bytes[kBufferBytes + index] = savedReturn[index];
	}
	return frame;
}

std::string_view labelView(const ToyFrame& frame) {
	return { frame.bytes.data(), kBufferBytes };
}

std::string_view shadowView(const ToyFrame& frame) {
	return { frame.bytes.data() + kBufferBytes, kShadowBytes };
}

void unsafeCopy(std::string_view payload, ToyFrame& frame) {
	const std::size_t limit = std::min(frame.bytes.size(), payload.size());
	for (std::size_t index = 0; index < limit; ++index) {
		frame.bytes[index] = payload[index];
	}
}

bool safeCopy(std::string_view payload, ToyFrame& frame) {
	if (payload.size() > kBufferBytes) {
		return false;
	}

	ToyFrame staged = makeFrame();
	for (std::size_t index = 0; index < payload.size(); ++index) {
		staged.bytes[index] = payload[index];
	}
	frame = staged;
	return true;
}

bool shadowCorrupted(const ToyFrame& frame) {
	return shadowView(frame) != "RETADDR!";
}

void runCase(const char* label, std::string_view payload) {
	ToyFrame unsafeFrame = makeFrame();
	unsafeCopy(payload, unsafeFrame);
	std::cout << label << " unsafe label=[" << labelView(unsafeFrame)
		<< "] shadow=[" << shadowView(unsafeFrame)
		<< "] corrupted=" << (shadowCorrupted(unsafeFrame) ? "yes" : "no")
		<< "\n";

	ToyFrame safeFrame = makeFrame();
	const bool copied = safeCopy(payload, safeFrame);
	std::cout << label << " safe   copied=" << (copied ? "yes" : "no")
		<< " shadow=[" << shadowView(safeFrame)
		<< "] corrupted=" << (shadowCorrupted(safeFrame) ? "yes" : "no")
		<< "\n";
}

int main() {
	runCase("short", "node-7");
	runCase("long", "telemetry-target-alpha");
}

