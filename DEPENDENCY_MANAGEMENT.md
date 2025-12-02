# Dependency Management with pip-tools

This project uses **pip-tools** for robust dependency management, ensuring reproducible builds and resolving dependency conflicts automatically.

## Overview

We maintain two types of dependency files:

### Source Files (Human-Edited)
- `requirements.in` - Production dependencies (direct dependencies only)
- `requirements-dev.in` - Development dependencies (testing, code quality)

### Compiled Files (Auto-Generated)
- `requirements.txt` - Locked production dependencies with all transitive dependencies
- `requirements-dev.txt` - Locked development dependencies with all transitive dependencies

**⚠️ Important**: Never edit `.txt` files directly! Always edit `.in` files and recompile.

## Installation

pip-tools is already installed in this project. If you need to install it:

```bash
pip install pip-tools
```

## Common Workflows

### 1. Installing Dependencies

**For production dependencies:**
```bash
pip install -r requirements.txt
```

**For development (includes production + dev dependencies):**
```bash
pip install -r requirements.txt -r requirements-dev.txt
```

Or use pip-sync for an exact match:
```bash
pip-sync requirements.txt requirements-dev.txt
```

### 2. Adding a New Dependency

**Step 1:** Add the package to the appropriate `.in` file

For production dependencies, edit `requirements.in`:
```
# Add new package
numpy>=1.20.0
```

For development dependencies, edit `requirements-dev.in`:
```
# Add new package
pytest-mock==3.12.0
```

**Step 2:** Recompile the requirements

```bash
# Compile production dependencies
pip-compile requirements.in

# Compile development dependencies
pip-compile requirements-dev.in -c requirements.txt
```

**Step 3:** Install the updated dependencies

```bash
pip install -r requirements.txt
# or for dev dependencies
pip install -r requirements-dev.txt
```

### 3. Upgrading Dependencies

**Upgrade all packages:**
```bash
pip-compile --upgrade requirements.in
pip-compile --upgrade requirements-dev.in -c requirements.txt
```

**Upgrade a specific package:**
```bash
pip-compile --upgrade-package fastapi requirements.in
```

**Upgrade to latest compatible versions:**
```bash
# Edit requirements.in and change version constraints, then:
pip-compile requirements.in
```

### 4. Removing a Dependency

**Step 1:** Remove the package from the `.in` file

**Step 2:** Recompile

```bash
pip-compile requirements.in
```

**Step 3:** Sync your environment to remove unused packages

```bash
pip-sync requirements.txt requirements-dev.txt
```

## pip-compile Options

### Useful Flags

```bash
# Upgrade all packages to their latest versions
pip-compile --upgrade requirements.in

# Upgrade a specific package
pip-compile --upgrade-package <package-name> requirements.in

# Use backtracking resolver (better conflict resolution)
pip-compile --resolver=backtracking requirements.in

# Show which packages depend on each package
pip-compile --annotation-style=line requirements.in

# Dry run to see what would change
pip-compile --dry-run requirements.in
```

## pip-sync

`pip-sync` ensures your virtual environment exactly matches your requirements files:

```bash
# Sync to production requirements only
pip-sync requirements.txt

# Sync to production + development requirements
pip-sync requirements.txt requirements-dev.txt
```

This will:
- Install packages that are in the requirements files but not in your environment
- Uninstall packages that are in your environment but not in the requirements files
- Ensure all versions match exactly

## Troubleshooting

### Dependency Conflicts

If you encounter a conflict, pip-compile will show you exactly which packages have incompatible requirements:

```
ERROR: Cannot install package-a==1.0 and package-b==2.0 
because these package versions have conflicting dependencies.
```

**Solution:** Adjust version constraints in your `.in` file to allow compatible versions:

```
# Instead of:
package-a==1.0

# Use:
package-a>=1.0,<2.0
```

### Resolved Conflicts in This Project

The following conflicts were automatically detected and resolved:

1. **SQLAlchemy version conflict**
   - Issue: `langchain-community` requires `SQLAlchemy<2.0.36,>=1.4`
   - Solution: Changed from `SQLAlchemy==2.0.36` to `SQLAlchemy>=2.0.0,<2.0.36`

2. **pydantic-settings version conflict**
   - Issue: `langchain-community` requires `pydantic-settings>=2.4.0`
   - Solution: Changed from `pydantic-settings==2.3.1` to `pydantic-settings>=2.4.0`

3. **Transitive dependency conflicts (packaging, etc.)**
   - Issue: Dev and production requirements had conflicting versions for shared dependencies
   - Solution: Compile dev requirements with production as constraints using `-c requirements.txt`
   - This ensures dev dependencies use the same versions as production for shared packages

### Viewing Dependency Tree

To see why a package is installed:

```bash
pip show <package-name>
```

Or use pipdeptree (install separately):

```bash
pip install pipdeptree
pipdeptree -p <package-name>
```

## Best Practices

1. **Always edit `.in` files**, never `.txt` files
2. **Commit both `.in` and `.txt` files** to version control
3. **Run pip-compile after changing `.in` files** before committing
4. **Use version ranges** (e.g., `>=1.0,<2.0`) instead of exact pins in `.in` files when possible
5. **Pin exact versions** only when necessary (e.g., known compatibility issues)
6. **Review the generated `.txt` files** after compiling to understand what changed
7. **Use pip-sync** to ensure your environment matches requirements exactly
8. **Run pip-compile regularly** to get security updates within your version constraints

## CI/CD Integration

In your CI/CD pipeline, you should:

```bash
# Install exact versions from locked files
pip install -r requirements.txt

# For development/testing environments
pip install -r requirements.txt -r requirements-dev.txt

# Optionally verify the lock files are up to date
pip-compile --dry-run requirements.in
pip-compile --dry-run requirements-dev.in
```

## Additional Resources

- [pip-tools Documentation](https://pip-tools.readthedocs.io/)
- [pip-compile Command Reference](https://pip-tools.readthedocs.io/en/latest/#pip-compile)
- [pip-sync Command Reference](https://pip-tools.readthedocs.io/en/latest/#pip-sync)
