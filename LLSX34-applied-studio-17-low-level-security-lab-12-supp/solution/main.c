#include <stdio.h>
#include <string.h>

typedef struct {
	char label[32];
	int value;
} Record;

int summarize_records(const Record *records, int count) {
	int total = 0;
	for (int i = 0; i < count; i++) {
		if (strncmp(records[i].label, "beta", sizeof(records[i].label)) == 0) {
			total += records[i].value * 2;
		} else {
			total += records[i].value;
		}
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
