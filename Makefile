# Makefile for The Floor Is a Lie development

.PHONY: help install test run clean build lint format docs

# Default target
help:
	@echo "Available targets:"
	@echo "  install    - Install the package in development mode"
	@echo "  test       - Run the test suite"
	@echo "  run        - Run the game"
	@echo "  clean      - Clean build artifacts"
	@echo "  build      - Build the package"
	@echo "  lint       - Run linting checks"
	@echo "  format     - Format code with black"
	@echo "  docs       - Generate documentation"

# Install in development mode
install:
	pip install -e .

# Run tests
test:
	python run_tests.py

# Run the game
run:
	python main.py

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf __pycache__/
	rm -rf src/__pycache__/
	rm -rf src/*/__pycache__/
	rm -rf tests/__pycache__/
	rm -rf .pytest_cache/
	rm -f game_debug.log

# Build the package
build:
	python -m build

# Run linting (basic)
lint:
	python -m flake8 src/ tests/ --max-line-length=100 --ignore=E203,W503

# Format code
format:
	python -m black src/ tests/ --line-length=100

# Generate documentation (placeholder)
docs:
	@echo "Documentation generation not implemented yet"
	@echo "Consider using sphinx-doc for proper documentation"