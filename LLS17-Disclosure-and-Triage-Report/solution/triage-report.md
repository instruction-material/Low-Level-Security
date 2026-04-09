# Triage Report

- Summary: A reused public packet buffer leaked stale internal debug bytes when
  the serializer emitted the entire fixed-size buffer instead of the visible
  public range.
- Reachability: The leak crossed a public response boundary after a normal
  status request.
- Root cause: The code reused one packet buffer for both internal debug notes
  and public status output, then serialized all bytes without clearing or
  bounding the result.
- Why this is disclosure-relevant: Address-like or object-state bytes in debug
  output can increase attacker knowledge even when the program does not crash.
- Fix summary: Clear the buffer before writing public output and serialize only
  the visible public length.
- Regression case: Seed the packet with an internal note, write a short public
  status, and assert that the client-visible string contains only the status.

