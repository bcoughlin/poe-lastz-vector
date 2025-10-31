# Bot Version Symlink

## Current Setup

The `bot_symlink` symlink points to the active bot version:

```
bot_symlink -> poe_lastz_v0_8_2/
```

## Why Use a Symlink?

- **No deployment config changes**: `render.yaml` always uses `bot_symlink`, never needs editing
- **Easy version switching**: Just update the symlink to point to a different version
- **Clear indication**: The symlink name makes it obvious this is pointing to the active bot version

## How to Switch Versions

When you want to deploy a different version (e.g., `poe_lastz_v0_8_3`):

```bash
# Remove old symlink
rm bot_symlink

# Create new symlink to the new version
ln -s poe_lastz_v0_8_3 bot_symlink

# Commit the change
git add bot_symlink
git commit -m "Switch to v0.8.3"
git push
```

Render will automatically pick up the new version on the next deploy!

## Verification

Check which version is active:
```bash
ls -la bot_symlink
# Output: bot_symlink -> poe_lastz_v0_8_2
```
