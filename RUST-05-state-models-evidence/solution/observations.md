# Review-state reference notes

## CORE
The valid shapes are draft 0/0/None, reviewed 1/0/Some(valid name), and published 1/1/Some(valid name). State is private and carries Reviewer in each payload-bearing variant. A draft can review/reset, a reviewed state can publish/reset, and a published state accepts none of the three events. A failed event preserves the previous value.

## WORKFLOW
Legacy raw flags still represent invalid data and are validated at import. Shape errors precede name errors. Snapshot round trips preserve valid data. Reset drops the previous reviewer, so a later review carries the new name. Successful earlier events remain applied if a later event fails.

## CHOICE
Reviewer validates 1..32 Unicode scalars, trims only for comparison, rejects controls and reserved dash, and preserves valid input exactly. Seventeen é scalars occupy 34 UTF-8 bytes; the unfinished starter refuses them, while the reference accepts them. Combining marks count separately from their base scalar. No normalization, grapheme segmentation or identity verification is claimed.

## CHALLENGE
The omitted Phase variant receives E0004. The exhaustive counterpart prints published. The raw Session field constructor compiles only for the starter, whose phase method then refuses the invalid legacy shape. Those fields do not exist on the reference Session and receive E0560. Actual command observations and additional independent cases must still be recorded.

## LIMITS
The enum removes inconsistent internal flag combinations. Domain rules are implemented by apply and still require tests. Legacy input remains untrusted raw data. This local model is neither a real publishing system nor an authorization mechanism.
