#include <iomanip>
#include <iostream>
#include <memory>
#include <string>
#include <vector>

int gGlobalCounter = 7;
static int gStaticCounter = 11;

int main() {
	int stackValue = 42;
	auto heapValue = std::make_unique<int>(99);
	std::string text = "security";
	std::vector<int> values{ 1, 2, 3, 4 };

	std::cout << std::hex << std::showbase;
	std::cout << "stackValue  : " << &stackValue << "\n";
	std::cout << "heapValue   : " << heapValue.get() << "\n";
	std::cout << "globalValue : " << &gGlobalCounter << "\n";
	std::cout << "staticValue : " << &gStaticCounter << "\n";
	std::cout << "string data : " << static_cast<const void*>(text.data()) << "\n";
	std::cout << "vector data : " << static_cast<const void*>(values.data()) << "\n";

	std::cout << "\nTODO:\n";
	std::cout << "1. Add another stack variable and compare its address.\n";
	std::cout << "2. Print a byte-distance estimate between two nearby addresses.\n";
	std::cout << "3. Write notes on which objects are stack, heap, global, or static.\n";
}

