#include <array>
#include <cstdint>
#include <iostream>
#include <vector>

class ByteRingBuffer {
public:
	bool push(const std::vector<std::uint8_t>& bytes) {
		(void) bytes;
		// TODO:
		// 1. Reject pushes that would exceed capacity.
		// 2. Write bytes at tail_ with wraparound.
		// 3. Update tail_ and count_ only after successful writes.
		return false;
	}

	bool pop(std::size_t amount, std::vector<std::uint8_t>& output) {
		(void) amount;
		output.clear();
		// TODO:
		// 1. Reject reads larger than count_.
		// 2. Read bytes from head_ with wraparound.
		// 3. Update head_ and count_ after a successful pop.
		return false;
	}

	std::size_t size() const {
		return count_;
	}

	static constexpr std::size_t capacity() {
		return kCapacity;
	}

private:
	static constexpr std::size_t kCapacity = 8;
	[[maybe_unused]] std::array<std::uint8_t, kCapacity> storage_{};
	[[maybe_unused]] std::size_t head_ = 0;
	[[maybe_unused]] std::size_t tail_ = 0;
	std::size_t count_ = 0;
};

void printBytes(const std::vector<std::uint8_t>& bytes) {
	for (std::uint8_t value : bytes) {
		std::cout << static_cast<int>(value) << ' ';
	}
	std::cout << "\n";
}

int main() {
	ByteRingBuffer buffer;
	std::vector<std::uint8_t> popped;

	std::cout << "push 4 -> " << buffer.push({ 1, 2, 3, 4 }) << "\n";
	std::cout << "size   -> " << buffer.size() << "\n";
	std::cout << "pop 2  -> " << buffer.pop(2, popped) << " data=";
	printBytes(popped);
	std::cout << "push 6 -> " << buffer.push({ 5, 6, 7, 8, 9, 10 }) << "\n";
	std::cout << "size   -> " << buffer.size() << "\n";
}
