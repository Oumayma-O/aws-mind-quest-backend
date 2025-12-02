# Dependency Management Quick Commands
# Run these commands from the project root

# Install production dependencies
install:
	pip install -r requirements.txt

# Install all dependencies (production + development)
install-dev:
	pip install -r requirements.txt -r requirements-dev.txt

# Compile requirements files from .in files
compile:
	pip-compile requirements.in
	pip-compile requirements-dev.in -c requirements.txt

# Upgrade all dependencies to latest compatible versions
upgrade:
	pip-compile --upgrade requirements.in
	pip-compile --upgrade requirements-dev.in -c requirements.txt

# Sync environment to match requirements exactly (removes extra packages)
sync:
	pip-sync requirements.txt requirements-dev.txt

# Sync to production only (removes dev packages)
sync-prod:
	pip-sync requirements.txt

# Check if requirements are up to date
check:
	pip-compile --dry-run requirements.in
	pip-compile --dry-run requirements-dev.in -c requirements.txt

# Clean compiled files (use with caution)
clean:
	rm -f requirements.txt requirements-dev.txt

.PHONY: install install-dev compile upgrade sync sync-prod check clean
