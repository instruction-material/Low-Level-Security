#include <array>
#include <cstdint>
#include <iostream>
#include <vector>

class ByteRingBuffer {
public:
	bool push(const std::vector<std::uint8_t>& bytes) {
		if (bytes.size() > kCapacity - count_) {
			return false;
		}

		for (std::uint8_t value : bytes) {
			storage_[tail_] = value;
			tail_ = (tail_ + 1) % kCapacity;
			++count_;
		}

		return true;
	}

	bool pop(std::size_t amount, std::vector<std::uint8_t>& output) {
		output.clear();

		if (amount > count_) {
			return false;
		}

		output.reserve(amount);

		for (std::size_t index = 0; index < amount; ++index) {
			output.push_back(storage_[head_]);
			head_ = (head_ + 1) % kCapacity;
			--count_;
		}

		return true;
	}

	std::size_t size() const {
		return count_;
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
	std::cout << "pop 4  -> " << buffer.pop(4, popped) << " data=";
	printBytes(popped);
	std::cout << "size   -> " << buffer.size() << "\n";
}

