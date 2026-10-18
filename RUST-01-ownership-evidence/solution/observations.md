# Ownership reference observations

## OWNER LEDGER
The String and Vec values move into make_packet; the returned Packet owns both.
clone creates a second Packet whose String and Vec own independent data. relay
moves its Packet parameter back to its caller. add_marker takes the Packet,
destructures it into owned fields, moves bytes through append_marker, then
rebuilds a complete Packet. borrowed_label uses a shared borrow; that inspection
does not take ownership. The final relay moves updated into returned. The u32
assignment copies 7, so both integer bindings remain usable.

## PREDICT
Default data is label packet-42 and bytes [3, 1, 4]. The cloned snapshot retains
those values when the moved branch gains 9. The empty-vector branch starts with
[] and ends with [9]. Changed labels are preserved as text, including Unicode.
Normal program stderr is empty and status is zero. Invalid vector mode, extra
arguments, or a non-UTF-8 label are refused with status 64 before trace output.

## CHECKS
Retain actual local versions, hashes and output; a reference explanation is not
a substitute for running the selected role. Four baseline unit tests cover
moves through helpers, independent cloned fields, empty fields and borrowing
before a later move. Passing them does not complete the observation worksheet.

## SCOPE
The sequence is inner-second, inner-first, explicit, after-explicit-drop, outer.
The inner local tags drop in reverse declaration order when their block ends.
std::mem::drop consumes explicit before the next println. The outer tag drops
when scope_trace returns. ScopeTag logs its own destructor; it does not log all
String/Vec destruction, allocator activity, object addresses or code generation.
No equivalent cost claim follows from this sequence.

## CHOICE
A useful independent-clone test changes both fields in the clone and checks all
fields in both results. Merely asserting that the clone initially equals the
original does not check later independence. The snapshot behavior needs its own
owned data; a read-only description alone can borrow and need not clone.

## CHALLENGE
use-after-move and use-after-drop are expected E0382 compile refusals. consume
and drop take the String by value, so the later println cannot borrow that old
binding. returned-owner passes ownership back; last-use-before-drop observes the
value first and consumes it afterward. copy-owned is expected E0204 because its
String field is not Copy. clone-owned explicitly clones, then demonstrates that
editing the clone leaves the first value intact. None of the rejected programs
has an observed runtime behavior. Compare actual diagnostic versions and spans.

## LIMITS
This lab illustrates checked ownership and explicit duplication in safe Rust.
It does not establish resource bounds, authorization correctness, constant cost,
or the absence of logic bugs. A clone can allocate; a moved value does not by
itself reveal actual machine-level data movement. Native observations support
only the commands, toolchain and inputs that were actually recorded.
