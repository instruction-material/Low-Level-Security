cmake_minimum_required(VERSION 3.20)
project(Low_Level_Security CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

option(LLS_ENABLE_SANITIZERS "Enable address and UB sanitizers" ON)

add_compile_options(-Wall -Wextra -Wpedantic -g)

if(LLS_ENABLE_SANITIZERS AND CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU")
	add_compile_options(-fsanitize=address,undefined -fno-omit-frame-pointer)
	add_link_options(-fsanitize=address,undefined -fno-omit-frame-pointer)
endif()

function(lls_add_lab target source_file)
	add_executable(${target} "${source_file}")
endfunction()

lls_add_lab(
	lls1_memory_map_starter
	"LLS1-Memory-Map-Inspector/starter/main.cpp"
)
lls_add_lab(
	lls1_memory_map_solution
	"LLS1-Memory-Map-Inspector/solution/main.cpp"
)
lls_add_lab(
	lls2_bounds_checked_copy_starter
	"LLS2-Bounds-Checked-Copy/starter/main.cpp"
)
lls_add_lab(
	lls2_bounds_checked_copy_solution
	"LLS2-Bounds-Checked-Copy/solution/main.cpp"
)
lls_add_lab(
	lls3_length_prefixed_parser_starter
	"LLS3-Length-Prefixed-Parser/starter/main.cpp"
)
lls_add_lab(
	lls3_length_prefixed_parser_solution
	"LLS3-Length-Prefixed-Parser/solution/main.cpp"
)
lls_add_lab(
	lls4_ring_buffer_guards_starter
	"LLS4-Ring-Buffer-Guards/starter/main.cpp"
)
lls_add_lab(
	lls4_ring_buffer_guards_solution
	"LLS4-Ring-Buffer-Guards/solution/main.cpp"
)
lls_add_lab(
	lls5_mini_fuzzer_starter
	"LLS5-Mini-Fuzzer/starter/main.cpp"
)
lls_add_lab(
	lls5_mini_fuzzer_solution
	"LLS5-Mini-Fuzzer/solution/main.cpp"
)
lls_add_lab(
	lls6_capstone_audit_starter
	"LLS6-Capstone-Audit/starter/main.cpp"
)
lls_add_lab(
	lls6_capstone_audit_solution
	"LLS6-Capstone-Audit/solution/main.cpp"
)
lls_add_lab(
	lls13_crash_classification_starter
	"LLS13-Crash-Classification-Lab/starter/main.cpp"
)
lls_add_lab(
	lls13_crash_classification_solution
	"LLS13-Crash-Classification-Lab/solution/main.cpp"
)
lls_add_lab(
	lls14_stack_frame_corruption_starter
	"LLS14-Stack-Frame-Corruption-Demo-and-Fix/starter/main.cpp"
)
lls_add_lab(
	lls14_stack_frame_corruption_solution
	"LLS14-Stack-Frame-Corruption-Demo-and-Fix/solution/main.cpp"
)
lls_add_lab(
	lls15_heap_lifetime_audit_starter
	"LLS15-Heap-Lifetime-Audit/starter/main.cpp"
)
lls_add_lab(
	lls15_heap_lifetime_audit_solution
	"LLS15-Heap-Lifetime-Audit/solution/main.cpp"
)
lls_add_lab(
	lls16_mitigation_matrix_starter
	"LLS16-Mitigation-Comparison-Build-Matrix/starter/main.cpp"
)
lls_add_lab(
	lls16_mitigation_matrix_solution
	"LLS16-Mitigation-Comparison-Build-Matrix/solution/main.cpp"
)
lls_add_lab(
	lls17_disclosure_triage_starter
	"LLS17-Disclosure-and-Triage-Report/starter/main.cpp"
)
lls_add_lab(
	lls17_disclosure_triage_solution
	"LLS17-Disclosure-and-Triage-Report/solution/main.cpp"
)
lls_add_lab(
	lls18_hardening_capstone_starter
	"LLS18-Exploit-Informed-Hardening-Capstone/starter/main.cpp"
)
lls_add_lab(
	lls18_hardening_capstone_solution
	"LLS18-Exploit-Informed-Hardening-Capstone/solution/main.cpp"
)

