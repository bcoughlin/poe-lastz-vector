#!/bin/bash
# Setup script for installing git hooks

set -e

echo "🔧 Installing git pre-commit hook..."

# Copy pre-commit hook
HOOK_SOURCE=".githooks/pre-commit"
HOOK_DEST=".git/hooks/pre-commit"

mkdir -p .githooks

cat > "$HOOK_SOURCE" << 'EOF'
#!/bin/bash
# Git pre-commit hook - runs linting checks before commit

echo "🔍 Running pre-commit checks..."

# Run ruff linting
if ! ruff check poe_lastz_v0_8_2/ scripts/ --exclude archive/ --quiet; then
    echo "❌ Ruff linting failed! Run 'make lint-fix' to auto-fix issues."
    exit 1
fi

# Run ruff format check
if ! ruff format poe_lastz_v0_8_2/ scripts/ --exclude archive/ --check --quiet; then
    echo "❌ Code formatting check failed! Run 'make format' to fix formatting."
    exit 1
fi

echo "✅ Pre-commit checks passed!"
exit 0
EOF

cp "$HOOK_SOURCE" "$HOOK_DEST"
chmod +x "$HOOK_DEST"

echo "✅ Git hooks installed successfully!"
echo ""
echo "📝 Pre-commit hook will now run linting checks before each commit."
echo "   To bypass: git commit --no-verify"
