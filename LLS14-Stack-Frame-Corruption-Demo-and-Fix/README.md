# LLS14 Stack Frame Corruption Demo and Fix

Use a local toy frame model to show how unchecked writes can spill from a local
buffer into adjacent control data, then patch the copy rules.

## Goals

- understand the relationship between local buffers and nearby frame data
- see why unchecked lengths can become security-relevant
- compare an unsafe copy routine to a bounded defensive one

## Notes

- this lab uses a toy local frame layout for observation
- it is not for public deployment or offensive experimentation

