#include <cctype>
#include <cstdint>
#include <iostream>
#include <random>
#include <vector>

enum class ParseStatus {
	Ok,
	Rejected
};

ParseStatus parsePacket(const std::vector<std::uint8_t>& bytes) {
	if (bytes.size() < 2) {
		return ParseStatus::Rejected;
	}

	const std::size_t declaredLength = bytes[0];
	const std::uint8_t command = bytes[1];

	if (bytes.size() - 2 != declaredLength) {
		return ParseStatus::Rejected;
	}

	if (command != 0x01 && command != 0x02) {
		return ParseStatus::Rejected;
	}

	for (std::size_t index = 2; index < bytes.size(); ++index) {
		if (!std::isprint(bytes[index])) {
			return ParseStatus::Rejected;
		}
	}

	return ParseStatus::Ok;
}

std::vector<std::uint8_t> mutate(const std::vector<std::uint8_t>& seed, std::mt19937& engine) {
	std::vector<std::uint8_t> candidate = seed;
	std::uniform_int_distribution<std::size_t> indexDist(0, candidate.size() - 1);
	std::uniform_int_distribution<int> byteDist(0, 255);
	std::uniform_int_distribution<int> coin(0, 3);

	candidate[indexDist(engine)] = static_cast<std::uint8_t>(byteDist(engine));

	if (coin(engine) == 0) {
		candidate[0] = static_cast<std::uint8_t>(byteDist(engine) % 9);
	}

	if (coin(engine) == 1) {
		candidate[1] = static_cast<std::uint8_t>(byteDist(engine));
	}

	return candidate;
}

int main() {
	std::mt19937 engine(1337);
	const std::vector<std::uint8_t> seed{ 5, 0x01, 'h', 'e', 'l', 'l', 'o' };

	int accepted = 0;
	int rejected = 0;

	for (int round = 0; round < 50; ++round) {
		const std::vector<std::uint8_t> candidate = mutate(seed, engine);
		if (parsePacket(candidate) == ParseStatus::Ok) {
			++accepted;
		}
		else {
			++rejected;
		}
	}

	std::cout << "accepted=" << accepted << " rejected=" << rejected << "\n";
}
