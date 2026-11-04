#pragma once

#include <coroutine>
#include <exception>
#include <iterator>
#include <optional>
#include <utility>

namespace templaria {

/// A sequence a coroutine hands out one item at a time. co_yield gives the caller an item and freezes
/// the function, locals and all, until the caller asks for the next one. This is what stands in for
/// the console game's input(): see Story.cpp.
///
/// C++20 brought the language part (co_yield) but left this library part to us. C++23 has
/// std::generator, but writing it out keeps the game building on any C++20 compiler.
template <typename T>
class Generator {
public:
    struct promise_type {
        std::optional<T> current;
        std::exception_ptr failure;

        Generator get_return_object() {
            return Generator(std::coroutine_handle<promise_type>::from_promise(*this));
        }
        std::suspend_always initial_suspend() noexcept { return {}; }  // nothing runs until it's asked
        std::suspend_always final_suspend() noexcept { return {}; }
        std::suspend_always yield_value(T item) {
            current = std::move(item);
            return {};
        }
        void return_void() noexcept {}
        void unhandled_exception() noexcept { failure = std::current_exception(); }
    };

    // A Generator owns its coroutine's frame, so it can be moved but never copied (the rule of five).
    Generator(Generator&& other) noexcept : coroutine_(std::exchange(other.coroutine_, {})) {}
    Generator& operator=(Generator&& other) noexcept {
        if (this != &other) {
            if (coroutine_) coroutine_.destroy();
            coroutine_ = std::exchange(other.coroutine_, {});
        }
        return *this;
    }
    Generator(const Generator&) = delete;
    Generator& operator=(const Generator&) = delete;
    ~Generator() {
        if (coroutine_) coroutine_.destroy();
    }

    /// Runs on to the next co_yield and returns its item, or nothing once the function has ended.
    std::optional<T> next() {
        auto& promise = coroutine_.promise();
        promise.current.reset();
        if (!coroutine_.done()) coroutine_.resume();
        if (promise.failure) std::rethrow_exception(std::exchange(promise.failure, nullptr));
        return std::move(promise.current);
    }

    /// Just enough of an iterator for a range-based for, so a part of the story can walk through a
    /// smaller part:  for (auto& prompt : smaller_part(q)) co_yield prompt;
    class Iterator {
    public:
        explicit Iterator(Generator& source) : source_(&source), item_(source.next()) {}
        T& operator*() { return *item_; }
        Iterator& operator++() {
            item_ = source_->next();
            return *this;
        }
        bool operator!=(std::default_sentinel_t) const { return item_.has_value(); }

    private:
        Generator* source_;
        std::optional<T> item_;
    };
    Iterator begin() { return Iterator(*this); }
    std::default_sentinel_t end() const { return std::default_sentinel; }

private:
    explicit Generator(std::coroutine_handle<promise_type> coroutine) : coroutine_(coroutine) {}

    std::coroutine_handle<promise_type> coroutine_;
};

}  // namespace templaria
