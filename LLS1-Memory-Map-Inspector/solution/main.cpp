#include <array>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <memory>
#include <string>
#include <vector>

int gGlobalCounter = 7;
static int gStaticCounter = 11;
const char gReadOnlyLabel[] = "lls";

struct RegionSample {
	const char* label;
	const void* address;
	const char* expectedRegion;
	const char* lifetime;
	const char* note;
};

std::intptr_t byteDistance(const void* left, const void* right) {
	const auto leftValue = reinterpret_cast<std::intptr_t>(left);
	const auto rightValue = reinterpret_cast<std::intptr_t>(right);
	return leftValue > rightValue ? leftValue - rightValue : rightValue - leftValue;
}

void printSample(const RegionSample& sample) {
	std::cout << std::left << std::setw(16) << sample.label
		<< " region=" << std::setw(10) << sample.expectedRegion
		<< " lifetime=" << std::setw(12) << sample.lifetime
		<< " address=" << sample.address
		<< " note=" << sample.note << "\n";
}

void printDistance(const char* label, const void* left, const void* right) {
	std::cout << std::left << std::setw(18) << label
		<< byteDistance(left, right) << " bytes\n";
}

int main() {
	int stackValue = 42;
	int secondStackValue = 314;
	std::array<int, 3> stackArray{ 1, 2, 3 };
	auto heapValue = std::make_unique<int>(99);
	auto heapBuffer = std::make_unique<std::array<char, 8>>();
	std::string text = "security";
	std::vector<int> values{ 1, 2, 3, 4 };

	(*heapBuffer)[0] = 'o';
	(*heapBuffer)[1] = 'k';
	(*heapBuffer)[2] = '\0';

	const std::vector<RegionSample> samples{
		{ "stackValue", &stackValue, "stack", "local", "destroyed when main returns" },
		{ "secondStack", &secondStackValue, "stack", "local", "near other locals" },
		{ "stackArray", stackArray.data(), "stack", "local", "contiguous local storage" },
		{ "heapValue", heapValue.get(), "heap", "owned", "released by unique_ptr" },
		{ "heapBuffer", heapBuffer->data(), "heap", "owned", "separate from local variables" },
		{ "globalValue", &gGlobalCounter, "global", "program", "static storage duration" },
		{ "staticValue", &gStaticCounter, "static", "program", "static storage duration" },
		{ "readOnly", gReadOnlyLabel, "rodata", "program", "read-only string literal area" },
		{ "string data", text.data(), "heap-ish", "object", "managed by std::string" },
		{ "vector data", values.data(), "heap", "object", "managed dynamic buffer" }
	};

	std::cout << std::hex << std::showbase;
	for (const RegionSample& sample : samples) {
		printSample(sample);
	}

	std::cout << std::dec;
	std::cout << "\nDistances in bytes (approximate):\n";
	printDistance("stack pair", &stackValue, &secondStackValue);
	printDistance("stack/global", &stackValue, &gGlobalCounter);
	printDistance("heap/vector", heapValue.get(), values.data());
	printDistance("global/static", &gGlobalCounter, &gStaticCounter);

	std::cout << "\nObservations:\n";
	std::cout << "- Stack locals cluster together because they share a call-frame lifetime.\n";
	std::cout << "- Heap allocations are separate from the stack and must be owned explicitly.\n";
	std::cout << "- Global, static, and read-only data live for the whole process lifetime.\n";
	std::cout << "- Address changes between runs do not change the storage class or lifetime rules.\n";
}

