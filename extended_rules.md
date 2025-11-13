# Extended Coding Rules and Best Practices

This document outlines a set of general coding rules, anti-patterns, and best practices to improve code quality, maintainability, and security.

## 1. Code Readability and Maintainability

- **Clear Naming:** Variable, function, and class names should be descriptive and unambiguous. Avoid abbreviations that are not widely understood (e.g., use `customer` instead of `cust`).
- **Consistent Formatting:** Adhere to a consistent code style (indentation, spacing, line breaks). Use a linter and formatter (like Black for Python, Prettier for JavaScript) to automate this.
- **Magic Numbers:** Avoid using "magic numbers" (unexplained numeric literals). Instead, define them as named constants.
- **Deeply Nested Code:** Avoid deep nesting of loops and conditional statements. Refactor using functions, methods, or guard clauses (`if ... return`). A good rule of thumb is to keep nesting to a maximum of 2-3 levels.
- **Large Functions/Classes:** Functions and classes should have a single, well-defined responsibility (Single Responsibility Principle). If a function or class is too long or does too many things, break it down.
- **Dead Code:** Remove commented-out or unreachable code to keep the codebase clean.

## 2. Anti-Patterns

- **God Object:** Avoid creating classes that know or do too much. These objects become bottlenecks and are difficult to maintain.
- **Spaghetti Code:** Code that has a complex and tangled control structure. Refactor to have clear, linear execution paths where possible.
- **Copy-Paste Programming:** Duplicating code is a sign that you need to create a reusable function or class.
- **Reinventing the Wheel:** Use well-tested libraries and frameworks for common tasks (e.g., date manipulation, HTTP requests) instead of writing your own from scratch.
- **Premature Optimization:** Do not optimize code without evidence (profiling) that it is a bottleneck. It often leads to more complex, harder-to-read code for negligible performance gain.

## 3. Error Handling and Reliability

- **Empty Catch Blocks:** Never swallow exceptions with an empty `catch` or `except` block. At a minimum, log the error.
- **Generic Exceptions:** Catch specific exceptions rather than generic ones (e.g., `except ValueError:` instead of `except:` in Python).
- **Error Messages:** Provide clear and informative error messages that can help with debugging.
- **Resource Management:** Ensure that resources like file handles, network connections, and database connections are properly closed, even if errors occur (e.g., using `try...finally` or context managers like `with` in Python).

## 4. Security Best Practices

- **Input Validation:** Never trust user input. Validate and sanitize all data coming from external sources to prevent injection attacks (SQLi, XSS).
- **Hardcoded Secrets:** Never hardcode API keys, passwords, or other secrets directly in the source code. Use environment variables or a secrets management system.
- **Dependencies:** Keep your project's dependencies up-to-date to patch known security vulnerabilities. Use tools to scan for vulnerabilities.
- **Principle of Least Privilege:** Code should only have the permissions it needs to perform its function.

## 5. Concurrency

- **Race Conditions:** Be cautious when multiple threads or processes access shared state. Use locks, mutexes, or other synchronization primitives to prevent race conditions.
- **Deadlocks:** Avoid situations where two or more threads are blocked forever, waiting for each other.
