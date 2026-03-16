# Contributing to Task Safety Framework

Thank you for your interest in contributing! 🎉

## How to Contribute

### 1. Report Bugs

- Check if the bug already exists in [Issues](https://github.com/chenqin2026/task-safety-framework/issues)
- Create a new issue with:
  - Clear title
  - Steps to reproduce
  - Expected vs actual behavior
  - Environment info (Python version, OS)

### 2. Suggest Features

- Open a discussion in [Discussions](https://github.com/chenqin2026/task-safety-framework/discussions)
- Explain the use case and benefits

### 3. Submit Pull Requests

1. Fork the repository
2. Create a feature branch:
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. Make your changes
4. Write/update tests
5. Run tests:
   ```bash
   pytest tests/
   ```
6. Commit with clear messages:
   ```bash
   git commit -m "Add amazing feature"
   ```
7. Push and create PR:
   ```bash
   git push origin feature/amazing-feature
   ```

## Development Setup

```bash
# Clone repo
git clone https://github.com/chenqin2026/task-safety-framework.git
cd task-safety-framework

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest tests/
```

## Code Style

- Use Python 3.8+
- Follow PEP 8 style guide
- Add docstrings to all functions
- Write tests for new features

## Testing

All PRs must pass tests:

```bash
pytest tests/ -v
```

### Running Specific Tests

```bash
# Unit tests
pytest tests/test_safe_task.py

# Integration tests
pytest tests/test_long_running_task.py

# With coverage
pytest --cov=src tests/
```

## Documentation

- Update README.md for major features
- Add examples in `examples/` directory
- Update docstrings for API changes

## Questions?

- Open a [Discussion](https://github.com/chenqin2026/task-safety-framework/discussions)
- Check existing [Issues](https://github.com/chenqin2026/task-safety-framework/issues)

---

**Thank you for contributing! 🐶**
