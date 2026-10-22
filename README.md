# todo for v1

 * make sure it builds on linux

# Polyglot

Single API for Python and Lua scripting. Extendable for any normal scripting language.

```cpp
void executeFile(const std::string& filename);
void executeString(const std::string& str);
Node getVar(const std::string& name);
void setVar(const std::string& name, const Node& value);
bool addExtension(const std::string& extensionName);
```

# One Interface, multiple engines

In this example the syntax of the query is the same for python and lua. Usually you need to provide the script in the desired language.

```cpp
void run(Engine& engine)
{
    engine.setVar("a", 10.0);
    engine.executeString("b = a + 5");
    Node result = engine.getVar("b");
    double numberResult = result;
}

LuaEngine lua;
PythonEngine py;
run(lua);
run(py);
```

# "Node" class and Lambdas

Node is an nlohmann::json compatible class, that additionally can store functions.

This works in both ways. Here is a way to call a c++ function from lua.

```cpp
    Polyglot::Lua::LuaEngine engine;
    std::function<Node(const Node& arg)> func = [](const Node& arg) -> Node { return static_cast<double>(arg) * 2.0; };
    engine.setVar("myCallback", func);
    engine.executeString("result = myCallback(21)");
    Node res = engine.getVar("result");
    int result = res;
```

And here one that calls lua from c++

```cpp
    Polyglot::Lua::LuaEngine engine;
    engine.executeString("my_func = function(x) return x * 2 end");
    auto fun = engine.getVar("my_func");
    Node result = fun(21.0);
    double result = res;
```

You also can leverage full nested json like structures.

```cpp
    Polyglot::Lua::LuaEngine engine;

    nlohmann::json table;
    table["a"] = 1.0;
    table["b"] = 2.0;

    engine.setVar("myTable", table);
    engine.executeString("sum = myTable.a + myTable.b");
    Node sum = engine.getVar("sum");
    double result = sum;
```

# Language Extensions

CMake cache variables configure packages installed during build time:

```cmake
set(POLYGLOT_PYTHON_EXTENSIONS "numpy" CACHE STRING "Space-separated list of pip packages")
set(POLYGLOT_LUA_EXTENSIONS "kikito/inspect.lua" CACHE STRING "Space-separated list of GitHub repositories (user/repo)")
```

Lua extensions use GitHub shortlinks (`user/repo`) to fetch pure Lua packages directly without requiring external C build tools.

You can also add extensions at runtime:

```cpp
Polyglot::Python::PythonEngine engine;
engine.addExtension("urlman");
engine.executeString("import urlman;");
```

```cpp
Polyglot::Lua::LuaEngine engine;
engine.addExtension("kikito/inspect.lua");
engine.executeString("inspect = require('inspect')");
```

# Installation

This project utilizes vcpkg and CMake for dependency management and building.

You need to specify a toolchain file in cmake.
```
 -DCMAKE_TOOLCHAIN_FILE=[path_to_vcpkg]/scripts/buildsystems/vcpkg.cmake
```
