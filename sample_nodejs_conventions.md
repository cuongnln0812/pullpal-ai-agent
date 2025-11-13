# Sample Node.js Coding Conventions

This document outlines specific coding conventions and rules for our Node.js projects. Adherence to these guidelines ensures consistency, readability, and maintainability across the codebase.

## 1. JavaScript/TypeScript Specific Rules

### 1.1 Naming Conventions
- **Variables and Functions:** `camelCase` (e.g., `userName`, `calculateTotal`).
- **Classes:** `PascalCase` (e.g., `UserManager`, `OrderProcessor`).
- **Constants (global/module-level):** `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`, `DEFAULT_TIMEOUT`).
- **Private/Internal Members:** Prefix with an underscore (e.g., `_internalMethod`, `_privateVariable`) for convention, though JavaScript doesn't enforce true privacy.

### 1.2 Asynchronous Code
- Prefer `async/await` over Promises `.then().catch()` for better readability and error handling.
- Always handle errors in asynchronous operations (e.g., `try...catch` with `async/await`).

### 1.3 Imports/Exports
- Use ES Modules (`import`/`export`) syntax. Avoid CommonJS (`require`/`module.exports`) unless absolutely necessary for compatibility with older modules.
- Group imports:
    1.  Node.js built-in modules (e.g., `path`, `fs`).
    2.  Third-party library imports.
    3.  Local application/library-specific imports.
- Each group should be separated by a blank line.

### 1.4 Type Safety (TypeScript)
- Define explicit types for variables, function parameters, and return values.
- Avoid `any` type unless absolutely necessary for interoperability with untyped libraries.
- Use interfaces or types for object shapes.

### 1.5 Error Handling
- Use custom error classes for application-specific errors.
- Centralize error handling where appropriate (e.g., middleware in Express apps).
- Log errors with sufficient context.

## 2. General Best Practices

### 2.1 Line Length
- Limit all lines to a maximum of 120 characters.

### 2.2 Comments
- Use comments to explain *why* a piece of code exists or *what* a complex algorithm does, not *how* it works.
- Keep comments up-to-date.

### 2.3 Function Size
- Functions should be concise and focused on a single responsibility. Refactor large functions.

### 2.4 Avoid Magic Numbers/Strings
- Define constants for any literal values that have special meaning.

### 2.5 Configuration
- All configuration parameters should be loaded from environment variables (e.g., using `dotenv`) or a dedicated configuration service, not hardcoded.

## 3. Security Guidelines

### 3.1 Input Validation
- Always validate and sanitize all external input (user input, API responses, file contents) to prevent security vulnerabilities. Use libraries like `Joi` or `Yup`.

### 3.2 Secrets Management
- Never commit API keys, passwords, or other sensitive information directly into the repository. Use environment variables or a secure secrets management system (e.g., AWS Secrets Manager, HashiCorp Vault).

### 3.3 Dependency Management
- Regularly update dependencies to patch known security vulnerabilities. Use tools like `npm audit` or `Snyk`.
- Be cautious when adding new dependencies; prefer well-maintained and widely used packages.
