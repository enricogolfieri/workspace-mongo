# Watch MongoDB Catalog Tool

This tool watches a MongoDB `_mdb_catalog.wt` file for changes and displays the decoded BSON content in real-time.

## Components

- `watch_catalog` - Main bash script that monitors file changes
- `hex_2_bson.py` - BSON decoder (used internally)

## Requirements

- Python 3 with `bson` module installed (`pip install pymongo`)
- WiredTiger `wt` utility (usually found in MongoDB installation)

## Usage

### Basic Usage

```bash
# Watch a catalog file (auto-detects wt utility)
./watch_catalog ~/.mcluster/cdata/shard01/rs1/db/_mdb_catalog.wt

# Custom check interval (5 seconds instead of default 2)
./watch_catalog ~/.mcluster/cdata/shard01/rs1/db/_mdb_catalog.wt 5
```

## How It Works

1. The script monitors the specified `_mdb_catalog.wt` file for changes using MD5 hash comparison
2. When a change is detected, it:
   - **Removes the WiredTiger.lock file** to allow reading
   - Runs `wt -h <db_dir> dump -x file:_mdb_catalog.wt`
   - Pipes the output through `hex_2_bson.py` to decode the BSON
   - Displays the human-readable output with timestamp
3. Continues watching until interrupted with Ctrl+C

**Note:** The script automatically removes the lock file before each dump to ensure the wt utility can read the database.

## Finding the wt Utility

The `wt` utility is typically found in:
- MongoDB build directory: `~/mongo/wt` or `~/mongodb/bin/wt`
- System-wide install: `/usr/local/bin/wt` or `/usr/bin/wt`
- MongoDB installation: `<mongodb-install-dir>/bin/wt`

The script will attempt to auto-detect these common locations.

## Example Output

```
Watching catalog: /root/.mcluster/cdata/shard01/rs1/db/_mdb_catalog.wt
Using wt utility: /usr/local/bin/wt
Check interval: 2 seconds
Press Ctrl+C to stop

================================================================================
Dumping catalog at 2026-01-28 10:30:45
================================================================================

Key:	00000000
Value:
	{'_id': 'config.system.sessions',
	 'idxIdent': {...},
	 'ident': 'collection-1-123456789',
	 'md': {...}}

Key:	00000001
Value:
	{'_id': 'local.startup_log',
	 ...}

>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
Change detected!
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

================================================================================
Dumping catalog at 2026-01-28 10:30:47
================================================================================
...
```

## Integration with Workspace

You can add this to your shell profile to make it easily accessible:

```bash
# Add to ~/.zshrc or ~/.bashrc
alias watch-catalog='~/path/to/bashscripts/watch_catalog'

# Then use it from anywhere:
watch-catalog ~/.mcluster/cdata/shard01/rs1/db/_mdb_catalog.wt
```

## Troubleshooting

### "Could not find wt utility"
- Ensure you have MongoDB built or installed
- Specify the path to `wt` explicitly as the second argument
- Check if `wt` is executable: `chmod +x /path/to/wt`

### "bson module not found"
- Install pymongo: `pip install pymongo` or `pip3 install pymongo`

### "Permission denied"
- Ensure the scripts are executable: `chmod +x watch_catalog watch_mdb_catalog.py hex_2_bson.py`

### File not found
- Ensure the MongoDB database is running and the path is correct
- The catalog file is typically at: `<dbpath>/_mdb_catalog.wt`
