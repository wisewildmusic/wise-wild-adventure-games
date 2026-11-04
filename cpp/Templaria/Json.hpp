#pragma once

#include <optional>
#include <ostream>
#include <string>
#include <string_view>
#include <vector>

// The game talks JSON with the website. C++ has no JSON in its standard library, and adding a library
// for one small request and one answer isn't worth it, so here are a small reader and writer.
namespace json {

/// A JSON value read from text. Parsing, and asking a value for the wrong kind of thing, throw
/// std::runtime_error.
class Value {
public:
    static Value parse(std::string_view text);

    bool is_null() const { return kind_ == Kind::Null; }
    bool as_bool() const;
    long long as_integer() const;
    const std::string& as_string() const;
    const std::vector<Value>& items() const;       // an array's items
    const Value& at(std::string_view name) const;  // an object's member, which must be there

private:
    enum class Kind { Null, Boolean, Number, String, Array, Object };
    friend class Parser;

    Kind kind_ = Kind::Null;
    bool boolean_ = false;
    long long number_ = 0;
    std::string text_;
    std::vector<Value> items_;         // an array's items, or an object's values...
    std::vector<std::string> names_;   // ...and, for an object, the name of each
};

/// Writes JSON text, putting in the commas. The methods have different names on purpose: as overloads
/// of one name, writer.value("text") would pick value(bool) over value(std::string_view), because a
/// string literal turns into a pointer and a pointer into a bool. (The final boss asks about this.)
class Writer {
public:
    explicit Writer(std::ostream& out) : out_(out) {}

    Writer& begin_object();
    Writer& end_object();
    Writer& begin_array();
    Writer& end_array();
    Writer& key(std::string_view name);
    Writer& string(std::string_view text);
    Writer& optional_string(const std::optional<std::string>& text);  // null when there's none
    Writer& number(long long value);
    Writer& boolean(bool value);
    Writer& null();

private:
    void separate();
    void quoted(std::string_view text);

    std::ostream& out_;
    bool needs_comma_ = false;
};

}  // namespace json
