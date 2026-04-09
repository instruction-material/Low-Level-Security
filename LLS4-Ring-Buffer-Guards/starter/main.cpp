#include <array>
#include <cstdint>
#include <iostream>
#include <vector>

class ByteRingBuffer {
public:
	bool push(const std::vector<std::uint8_t>& bytes) {
		if (bytes.size() > freeSpace()) {
			return false;
		}

		// TODO:
		// 1. Stage writes starting at tail_ with wraparound.
		// 2. Commit tail_ and count_ only after the staged write succeeds.
		(void) bytes;
		return false;
	}

	bool pop(std::size_t amount, std::vector<std::uint8_t>& output) {
		output.clear();

		if (amount > count_) {
			return false;
		}

		// TODO:
		// 1. Read bytes from head_ with wraparound into a temporary vector.
		// 2. Commit head_ and count_ only after the read succeeds.
		(void) amount;
		return false;
	}

	std::size_t size() const {
		return count_;
	}

	std::size_t freeSpace() const {
		return kCapacity - count_;
	}

	bool invariantHolds() const {
		return head_ < kCapacity && tail_ < kCapacity && count_ <= kCapacity;
	}

	std::vector<std::uint8_t> snapshot() const {
		std::vector<std::uint8_t> bytes;
		bytes.reserve(count_);
		std::size_t index = head_;
		for (std::size_t count = 0; count < count_; ++count) {
			bytes.push_back(storage_[index]);
			index = (index + 1) % kCapacity;
		}
		return bytes;
	}

	static constexpr std::size_t capacity() {
		return kCapacity;
	}

private:
	static constexpr std::size_t kCapacity = 8;
	std::array<std::uint8_t, kCapacity> storage_{};
	std::size_t head_ = 0;
	std::size_t tail_ = 0;
	std::size_t count_ = 0;
};

void printBytes(const std::vector<std::uint8_t>& bytes) {
	if (bytes.empty()) {
		std::cout << "(empty)";
	}
	for (std::uint8_t value : bytes) {
		std::cout << static_cast<int>(value) << ' ';
	}
	std::cout << "\n";
}

void printState(const ByteRingBuffer& buffer, const char* label) {
	std::cout << label
		<< " size=" << buffer.size()
		<< " free=" << buffer.freeSpace()
		<< " invariant=" << buffer.invariantHolds()
		<< " logical=";
	printBytes(buffer.snapshot());
}

int main() {
	ByteRingBuffer buffer;
	std::vector<std::uint8_t> popped;

	printState(buffer, "initial ->");
	std::cout << "push 4 -> " << buffer.push({ 1, 2, 3, 4 }) << "\n";
	printState(buffer, "after p4 ->");
	std::cout << "pop 2  -> " << buffer.pop(2, popped) << " data=";
	printBytes(popped);
	printState(buffer, "after r2 ->");
	std::cout << "push 6 -> " << buffer.push({ 5, 6, 7, 8, 9, 10 }) << "\n";
	printState(buffer, "after p6 ->");
	std::cout << "pop 9  -> " << buffer.pop(9, popped) << " data=";
	printBytes(popped);
	printState(buffer, "after r9 ->");
}
