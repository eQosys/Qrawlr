cmake_minimum_required(VERSION 3.8)

project("libqrawlr")

if (NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE "Release")
    set(CMAKE_BUILD_TYPE_RELEASE)

    set(CMAKE_CXX_FLAGS_RELEASE "-O3")
endif()

set(CMAKE_CXX_FLAGS "-Wall -Wextra")

add_library(
    libqrawlr
    "src/Rule.cpp"
    "src/Grammar.cpp"
    "src/FileReader.cpp"
)

target_include_directories(
	libqrawlr PUBLIC
	"include/"
)

set_property(TARGET libqrawlr PROPERTY CXX_STANDARD 17)