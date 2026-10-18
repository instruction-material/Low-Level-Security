# Trait-pipeline reference observations

## CORE
audit accepts S: RowSource; Report labels borrow source rows. MemoryRows owns strings; BorrowedRows is an independent local implementation. Report container ownership does not turn its labels into independent strings. Keep actual local commands and an independent regression with this reasoning.

## WORKFLOW
For alpha=7, bad, omega=17, the starter pulls 3 rows before parsing; the reference pulls 2 and returns only RowError at index 2. try_fold uses ? to stop fallible work. No partial Report is returned, but the source's two pulls are already observed and are not rolled back.

## CHOICE
all_records maps each input to a Result and collects the outer Vec. It retains success/error/success and consumes all 3 rows. Collecting into Result<Vec<_>, _> or discarding Err with filter_map changes the contract. Validate an alternate implementation's order and lifetime behavior with synthetic rows.

## CHALLENGE
Both roles refuse missing-method with E0046 and mutate-live-iterator with E0502. alternate-source refuses with E0308 only in the starter; the reference prints count=2 total=12. report-after-owner-drop prints alpha only in the owned starter; the borrowed reference refuses with E0505. mutation-after-last-use prints rows=2 in both. Record actual compiler output before comparing.

## LIMITS
The trait checks a method/type shape, not finiteness, ordering, business correctness or arbitrary side-effect behavior. CLI input is capped at 16 rows. The library documents a finite data source; the total uses u128 for this u16/host-sized sequence case. Neither tests nor this counter certify production resource policy, authentication or dynamic plugin compatibility.
