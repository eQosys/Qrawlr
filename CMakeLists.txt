cmake_minimum_required(VERSION 3.8)

project("qrawlr")

if (NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE "Release")
    set(CMAKE_BUILD_TYPE_RELEASE)

    set(CMAKE_CXX_FLAGS_RELEASE "-O3")
endif()

set(CMAKE_CXX_FLAGS "-Wall -Wextra")

add_subdirectory("libQrawlr")

add_executable(
    qrawlr
    "src/Qrawlr.cpp"
)

target_link_libraries(
    qrawlr
    libqrawlr
)

set_property(TARGET qrawlr PROPERTY CXX_STANDARD 17)