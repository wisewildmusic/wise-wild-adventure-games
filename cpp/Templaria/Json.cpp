#include "Json.hpp"

#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <stdexcept>

namespace json {

/// A recursive-descent parser: one function for each kind of value, calling each other as they nest.
class Parser {
public:
    explicit Parser(std::string_view text) : text_(text) {}

    Value document() {
        if (text_.starts_with("\xEF\xBB\xBF")) at_ = 3;  // a UTF-8 byte order mark, which PowerShell's pipes add
        Value value = parse_value();
        skip_space();
        if (at_ != text_.size()) fail("text after the value");
        return value;
    }

private:
    [[noreturn]] void fail(const std::string& why) const {
        throw std::runtime_error("bad JSON at " + std::to_string(at_) + ": " + why);
    }

    void skip_space() {
        while (at_ < text_.size() && (text_[at_] == ' ' || text_[at_] == '\t' || text_[at_] == '\n' || text_[at_] == '\r'))
            ++at_;
    }

    char peek() {
        skip_space();
        if (at_ == text_.size()) fail("unexpected end");
        return text_[at_];
    }

    bool accept(std::string_view word) {
        if (text_.substr(at_, word.size()) != word) return false;
        at_ += word.size();
        return true;
    }

    Value parse_value() {
        Value value;
        switch (peek()) {
            case '{': parse_object(value); break;
            case '[': parse_array(value); break;
            case '"':
                value.kind_ = Value::Kind::String;
                value.text_ = parse_string();
                break;
            case 't':
            case 'f':
                value.kind_ = Value::Kind::Boolean;
                value.boolean_ = text_[at_] == 't';
                if (!accept(value.boolean_ ? "true" : "false")) fail("expected true or false");
                break;
            case 'n':
                if (!accept("null")) fail("expected null");
                break;
            default: parse_number(value);
        }
        return value;
    }

    void parse_object(Value& value) {
        value.kind_ = Value::Kind::Object;
        ++at_;
        if (peek() == '}') {
            ++at_;
            return;
        }
        while (true) {
            if (peek() != '"') fail("expected a name");
            value.names_.push_back(parse_string());
            if (peek() != ':') fail("expected :");
            ++at_;
            value.items_.push_back(parse_value());
            const char next = peek();
            ++at_;
            if (next == '}') return;
            if (next != ',') fail("expected , or }");
        }
    }

    void parse_array(Value& value) {
        value.kind_ = Value::Kind::Array;
        ++at_;
        if (peek() == ']') {
            ++at_;
            return;
        }
        while (true) {
            value.items_.push_back(parse_value());
            const char next = peek();
            ++at_;
            if (next == ']') return;
            if (next != ',') fail("expected , or ]");
        }
    }

    void parse_number(Value& value) {
        const std::size_t start = at_;
        if (at_ < text_.size() && text_[at_] == '-') ++at_;
        while (at_ < text_.size() && text_[at_] >= '0' && text_[at_] <= '9') ++at_;
        if (at_ == start || (at_ == start + 1 && text_[start] == '-')) fail("expected a value");
        // (The website only ever sends whole numbers, so a fraction or an exponent is a mistake.)
        if (at_ < text_.size() && (text_[at_] == '.' || text_[at_] == 'e' || text_[at_] == 'E')) fail("expected a whole number");
        value.kind_ = Value::Kind::Number;
        value.number_ = std::stoll(std::string(text_.substr(start, at_ - start)));
    }

    std::uint32_t parse_hex4() {
        if (at_ + 4 > text_.size()) fail("short \\u escape");
        std::uint32_t code = 0;
        for (int i = 0; i < 4; ++i) {
            const char c = text_[at_++];
            code <<= 4;
            if (c >= '0' && c <= '9') code |= c - '0';
            else if (c >= 'a' && c <= 'f') code |= c - 'a' + 10;
            else if (c >= 'A' && c <= 'F') code |= c - 'A' + 10;
            else fail("bad \\u escape");
        }
        return code;
    }

    static void append_utf8(std::string& out, std::uint32_t code) {
        if (code < 0x80) {
            out += static_cast<char>(code);
        } else if (code < 0x800) {
            out += static_cast<char>(0xC0 | (code >> 6));
            out += static_cast<char>(0x80 | (code & 0x3F));
        } else if (code < 0x10000) {
            out += static_cast<char>(0xE0 | (code >> 12));
            out += static_cast<char>(0x80 | ((code >> 6) & 0x3F));
            out += static_cast<char>(0x80 | (code & 0x3F));
        } else {
            out += static_cast<char>(0xF0 | (code >> 18));
            out += static_cast<char>(0x80 | ((code >> 12) & 0x3F));
            out += static_cast<char>(0x80 | ((code >> 6) & 0x3F));
            out += static_cast<char>(0x80 | (code & 0x3F));
        }
    }

    std::string parse_string() {
        std::string out;
        ++at_;  // the opening quote
        while (true) {
            if (at_ == text_.size()) fail("unfinished string");
            const char c = text_[at_++];
            if (c == '"') return out;
            if (c != '\\') {
                out += c;
                continue;
            }
            if (at_ == text_.size()) fail("unfinished escape");
            const char escape = text_[at_++];
            switch (escape) {
                case '"': case '\\': case '/': out += escape; break;
                case 'b': out += '\b'; break;
                case 'f': out += '\f'; break;
                case 'n': out += '\n'; break;
                case 'r': out += '\r'; break;
                case 't': out += '\t'; break;
                case 'u': {
                    std::uint32_t code = parse_hex4();
                    if (code >= 0xD800 && code < 0xDC00) {  // a surrogate pair: two escapes, one character
                        if (!accept("\\u")) fail("lone surrogate");
                        code = 0x10000 + ((code - 0xD800) << 10) + (parse_hex4() - 0xDC00);
                    }
                    append_utf8(out, code);
                    break;
                }
                default: fail("bad escape");
            }
        }
    }

    std::string_view text_;
    std::size_t at_ = 0;
};

Value Value::parse(std::string_view text) { return Parser(text).document(); }

bool Value::as_bool() const {
    if (kind_ != Kind::Boolean) throw std::runtime_error("expected true or false");
    return boolean_;
}

long long Value::as_integer() const {
    if (kind_ != Kind::Number) throw std::runtime_error("expected a number");
    return number_;
}

const std::string& Value::as_string() const {
    if (kind_ != Kind::String) throw std::runtime_error("expected a string");
    return text_;
}

const std::vector<Value>& Value::items() const {
    if (kind_ != Kind::Array) throw std::runtime_error("expected an array");
    return items_;
}

const Value& Value::at(std::string_view name) const {
    if (kind_ != Kind::Object) throw std::runtime_error("expected an object");
    const auto found = std::find(names_.begin(), names_.end(), name);
    if (found == names_.end()) throw std::runtime_error("missing " + std::string(name));
    return items_[found - names_.begin()];
}

void Writer::separate() {
    if (needs_comma_) out_ << ',';
}

void Writer::quoted(std::string_view text) {
    out_ << '"';
    for (const char c : text) {
        switch (c) {
            case '"': out_ << "\\\""; break;
            case '\\': out_ << "\\\\"; break;
            case '\n': out_ << "\\n"; break;
            case '\r': out_ << "\\r"; break;
            case '\t': out_ << "\\t"; break;
            default:
                if (static_cast<unsigned char>(c) < 0x20) {
                    char escape[7];
                    std::snprintf(escape, sizeof escape, "\\u%04x", static_cast<unsigned>(c));
                    out_ << escape;
                } else {
                    out_ << c;  // anything else, including UTF-8, goes as it is
                }
        }
    }
    out_ << '"';
}

Writer& Writer::begin_object() {
    separate();
    out_ << '{';
    needs_comma_ = false;
    return *this;
}

Writer& Writer::end_object() {
    out_ << '}';
    needs_comma_ = true;
    return *this;
}

Writer& Writer::begin_array() {
    separate();
    out_ << '[';
    needs_comma_ = false;
    return *this;
}

Writer& Writer::end_array() {
    out_ << ']';
    needs_comma_ = true;
    return *this;
}

Writer& Writer::key(std::string_view name) {
    separate();
    quoted(name);
    out_ << ':';
    needs_comma_ = false;
    return *this;
}

Writer& Writer::string(std::string_view text) {
    separate();
    quoted(text);
    needs_comma_ = true;
    return *this;
}

Writer& Writer::optional_string(const std::optional<std::string>& text) {
    return text ? string(*text) : null();
}

Writer& Writer::number(long long value) {
    separate();
    out_ << value;
    needs_comma_ = true;
    return *this;
}

Writer& Writer::boolean(bool value) {
    separate();
    out_ << (value ? "true" : "false");
    needs_comma_ = true;
    return *this;
}

Writer& Writer::null() {
    separate();
    out_ << "null";
    needs_comma_ = true;
    return *this;
}

}  // namespace json
