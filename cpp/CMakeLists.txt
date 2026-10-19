cmake_minimum_required(VERSION 3.14)
project(ml_placer LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include(FetchContent)
FetchContent_Declare(
  nlohmann_json
  GIT_REPOSITORY https://github.com/nlohmann/json.git
  GIT_TAG v3.11.2
)
FetchContent_MakeAvailable(nlohmann_json)

add_executable(placer_cli
    src/main.cpp
    src/placer.cpp
)

target_link_libraries(placer_cli PRIVATE nlohmann_json::nlohmann_json)
