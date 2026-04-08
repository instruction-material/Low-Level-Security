#include <cstdint>
#include <iomanip>
#include <iostream>
#include <memory>
#include <string>
#include <vector>

int gGlobalCounter = 7;
static int gStaticCounter = 11;

std::intptr_t distanceBetween(const void* left, const void* right) {
	auto leftValue = reinterpret_cast<std::intptr_t>(left);
	auto rightValue = reinterpret_cast<std::intptr_t>(right);
	return leftValue > rightValue ? leftValue - rightValue : rightValue - leftValue;
}

void printRegion(const char* label, const void* address) {
	std::cout << std::left << std::setw(14) << label << ": " << address << "\n";
}

int main() {
	int stackValue = 42;
	int secondStackValue = 314;
	auto heapValue = std::make_unique<int>(99);
	std::string text = "security";
	std::vector<int> values{ 1, 2, 3, 4 };

	std::cout << std::hex << std::showbase;
	printRegion("stackValue", &stackValue);
	printRegion("secondStack", &secondStackValue);
	printRegion("heapValue", heapValue.get());
	printRegion("globalValue", &gGlobalCounter);
	printRegion("staticValue", &gStaticCounter);
	printRegion("string data", text.data());
	printRegion("vector data", values.data());

	std::cout << "\nDistances in bytes (approximate):\n";
	std::cout << "stack pair   : " << std::dec
		<< distanceBetween(&stackValue, &secondStackValue) << "\n";
	std::cout << "stack/heap   : "
		<< distanceBetween(&stackValue, heapValue.get()) << "\n";
	std::cout << "global/static: "
		<< distanceBetween(&gGlobalCounter, &gStaticCounter) << "\n";

	std::cout << "\nObservations:\n";
	std::cout << "- Stack locals are near each other and share function lifetime.\n";
	std::cout << "- Heap data is allocated separately and must be owned carefully.\n";
	std::cout << "- Global and static storage outlive main and have static duration.\n";
}

