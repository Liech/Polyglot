cmake_minimum_required(VERSION 3.24...4.0.2)

project(Polyglot)

option(POLYGLOT_ENABLE_PYTHON "Polyglot Python" ON)
option(POLYGLOT_ENABLE_LUA "Polyglot Lua" ON)
option(BUILD_TESTS "Build tests" ON)
set(POLYGLOT_PYTHON_EXTENSIONS "numpy" CACHE STRING "Space-separated list of pip packages")
set(POLYGLOT_LUA_EXTENSIONS "kikito/inspect.lua" CACHE STRING "Space-separated list of GitHub repositories (user/repo)")

############################################################################

find_package(nlohmann_json REQUIRED)

if(BUILD_TESTS)
    find_package(Catch2 CONFIG REQUIRED)
endif()

if(POLYGLOT_ENABLE_LUA)
    find_package(Lua REQUIRED)
endif()

if(POLYGLOT_ENABLE_PYTHON)
    find_package(Python3 REQUIRED COMPONENTS Interpreter Development.Embed)
    find_package(pybind11 CONFIG REQUIRED)
endif()

############################################################################
############################################################################
############################################################################

set(Lua_Files
    "Source/Polyglot/Lua/LuaEngine.h"
    "Source/Polyglot/Lua/LuaEngine.cpp"
    "Source/Polyglot/Lua/Conversion.h"
    "Source/Polyglot/Lua/Conversion.cpp"
)
source_group("Lua" FILES ${Lua_Files})

set(Python_Files
    "Source/Polyglot/Python/PythonEngine.h"
    "Source/Polyglot/Python/PythonEngine.cpp"
    "Source/Polyglot/Python/Conversion.h"
    "Source/Polyglot/Python/Conversion.cpp"
)
source_group("Python" FILES ${Python_Files})

set(main_Files
    "Source/Polyglot/Node.cpp"
    "Source/Polyglot/Node.h"
    "Source/Polyglot/Engine.cpp"
    "Source/Polyglot/Engine.h"
    "Source/Polyglot/testmain.cpp"
)
source_group("" FILES ${main_Files})

set(ALL_FILES
    ${main_Files}
)

if(POLYGLOT_ENABLE_LUA)
    list(APPEND ALL_FILES ${Lua_Files})
endif()

if(POLYGLOT_ENABLE_PYTHON)
    list(APPEND ALL_FILES ${Python_Files})
endif()

############################################################################
############################################################################
############################################################################

add_library(PolyglotDependencies INTERFACE)

add_library(Polyglot SHARED ${ALL_FILES})

set_property(TARGET Polyglot PROPERTY CXX_STANDARD 23)
set_property(TARGET Polyglot PROPERTY MSVC_DEBUG_INFORMATION_FORMAT Embedded)

target_link_libraries(PolyglotDependencies INTERFACE
    nlohmann_json::nlohmann_json
)
target_include_directories(PolyglotDependencies INTERFACE 
    "${CMAKE_CURRENT_SOURCE_DIR}/Source"
)
if(POLYGLOT_ENABLE_LUA)
    target_link_libraries(PolyglotDependencies INTERFACE ${LUA_LIBRARIES})
    target_include_directories(PolyglotDependencies INTERFACE ${LUA_INCLUDE_DIR})
endif()
if(POLYGLOT_ENABLE_PYTHON)
    target_link_libraries(PolyglotDependencies INTERFACE
        Python3::Python
        pybind11::module
    )
    target_include_directories(PolyglotDependencies INTERFACE ${Python3_INCLUDE_DIRS})
endif()

target_link_libraries(Polyglot PRIVATE PolyglotDependencies)
target_include_directories(Polyglot PUBLIC 
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/Source>
    $<INSTALL_INTERFACE:include>
)

set_target_properties(Polyglot PROPERTIES 
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin/$<CONFIG>"
)
target_compile_definitions(Polyglot PRIVATE
    $<$<CONFIG:Debug>:DEBUG>
)

if(BUILD_TESTS)
    add_executable(PolyglotTest ${ALL_FILES})
    target_compile_definitions(PolyglotTest PRIVATE -DISTESTPROJECT=1)

    set_property(TARGET PolyglotTest PROPERTY CXX_STANDARD 23)
    set_property(TARGET PolyglotTest PROPERTY MSVC_DEBUG_INFORMATION_FORMAT Embedded)

    target_link_libraries(PolyglotTest PRIVATE PolyglotDependencies Catch2::Catch2WithMain)

    set_target_properties(PolyglotTest PROPERTIES 
        RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/Test/$<CONFIG>"
    )
    target_compile_definitions(PolyglotTest PRIVATE
        $<$<CONFIG:Debug>:DEBUG>
    )
endif()

############################################################################
if(POLYGLOT_ENABLE_PYTHON)
    set(PYTHON_EXT_ARGS ${POLYGLOT_PYTHON_EXTENSIONS})
    set(PYTHON_EXECUTABLE ${Python3_EXECUTABLE})
    get_filename_component(PYTHON_ROOT "${Python3_EXECUTABLE}" DIRECTORY)

    add_custom_command(
        TARGET Polyglot POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E env PYTHON_ROOT="${PYTHON_ROOT}" 
                ${PYTHON_EXECUTABLE} "${CMAKE_CURRENT_SOURCE_DIR}/cmake/sync_python.py" 
                "${PYTHON_ROOT}" "$<TARGET_FILE_DIR:Polyglot>/python" ${PYTHON_EXT_ARGS}
        COMMENT "Syncing Python environment and installing extensions"
        VERBATIM
    )
    if(BUILD_TESTS)
        add_custom_command(
            TARGET PolyglotTest POST_BUILD
            COMMAND ${CMAKE_COMMAND} -E env PYTHON_ROOT="${PYTHON_ROOT}" 
                    ${PYTHON_EXECUTABLE} "${CMAKE_CURRENT_SOURCE_DIR}/cmake/sync_python.py" 
                    "${PYTHON_ROOT}" "$<TARGET_FILE_DIR:PolyglotTest>/python" ${PYTHON_EXT_ARGS}
            COMMENT "Syncing Python environment and installing extensions"
            VERBATIM
        )
    endif()
endif()

if(POLYGLOT_ENABLE_LUA)
    set(LUA_EXT_ARGS ${POLYGLOT_LUA_EXTENSIONS})

    add_custom_command(
        TARGET Polyglot POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
                "${CMAKE_CURRENT_SOURCE_DIR}/cmake/sync_lua.py" 
                "$<TARGET_FILE_DIR:Polyglot>/lua/sync_lua.py"
        COMMAND ${Python3_EXECUTABLE} "${CMAKE_CURRENT_SOURCE_DIR}/cmake/sync_lua.py" 
                "$<TARGET_FILE_DIR:Polyglot>/lua/modules" --allow-offline ${LUA_EXT_ARGS}
        COMMENT "Syncing Lua environment and installing extensions"
        VERBATIM
    )
    if(BUILD_TESTS)
        add_custom_command(
            TARGET PolyglotTest POST_BUILD
            COMMAND ${CMAKE_COMMAND} -E copy_if_different
                    "${CMAKE_CURRENT_SOURCE_DIR}/cmake/sync_lua.py" 
                    "$<TARGET_FILE_DIR:PolyglotTest>/lua/sync_lua.py"
            COMMAND ${Python3_EXECUTABLE} "${CMAKE_CURRENT_SOURCE_DIR}/cmake/sync_lua.py" 
                    "$<TARGET_FILE_DIR:PolyglotTest>/lua/modules" --allow-offline ${LUA_EXT_ARGS}
            COMMENT "Syncing Lua environment and installing extensions"
            VERBATIM
        )
    endif()
endif()

############################################################################
# Install & Export
############################################################################

install(TARGETS Polyglot EXPORT PolyglotTargets
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
    RUNTIME DESTINATION bin
)

install(DIRECTORY Source/ DESTINATION include FILES_MATCHING PATTERN "*.h")

install(EXPORT PolyglotTargets
    FILE PolyglotTargets.cmake
    NAMESPACE Polyglot::
    DESTINATION share/polyglot
)

install(FILES "cmake/sync_lua.py" "cmake/sync_python.py" DESTINATION share/polyglot)

file(WRITE "${CMAKE_CURRENT_BINARY_DIR}/PolyglotConfig.cmake"
"include(CMakeFindDependencyMacro)\n"
"find_dependency(nlohmann_json CONFIG)\n"
"find_dependency(Lua)\n"
"find_dependency(Python3 COMPONENTS Interpreter Development.Embed)\n"
"find_dependency(pybind11 CONFIG)\n"
"include(\"\${CMAKE_CURRENT_LIST_DIR}/PolyglotTargets.cmake\")\n"
)
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/PolyglotConfig.cmake" DESTINATION share/polyglot)
