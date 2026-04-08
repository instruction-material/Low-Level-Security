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

add_executable(
	lls1_memory_map_starter
	"LLS1-Memory-Map-Inspector/starter/main.cpp"
)
add_executable(
	lls1_memory_map_solution
	"LLS1-Memory-Map-Inspector/solution/main.cpp"
)
add_executable(
	lls2_bounds_checked_copy_starter
	"LLS2-Bounds-Checked-Copy/starter/main.cpp"
)
add_executable(
	lls2_bounds_checked_copy_solution
	"LLS2-Bounds-Checked-Copy/solution/main.cpp"
)
add_executable(
	lls3_length_prefixed_parser_starter
	"LLS3-Length-Prefixed-Parser/starter/main.cpp"
)
add_executable(
	lls3_length_prefixed_parser_solution
	"LLS3-Length-Prefixed-Parser/solution/main.cpp"
)
add_executable(
	lls4_ring_buffer_guards_starter
	"LLS4-Ring-Buffer-Guards/starter/main.cpp"
)
add_executable(
	lls4_ring_buffer_guards_solution
	"LLS4-Ring-Buffer-Guards/solution/main.cpp"
)
add_executable(
	lls5_mini_fuzzer_starter
	"LLS5-Mini-Fuzzer/starter/main.cpp"
)
add_executable(
	lls5_mini_fuzzer_solution
	"LLS5-Mini-Fuzzer/solution/main.cpp"
)

