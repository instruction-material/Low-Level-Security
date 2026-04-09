#include <iostream>
#include <sstream>
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
	if (bug.onlyAborts && !bug.leaksMemory && !bug.corruptsMemory) {
		return CrashClass::HarmlessAbort;
	}

	if (bug.corruptsMemory && bug.reachableFromUntrustedInput
		&& bug.attackerControlsShape) {
		return CrashClass::MemoryCorruption;
	}

	if (bug.leaksMemory && bug.reachableFromUntrustedInput) {
		return CrashClass::MemoryDisclosure;
	}

	return CrashClass::DenialOfService;
}

std::string exploitabilityNote(const BugCase& bug, CrashClass classification) {
	std::ostringstream stream;
	stream << "reachable=" << (bug.reachableFromUntrustedInput ? "yes" : "no")
		<< ", attacker-control=" << (bug.attackerControlsShape ? "high" : "low")
		<< ", mitigations=" << (bug.mitigationsPresent ? "present" : "limited")
		<< ", impact=" << toText(classification);

	if (classification == CrashClass::MemoryCorruption) {
		stream << ". Treat as security-relevant because attacker-shaped input can corrupt adjacent control or state data.";
	}
	else if (classification == CrashClass::MemoryDisclosure) {
		stream << ". Treat as disclosure risk because stale or unintended bytes cross a trust boundary.";
	}
	else if (classification == CrashClass::DenialOfService) {
		stream << ". Prioritize availability impact and confirm whether the crash can be triggered repeatedly.";
	}
	else {
		stream << ". Keep the note short and explain why current evidence does not show disclosure or corruption.";
	}

	return stream.str();
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

