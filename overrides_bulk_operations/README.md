# Override Bulk Operation Scripts

Using `vacation_overrides.py` (originally by Lucas Epp:
[lfepp/35a2ce76114e7e6e3d7dece79eb7c635](https://gist.github.com/lfepp/35a2ce76114e7e6e3d7dece79eb7c635))
one can create overrides on all schedules where a user going on vacation would be on-call, and overrides them with another user on that schedule.

If a lot of overrides are accidentally added, or one wishes to revert that
action, these overrides can be almost as easily removed. The only way otherwise
to clean up overrides is clicking on each and every one of them after assessing
whether it is the correct override to delete, so we have scripts for that too.

## Scripts Overview

### get_overrides.py

This script retrieves PagerDuty schedule overrides within a specified date range and exports them to CSV format. It's designed to help with bulk override management and cleanup operations.

#### Features

- **Flexible Output**: Export to CSV file or stdout
- **Date Range Filtering**: Specify exact time windows for override searches
- **Schedule Selection**: Target specific schedules or scan all schedules
- **Robust Error Handling**: Graceful handling of API errors and missing data
- **Verbose Logging**: Optional detailed output for debugging
- **CSV Headers**: Optional column headers for better data organization

#### Usage

```bash
./get_overrides.py -k <API_KEY> -s <START_DATE> -e <END_DATE> [OPTIONS]
```

#### Required Arguments

- `-k, --api-key`: PagerDuty REST API key
- `-s, --start`: Start date in YYYY-MM-DD format
- `-e, --end`: End date in YYYY-MM-DD format

#### Optional Arguments

- `-f, --csv-file`: Output CSV file (default: stdout)
- `-c, --schedules`: Specific schedule IDs to search (can be used multiple times)
- `-v, --verbose`: Enable detailed logging output
- `--include-headers`: Add CSV column headers

#### Examples

```bash
# Basic usage - output to terminal
./get_overrides.py -k $PAGERDUTY_TOKEN -s 2025-11-01 -e 2025-11-30

# Save to file with headers
./get_overrides.py -k $PAGERDUTY_TOKEN -s 2025-11-01 -e 2025-11-30 -f overrides.csv --include-headers

# Search specific schedules only
./get_overrides.py -k $PAGERDUTY_TOKEN -s 2025-11-01 -e 2025-11-30 -c SCHEDULE1 -c SCHEDULE2

# Verbose output for debugging
./get_overrides.py -k $PAGERDUTY_TOKEN -s 2025-11-01 -e 2025-11-30 -v
```

#### CSV Output Format

The script outputs three columns:

1. **Schedule ID**: The PagerDuty schedule identifier
2. **Override ID**: The unique override identifier  
3. **User and Time Range**: Human-readable description in format "User Name: Start Time to End Time"

Example output:

```csv
Schedule ID,Override ID,User and Time Range
P123ABC,OVR456DEF,John Smith: 2025-11-01T09:00:00Z to 2025-11-01T17:00:00Z
P123ABC,OVR789GHI,Jane Doe: 2025-11-02T09:00:00Z to 2025-11-02T17:00:00Z
```

#### Prerequisites

- Python 3.6+
- `pagerduty` Python module: `pip install pagerduty`
- Valid PagerDuty API key with appropriate permissions

## Bulk Override Cleanup Workflow

To clean up overrides in an automated fashion:

1. **Extract Overrides**: Run `get_overrides.py` to export current overrides
2. **Review and Filter**: Modify the CSV file to remove any overrides that shouldn't be deleted
3. **Bulk Delete**: Run `mass_delete_overrides.py` on the filtered CSV to remove the overrides
