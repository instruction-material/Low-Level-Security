#include <algorithm>
#include <array>
#include <iostream>
#include <string>
#include <string_view>

constexpr std::size_t kPacketBytes = 24;

struct PublicPacket {
	std::array<char, kPacketBytes> bytes{};
	std::size_t visibleLength = 0;
};

void fillInternalDebugNote(PublicPacket& packet, std::string_view note) {
	packet.bytes.fill('.');
	const std::size_t count = std::min(note.size(), packet.bytes.size());
	for (std::size_t index = 0; index < count; ++index) {
		packet.bytes[index] = note[index];
	}
	packet.visibleLength = count;
}

void writePublicStatus(PublicPacket& packet, std::string_view status) {
	const std::size_t count = std::min(status.size(), packet.bytes.size());
	for (std::size_t index = 0; index < count; ++index) {
		packet.bytes[index] = status[index];
	}
	packet.visibleLength = count;
}

std::string serializeForClient(const PublicPacket& packet) {
	// TODO:
	// return only the intended public bytes instead of the entire reused buffer.
	return std::string(packet.bytes.data(), packet.bytes.size());
}

int main() {
	PublicPacket packet{};
	fillInternalDebugNote(packet, "stack@0xfeedface");
	writePublicStatus(packet, "ok");

	std::cout << "public response -> [" << serializeForClient(packet) << "]\n";
	std::cout << "visible-length  -> " << packet.visibleLength << "\n";
	std::cout << "TODO: patch the serializer and write the triage note.\n";
}

