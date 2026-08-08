#include <stdio.h>
#include <string.h>

/*****************
*   CONSTANTS   *
*****************/

#define LABEL_CAPACITY 32U
#define BETA_MULTIPLIER 2
#define SAMPLE_RECORD_COUNT 3

/************
*   TYPES   *
************/

// Store one labeled integer record
struct record_t {
    char label[LABEL_CAPACITY];
    int value;
};

/*****************
*   FUNCTIONS   *
*****************/

/**
 * @brief Summarize records with a special beta weighting rule
 *
 * @param records Records to summarize
 *
 * @param count Number of records in the array
 *
 * @return Weighted record total
 */
int summarize_records(const struct record_t* records, int count) {
    int total = 0;

    // Process each record exactly once
    for (int record_index = 0; record_index < count; record_index++) {
        const struct record_t* current_record = &records[record_index];

        // Apply the beta-specific weighting rule
        if (strncmp(current_record->label, "beta",
                    sizeof(current_record->label)) == 0) {
            total += current_record->value * BETA_MULTIPLIER;
        }
        // Preserve the original value for all other labels
        else {
            total += current_record->value;
        }
    }

    return total;
}

/**
 * @brief Print the summary for the sample records
 *
 * @return Program exit status
 */
int main(void) {
    const struct record_t records[SAMPLE_RECORD_COUNT] = {
        {"alpha", 4},
        {"beta", 9},
        {"gamma", 15},
    };

    printf("summary=%d\n", summarize_records(records, SAMPLE_RECORD_COUNT));
    return 0;
}
