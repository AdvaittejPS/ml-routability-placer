cmake_minimum_required(VERSION 3.10)
project(ml_placer LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(placer_cli
    src/main.cpp
    src/placer.cpp
)
find_package(nlohmann_json QUIET)
if (nlohmann_json_FOUND)
  target_link_libraries(placer_cli PRIVATE nlohmann_json::nlohmann_json)
endif()
