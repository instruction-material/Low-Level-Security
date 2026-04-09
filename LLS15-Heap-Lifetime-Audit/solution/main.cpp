#include <cstdint>
#include <iostream>
#include <optional>
#include <string>
#include <vector>

struct Session {
	std::string owner;
	bool privileged = false;
};

struct SessionHandle {
	std::size_t slot = 0;
	std::uint32_t generation = 0;
};

struct Slot {
	std::optional<Session> session;
	std::uint32_t generation = 1;
};

class SessionPool {
public:
	SessionHandle create(std::string owner, bool privileged) {
		for (std::size_t index = 0; index < slots.size(); ++index) {
			if (!slots[index].session.has_value()) {
				slots[index].session = Session{ std::move(owner), privileged };
				return SessionHandle{ index, slots[index].generation };
			}
		}

		slots.push_back(Slot{ Session{ std::move(owner), privileged }, 1 });
		return SessionHandle{ slots.size() - 1, slots.back().generation };
	}

	bool release(const SessionHandle& handle) {
		if (!isValid(handle)) {
			return false;
		}

		slots[handle.slot].session.reset();
		++slots[handle.slot].generation;
		return true;
	}

	std::string auditView(const SessionHandle& handle) const {
		if (!isValid(handle)) {
			return "<invalid>";
		}

		const Session& session = *slots[handle.slot].session;
		return session.owner + (session.privileged ? " [priv]" : " [user]");
	}

private:
	bool isValid(const SessionHandle& handle) const {
		return handle.slot < slots.size()
			&& slots[handle.slot].session.has_value()
			&& slots[handle.slot].generation == handle.generation;
	}

	std::vector<Slot> slots;
};

int main() {
	SessionPool pool;

	const SessionHandle alice = pool.create("alice", false);
	std::cout << "alice view -> " << pool.auditView(alice) << "\n";

	const bool released = pool.release(alice);
	std::cout << "released alice -> " << (released ? "yes" : "no") << "\n";

	const SessionHandle bob = pool.create("bob", true);
	std::cout << "bob view   -> " << pool.auditView(bob) << "\n";

	std::cout << "stale alice handle now sees -> " << pool.auditView(alice)
		<< "\n";
	std::cout << "second release attempt -> "
		<< (pool.release(alice) ? "unexpected-success" : "blocked")
		<< "\n";
}

