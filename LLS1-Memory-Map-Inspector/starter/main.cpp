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
		<< " address=" << sample.address << "\n";
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
		{ "stackValue", &stackValue, "stack", "local" },
		{ "secondStack", &secondStackValue, "stack", "local" },
		{ "stackArray", stackArray.data(), "stack", "local" },
		{ "heapValue", heapValue.get(), "heap", "owned" },
		{ "heapBuffer", heapBuffer->data(), "heap", "owned" },
		{ "globalValue", &gGlobalCounter, "global", "program" },
		{ "staticValue", &gStaticCounter, "static", "program" },
		{ "readOnly", gReadOnlyLabel, "rodata", "program" },
		{ "string data", text.data(), "heap-ish", "object" },
		{ "vector data", values.data(), "heap", "object" }
	};

	std::cout << std::hex << std::showbase;
	for (const RegionSample& sample : samples) {
		printSample(sample);
	}

	std::cout << std::dec;
	std::cout << "\nStarter measurements:\n";
	std::cout << "stack pair bytes   = " << byteDistance(&stackValue, &secondStackValue) << "\n";
	std::cout << "stack/global bytes = " << byteDistance(&stackValue, &gGlobalCounter) << "\n";
	std::cout << "heap/vector bytes  = " << byteDistance(heapValue.get(), values.data()) << "\n";

	std::cout << "\nExtend this lab:\n";
	std::cout << "1. Add one more helper-function local and compare it to main's stack addresses.\n";
	std::cout << "2. Record which regions are tied to scope versus program lifetime.\n";
	std::cout << "3. Explain which addresses changed between runs and why that does not change storage class.\n";
}

