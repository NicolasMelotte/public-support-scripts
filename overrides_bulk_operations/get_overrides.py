#!/usr/bin/env python3

import argparse
import csv
import logging
import sys
from datetime import datetime
from typing import List, Optional

try:
    import pagerduty
except ImportError:
    print("Error: pagerduty module is required. Install with: pip install pagerduty", file=sys.stderr)
    sys.exit(1)


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s',
        stream=sys.stderr
    )


def validate_date_format(date_str: str) -> bool:
    """Validate date format (YYYY-MM-DD)."""
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def get_schedules(session: pagerduty.RestApiV2Client, schedule_ids: List[str]) -> List[str]:
    """Get schedule IDs, either from provided list or all available schedules."""
    if schedule_ids:
        return schedule_ids
    
    try:
        schedules = [s['id'] for s in session.iter_all('schedules')]
        return schedules
    except Exception as e:
        logging.error(f"Failed to fetch schedules: {e}")
        raise


def process_overrides(session: pagerduty.RestApiV2Client, schedule_ids: List[str], 
                     window: dict, writer: csv.writer) -> int:
    """Process overrides for given schedules and write to CSV."""
    total_overrides = 0
    
    for sid in schedule_ids:
        try:
            overrides = list(session.rget(f'/schedules/{sid}/overrides', params=window))
            total_overrides += len(overrides)
            
            for override in overrides:
                try:
                    user_summary = override.get('user', {}).get('summary', 'Unknown User')
                    start_time = override.get('start', 'Unknown Start')
                    end_time = override.get('end', 'Unknown End')
                    override_id = override.get('id', 'Unknown ID')
                    
                    idtag = f"{user_summary}: {start_time} to {end_time}"
                    writer.writerow((sid, override_id, idtag))
                    
                except Exception as e:
                    logging.warning(f"Error processing override in schedule {sid}: {e}")
                    continue
                    
        except Exception as e:
            logging.error(f"Failed to process schedule {sid}: {e}")
            continue
    
    return total_overrides


def main():
    ap = argparse.ArgumentParser(
        description="Gets all overrides in PagerDuty schedules and exports to CSV. "
                   "The output contains schedule ID, override ID, and user/time information.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    ap.add_argument('-k', '--api-key', type=str, required=True,
                   dest='api_key', help="PagerDuty REST API key")
    ap.add_argument('-f', '--csv-file', type=argparse.FileType('w'),
                   dest="csv_file", help="Output CSV file (default: stdout)")
    ap.add_argument('-s', '--start', required=True, 
                   help="Start date of search (YYYY-MM-DD format)")
    ap.add_argument('-e', '--end', required=True,
                   help="End date of search (YYYY-MM-DD format)")
    ap.add_argument('-c', '--schedules', default=[], action='append',
                   help="Schedule IDs to search (can be used multiple times). "
                        "If not specified, all schedules will be included.")
    ap.add_argument('-v', '--verbose', action='store_true',
                   help="Enable verbose logging")
    ap.add_argument('--include-headers', action='store_true',
                   help="Include CSV column headers in output")

    args = ap.parse_args()
    
    # Set up logging
    setup_logging(args.verbose)
    
    # Validate date formats
    if not validate_date_format(args.start):
        print(f"Error: Invalid start date format: {args.start}. Use YYYY-MM-DD format.", file=sys.stderr)
        sys.exit(1)
    
    if not validate_date_format(args.end):
        print(f"Error: Invalid end date format: {args.end}. Use YYYY-MM-DD format.", file=sys.stderr)
        sys.exit(1)
    
    # Validate date range
    start_date = datetime.strptime(args.start, '%Y-%m-%d')
    end_date = datetime.strptime(args.end, '%Y-%m-%d')
    if start_date >= end_date:
        print("Error: Start date must be before end date", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Initialize PagerDuty session
        session = pagerduty.RestApiV2Client(args.api_key)
        
        # Set up time window
        window = {'since': args.start, 'until': args.end}
        
        # Set up output
        output_file = args.csv_file if args.csv_file else sys.stdout
        writer = csv.writer(output_file)
        
        # Add headers if requested
        if args.include_headers:
            writer.writerow(['Schedule ID', 'Override ID', 'User and Time Range'])
        
        # Get schedules
        schedules = get_schedules(session, args.schedules)
        
        # Process overrides
        total_overrides = process_overrides(session, schedules, window, writer)
        
        # Close file if we opened one
        if args.csv_file:
            args.csv_file.close()
            
    except KeyboardInterrupt:
        print("Operation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
