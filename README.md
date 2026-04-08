# Low Level Security

This folder contains defensive low-level security labs for the site course.
The focus is understanding memory layout, input validation, bug hunting, and
safer systems programming habits.

These labs are intentionally local toy programs. They are for learning how to
find, explain, and fix bugs in code you control. They do not include exploit
payloads or offensive deployment workflows.

## Layout

- `LLS1-Memory-Map-Inspector`
- `LLS2-Bounds-Checked-Copy`
- `LLS3-Length-Prefixed-Parser`
- `LLS4-Ring-Buffer-Guards`
- `LLS5-Mini-Fuzzer`

Each lab contains:

- `starter/` for student work
- `solution/` for a reference implementation

## Build

From this directory:

```bash
cmake -S . -B build
cmake --build build
```

To keep the labs tool-friendly, the CMake project enables warnings and, on
Clang/GCC, address and undefined-behavior sanitizers by default.

