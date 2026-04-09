#include <iostream>
#include <string>

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

#if defined(__SSP__) || defined(__SSP_ALL__) || defined(__SSP_STRONG__)
	snapshot.stackProtector = true;
#endif

#if defined(_FORTIFY_SOURCE) && _FORTIFY_SOURCE > 0
	snapshot.fortify = true;
#endif

	return snapshot;
}

std::string summary(const MitigationSnapshot& snapshot) {
	std::string text = "Mitigations observed:";
	text += snapshot.pie ? " PIE" : " no-PIE";
	text += snapshot.addressSanitizer ? " ASan" : " no-ASan";
	text += snapshot.stackProtector ? " stack-protector" : " no-stack-protector";
	text += snapshot.fortify ? " fortify" : " no-fortify";
	return text;
}

void printSnapshot(const MitigationSnapshot& snapshot) {
	std::cout << "pie=" << (snapshot.pie ? "yes" : "no") << "\n";
	std::cout << "asan=" << (snapshot.addressSanitizer ? "yes" : "no") << "\n";
	std::cout << "stack-protector=" << (snapshot.stackProtector ? "yes" : "no")
		<< "\n";
	std::cout << "fortify=" << (snapshot.fortify ? "yes" : "no") << "\n";
	std::cout << summary(snapshot) << "\n";
}

int main() {
	std::cout << "Solution mitigation snapshot\n";
	printSnapshot(detectMitigations());
}

