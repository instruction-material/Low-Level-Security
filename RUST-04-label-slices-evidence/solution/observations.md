# Label and slice observations

## CORE
The target keeps ASCII alphanumeric characters and dashes; the identity baseline is unfinished.

## LABEL CASES
packet-42! becomes packet-42. Non-ASCII letters, underscores, punctuation and controls are removed. Allowed empty output remains a valid String.

## PREDICT
a🦀bc has seven bytes and four scalars. Bytes1..5 and scalars1..2 select the crab; bytes2..3 is [159], but that interval is not valid str.

## CHECKS
The eight tests cover exact ASCII membership, default task distinction, valid windows, ordered errors, scalar/grapheme distinction, small-range enumeration and usize extremes. Actual command observations must be recorded separately.

## WINDOWS
The target returns &str and &[u8] tied to the input. get validates the selected range; an empty byte interval inside a multibyte scalar is still not a str boundary.

## CHOICE
char_indices maps scalar positions to byte boundaries. Chaining the final byte length permits the end position. Combining marks remain separate scalars; no grapheme segmentation is claimed.

## CHALLENGE
String indexing by usize fails E0277. Direct invalid byte, UTF-8 and reversed ranges compile and panic101. Checked examples return None; scalar nth returns Some('🦀'). These are distinct outcomes.

## LIMITS
The code uses safe Rust and bounded teaching fixtures. Filtering is not context-sensitive escaping; no timing or application-wide resource guarantee follows from these examples.
