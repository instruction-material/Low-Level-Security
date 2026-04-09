#include <iostream>

#ifndef __has_feature
#define __has_feature(feature) 0
#endif

struct MitigationSnapshot {
	bool pie = false;
	bool addressSanitizer = false;
	bool stackProtector = false;
	bool fortify = false;
};

MitigationSnapshot detectMitigations() {
	MitigationSnapshot snapshot{};

#if defined(__PIE__) || defined(__pie__)
	snapshot.pie = true;
#endif

#if __has_feature(address_sanitizer) || defined(__SANITIZE_ADDRESS__)
	snapshot.addressSanitizer = true;
#endif

	// TODO:
	// detect stack protector macros such as __SSP__ or __SSP_STRONG__ and
	// mention the outcome in the printed summary.

#if defined(_FORTIFY_SOURCE) && _FORTIFY_SOURCE > 0
	snapshot.fortify = true;
#endif

	return snapshot;
}

void printSnapshot(const MitigationSnapshot& snapshot) {
	std::cout << "pie=" << (snapshot.pie ? "yes" : "no") << "\n";
	std::cout << "asan=" << (snapshot.addressSanitizer ? "yes" : "no") << "\n";
	std::cout << "stack-protector=" << (snapshot.stackProtector ? "yes" : "no")
		<< "\n";
	std::cout << "fortify=" << (snapshot.fortify ? "yes" : "no") << "\n";
}

int main() {
	std::cout << "Starter mitigation snapshot\n";
	printSnapshot(detectMitigations());
}

