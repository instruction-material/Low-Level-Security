#include <iostream>
#include <string>
#include <vector>

enum class CrashClass {
	HarmlessAbort,
	DenialOfService,
	MemoryDisclosure,
	MemoryCorruption
};

struct BugCase {
	std::string name;
	bool reachableFromUntrustedInput;
	bool attackerControlsShape;
	bool onlyAborts;
	bool leaksMemory;
	bool corruptsMemory;
	bool mitigationsPresent;
};

const char* toText(CrashClass value) {
	switch (value) {
	case CrashClass::HarmlessAbort:
		return "harmless-abort";
	case CrashClass::DenialOfService:
		return "denial-of-service";
	case CrashClass::MemoryDisclosure:
		return "memory-disclosure";
	case CrashClass::MemoryCorruption:
		return "memory-corruption";
	}

	return "unknown";
}

CrashClass classify(const BugCase& bug) {
	// TODO:
	// tighten this heuristic so corruption and disclosure outcomes do not get
	// flattened into a generic crash label.
	if (bug.onlyAborts) {
		return CrashClass::HarmlessAbort;
	}

	if (bug.leaksMemory) {
		return CrashClass::MemoryDisclosure;
	}

	return CrashClass::DenialOfService;
}

std::string exploitabilityNote(const BugCase& bug, CrashClass classification) {
	return "classification=" + std::string(toText(classification))
		+ " reachable=" + (bug.reachableFromUntrustedInput ? "yes" : "no")
		+ " attacker-control=" + (bug.attackerControlsShape ? "high" : "low");
}

int main() {
	const std::vector<BugCase> cases{
		{ "assert-only-parser", true, false, true, false, false, true },
		{ "null-deref-on-login", true, false, false, false, false, true },
		{ "stale-debug-dump", true, true, false, true, false, false },
		{ "unchecked-stack-write", true, true, false, false, true, false }
	};

	for (const BugCase& bug : cases) {
		const CrashClass classification = classify(bug);
		std::cout << bug.name << " -> " << toText(classification) << "\n";
		std::cout << "  " << exploitabilityNote(bug, classification) << "\n";
	}
}

