#!/bin/bash
# setup-cores.sh - Configure core dump settings for development

set -e  # Exit on error

echo "=== Setting up core dump configuration ==="

# Set core pattern using sysctl
if sysctl -w kernel.core_pattern="dump_%e.%p.core" 2>/dev/null; then
    echo "✓ Core pattern set to: $(sysctl -n kernel.core_pattern)"
else
    echo "⚠ Warning: Could not set core pattern (need --privileged)"
    echo "  Current pattern: $(sysctl -n kernel.core_pattern)"
    echo "  Run container with --privileged to enable custom core naming"
fi

# Enable unlimited core dumps
ulimit -c unlimited
echo "✓ Core dumps enabled (unlimited)"

# Create cores directory
mkdir -p /tmp/cores
echo "✓ Created /tmp/cores directory"

# Set working directory for cores (optional)
cd /tmp/cores
echo "✓ Changed working directory to /tmp/cores"

# Show current settings
echo ""
echo "=== Current core dump settings ==="
echo "Core pattern: $(sysctl -n kernel.core_pattern)"
echo "Core limit: $(ulimit -c)"
echo "Working directory: $(pwd)"
echo ""

# Execute the command passed to the script
if [ $# -gt 0 ]; then
    echo "=== Executing: $@ ==="
    exec "$@"
else
    echo "=== Starting bash shell ==="
    exec /bin/bash
fi
