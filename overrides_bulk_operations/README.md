# Override Bulk Operation Scripts

## Table of Contents
- [vacation_overrides.py](#vacation_overridespy)
- [get_overrides.py](#get_overridespy)
- [mass_delete_overrides.py](#mass_delete_overridespy)
- [Bulk Override Cleanup Workflow](#bulk-override-cleanup-workflow)

## vacation_overrides.py

Using `vacation_overrides.py` (originally by Lucas Epp:
[lfepp/35a2ce76114e7e6e3d7dece79eb7c635](https://gist.github.com/lfepp/35a2ce76114e7e6e3d7dece79eb7c635))
one can create overrides on all schedules where a user going on vacation would be on-call, and overrides them with another user on that schedule.

If a lot of overrides are accidentally added, or one wishes to revert that
action, these overrides can be almost as easily removed. The only way otherwise
to clean up overrides is clicking on each and every one of them after assessing
whether it is the correct override to delete, so we have scripts for that too.

This script automates the creation of PagerDuty schedule overrides for vacation coverage. When a team member goes on vacation, this script identifies all their scheduled on-call shifts and creates overrides to assign those shifts to a substitute user.

#### Features

- **Automatic Shift Detection**: Scans all schedules to find the vacationing user's on-call shifts
- **Flexible Schedule Selection**: Target specific schedules or scan all schedules
- **Date Range Support**: Cover any vacation period with precise start/end dates
- **User-Friendly Output**: Shows progress and details of each override created
- **Error Handling**: Continues processing if individual overrides fail
- **Email-Based User Lookup**: Uses email addresses to identify users

#### Usage

```bash
./vacation_overrides.py -v <VACATIONER_EMAIL> -u <SUBSTITUTE_EMAIL> -k <API_KEY> -s <START_DATE> -e <END_DATE> [OPTIONS]
```

#### Required Arguments

- `-v, --vacationer`: Email address of the user going on vacation
- `-u, --substitute`: Email address of the user who will cover the shifts
- `-k, --api-key`: PagerDuty REST API key
- `-s, --start`: Start date of the vacation period
- `-e, --end`: End date of the vacation period

#### Optional Arguments

- `-c, --schedules`: Specific schedule IDs to process (can be used multiple times). If not specified, all schedules will be scanned.

#### Examples

```bash
# Basic vacation coverage - scan all schedules
./vacation_overrides.py -v john.doe@company.com -u jane.smith@company.com -k $PAGERDUTY_TOKEN -s 2025-11-06 -e 2025-11-15

# Target specific schedules only
./vacation_overrides.py -v john.doe@company.com -u jane.smith@company.com -k $PAGERDUTY_TOKEN -s 2025-11-06 -e 2025-11-15 -c SCHEDULE1 -c SCHEDULE2

# Extended vacation period
./vacation_overrides.py -v john.doe@company.com -u jane.smith@company.com -k $PAGERDUTY_TOKEN -s 2025-12-20 -e 2026-01-05
```

#### How It Works

1. **User Validation**: Verifies that both the vacationer and substitute users exist in PagerDuty
2. **Schedule Discovery**: Retrieves all schedules (or specified schedules) from PagerDuty
3. **Shift Analysis**: Examines each schedule's rendered entries to find shifts assigned to the vacationing user
4. **Override Creation**: Creates overrides for each identified shift, assigning them to the substitute user
5. **Progress Reporting**: Shows details of each shift found and override created

#### Sample Output

```text
Getting schedules...
Looking for shifts that will require coverage...
Found shift for vacationing user from 2025-11-06T14:00:00Z to 2025-11-07T02:00:00Z
Found shift for vacationing user from 2025-11-07T14:00:00Z to 2025-11-08T02:00:00Z
Creating override on schedule PWC94CB (Systems Infra - Primary) from 2025-11-06T14:00:00Z to 2025-11-07T02:00:00Z...
Success.
Creating override on schedule PWC94CB (Systems Infra - Primary) from 2025-11-07T14:00:00Z to 2025-11-08T02:00:00Z...
Success.
```

#### Prerequisites

- Python 3.6+
- `pagerduty` Python module: `pip install pagerduty`
- Valid PagerDuty API key with appropriate permissions
- Both users must exist in PagerDuty and be identified by their login email addresses

#### Important Notes

- **Existing Overrides**: This script does not check for existing overrides - it will create new ones regardless
- **Schedule Permissions**: The substitute user should have appropriate permissions on the schedules where overrides are created
- **Time Zones**: All times are processed in UTC as returned by the PagerDuty API
- **Cleanup**: Use `get_overrides.py` and `mass_delete_overrides.py` if you need to remove the created overrides later

## get_overrides.py

This script retrieves PagerDuty schedule overrides within a specified date range and exports them to CSV format. It's designed to help with bulk override management and cleanup operations.

#### Key Features

- **Flexible Output**: Export to CSV file or stdout
- **Date Range Filtering**: Specify exact time windows for override searches
- **Schedule Selection**: Target specific schedules or scan all schedules
- **Robust Error Handling**: Graceful handling of API errors and missing data
- **Verbose Logging**: Optional detailed output for debugging
- **CSV Headers**: Optional column headers for better data organization

#### Command Syntax

```bash
./get_overrides.py -k <API_KEY> -s <START_DATE> -e <END_DATE> [OPTIONS]
```

#### Arguments

**Required:**

- `-k, --api-key`: PagerDuty REST API key
- `-s, --start`: Start date in YYYY-MM-DD format
- `-e, --end`: End date in YYYY-MM-DD format

**Optional:**

- `-f, --csv-file`: Output CSV file (default: stdout)
- `-c, --schedules`: Specific schedule IDs to search (can be used multiple times)
- `-v, --verbose`: Enable detailed logging output
- `--include-headers`: Add CSV column headers
- `--team`: Filter to schedules belonging to the specified team name (case-insensitive). If multiple teams match the query, use the exact full name.

#### Usage Examples

```bash
# Basic usage - output to terminal
./get_overrides.py -k $PAGERDUTY_TOKEN -s 2025-11-01 -e 2025-11-30

# Save to file with headers
./get_overrides.py -k $PAGERDUTY_TOKEN -s 2025-11-01 -e 2025-11-30 -f overrides.csv --include-headers

# Search specific schedules only
./get_overrides.py -k $PAGERDUTY_TOKEN -s 2025-11-01 -e 2025-11-30 -c SCHEDULE1 -c SCHEDULE2

# Verbose output for debugging
./get_overrides.py -k $PAGERDUTY_TOKEN -s 2025-11-01 -e 2025-11-30 -v

# Filter to a specific team by name
./get_overrides.py -k $PAGERDUTY_TOKEN -s 2025-11-01 -e 2025-11-30 --team "Systems Infra"
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

#### Requirements

- Python 3.6+
- `pagerduty` Python module: `pip install pagerduty`
- Valid PagerDuty API key with appropriate permissions

#### Sample Output

```text
# Basic (stdout, no headers)
P123ABC,OVR456DEF,John Smith: 2025-11-01T09:00:00Z to 2025-11-01T17:00:00Z
P123ABC,OVR789GHI,Jane Doe: 2025-11-02T09:00:00Z to 2025-11-02T17:00:00Z

# With --include-headers
Schedule ID,Override ID,User and Time Range
P123ABC,OVR456DEF,John Smith: 2025-11-01T09:00:00Z to 2025-11-01T17:00:00Z
P123ABC,OVR789GHI,Jane Doe: 2025-11-02T09:00:00Z to 2025-11-02T17:00:00Z

# Verbose mode (-v)
[INFO] Using schedules: all
[INFO] Time range: 2025-11-01T00:00:00Z to 2025-11-30T23:59:59Z
[INFO] Fetching schedules...
[INFO] Processing schedule P123ABC (Systems Infra - Primary)
[DEBUG] Retrieved 2 overrides
P123ABC,OVR456DEF,John Smith: 2025-11-01T09:00:00Z to 2025-11-01T17:00:00Z
P123ABC,OVR789GHI,Jane Doe: 2025-11-02T09:00:00Z to 2025-11-02T17:00:00Z
[INFO] Done. Total overrides: 2
```

## mass_delete_overrides.py

Deletes overrides listed in a CSV (as produced by get_overrides.py). Reads each line and attempts to delete the corresponding override.

#### Sample Output

```text
Reading overrides from overrides.csv...
Validating CSV format...
Found 2 overrides to delete.
Deleting override OVR456DEF on schedule P123ABC...
Success.
Deleting override OVR789GHI on schedule P123ABC...
Failed (404 Not Found). Skipping.

Summary:
- Attempted: 2
- Deleted: 1
- Failed: 1
```

## Bulk Override Cleanup Workflow

To clean up overrides in an automated fashion:

1. **Extract Overrides**: Run `get_overrides.py` to export current overrides
2. **Review and Filter**: Modify the CSV file to remove any overrides that shouldn't be deleted
3. **Bulk Delete**: Run `mass_delete_overrides.py` on the filtered CSV to remove the overrides
