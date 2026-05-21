#include <stdio.h>
#include <string.h>

typedef struct {
	char label[32];
	int value;
} Record;

int summarize_records(const Record *records, int count) {
	int total = 0;
	for (int i = 0; i < count; i++) {
		// TODO: fold the current record into the total in a safer, clearer way.
		(void)records;
	}
	return total;
}

int main(void) {
	Record records[] = {
		{"alpha", 4},
		{"beta", 9},
		{"gamma", 15},
	};
	printf("summary=%d\n", summarize_records(records, 3));
	return 0;
}
