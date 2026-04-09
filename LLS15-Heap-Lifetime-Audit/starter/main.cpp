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
};

class SessionPool {
public:
	SessionHandle create(std::string owner, bool privileged) {
		for (std::size_t index = 0; index < slots.size(); ++index) {
			if (!slots[index].has_value()) {
				slots[index] = Session{ std::move(owner), privileged };
				return SessionHandle{ index };
			}
		}

		slots.push_back(Session{ std::move(owner), privileged });
		return SessionHandle{ slots.size() - 1 };
	}

	void release(const SessionHandle& handle) {
		if (handle.slot < slots.size()) {
			slots[handle.slot].reset();
		}
	}

	std::string auditView(const SessionHandle& handle) const {
		if (handle.slot >= slots.size() || !slots[handle.slot].has_value()) {
			return "<invalid>";
		}

		const Session& session = *slots[handle.slot];
		return session.owner + (session.privileged ? " [priv]" : " [user]");
	}

private:
	std::vector<std::optional<Session>> slots;
};

int main() {
	SessionPool pool;

	const SessionHandle alice = pool.create("alice", false);
	std::cout << "alice view -> " << pool.auditView(alice) << "\n";

	pool.release(alice);
	const SessionHandle bob = pool.create("bob", true);
	std::cout << "bob view   -> " << pool.auditView(bob) << "\n";

	std::cout << "stale alice handle now sees -> " << pool.auditView(alice)
		<< "\n";
	std::cout << "TODO: add generation-aware validation so stale handles stop working.\n";
}

