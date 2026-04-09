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

void clearPacket(PublicPacket& packet) {
	packet.bytes.fill('.');
	packet.visibleLength = 0;
}

void fillInternalDebugNote(PublicPacket& packet, std::string_view note) {
	clearPacket(packet);
	const std::size_t count = std::min(note.size(), packet.bytes.size());
	for (std::size_t index = 0; index < count; ++index) {
		packet.bytes[index] = note[index];
	}
	packet.visibleLength = count;
}

void writePublicStatus(PublicPacket& packet, std::string_view status) {
	clearPacket(packet);
	const std::size_t count = std::min(status.size(), packet.bytes.size());
	for (std::size_t index = 0; index < count; ++index) {
		packet.bytes[index] = status[index];
	}
	packet.visibleLength = count;
}

std::string serializeForClient(const PublicPacket& packet) {
	return std::string(packet.bytes.data(), packet.visibleLength);
}

int main() {
	PublicPacket packet{};
	fillInternalDebugNote(packet, "stack@0xfeedface");
	writePublicStatus(packet, "ok");

	std::cout << "public response -> [" << serializeForClient(packet) << "]\n";
	std::cout << "visible-length  -> " << packet.visibleLength << "\n";
	std::cout << "summary         -> cleared stale bytes and serialized only the intended public range\n";
}

