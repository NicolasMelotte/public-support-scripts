#!/usr/bin/env python
import argparse
import json
import requests
import sys
import pagerduty

# Add: examples epilog for argparse help
EXAMPLES = """
Examples:
  # Basic vacation coverage - scan all schedules
  %(prog)s -v john.doe@company.com -u jane.smith@company.com -k $PAGERDUTY_TOKEN -s 2026-01-15 -e 2026-01-20

  # Target specific schedules only
  %(prog)s -v john.doe@company.com -u jane.smith@company.com -k $PAGERDUTY_TOKEN -s 2026-01-15 -e 2026-01-20 -c PWC94CB -c PABC123
""".strip()

def find_shifts(session, vacationing_user, start, end, schedule_ids):
    """Find all on-call shifts on the specified schedules between `since` and `until`."""
    params = {"since": start, "until": end}
    shifts = {}  # {(start, end): {"id": schedule_id, "summary": schedule_summary}}
    get_schedule = lambda sid: session.rget('/schedules/' + sid, params=params)

    schedules = []
    for sid in schedule_ids:
        try:
            raw = get_schedule(sid)
            # Some clients wrap the schedule under "schedule"
            schedule = raw.get('schedule', raw) if isinstance(raw, dict) else raw
            schedules.append(schedule)
        except Exception as e:
            print(f"Error fetching schedule {sid}: {e}", file=sys.stderr)
            continue

    for schedule in schedules:
        entries = (schedule or {}).get("final_schedule", {}).get("rendered_schedule_entries", [])
        for shift in entries:
            try:
                user_id = (shift.get("user") or {}).get("id")
                if user_id == vacationing_user:
                    start_ts = shift.get("start")
                    end_ts = shift.get("end")
                    print("Found shift for vacationing user from %s to %s" % (start_ts, end_ts))
                    shifts[(start_ts, end_ts)] = {
                        "id": schedule.get("id"),
                        "summary": (schedule.get("summary") or "").replace("\n", " ").strip()
                    }
            except Exception as e:
                print(f"Error parsing shift entry: {e}", file=sys.stderr)
                continue
    return shifts

def create_overrides():
    """For shift in find_shifts(), create an override to replace vacationing_user with replacement_user."""
    ap = argparse.ArgumentParser(
        description="For a given user going on vacation, create overrides on all the vacationing user's schedules so the substitute covers those shifts.",
        epilog=EXAMPLES,
        formatter_class=argparse.RawTextHelpFormatter  # ensures examples render nicely
    )
    ap.add_argument('-v', '--vacationer', required=True,
                    help="Login email address of the user who is going on vacation.")
    ap.add_argument('-u', '--substitute', required=True,
                    help="Login email address of the user who is covering the shifts.")
    ap.add_argument('-k', '--api-key', required=True,
                    help="PagerDuty REST API key to use for operations.")
    ap.add_argument('-s', '--start', required=True,
                    help="Start date of the vacation (YYYY-MM-DD or ISO8601).")
    ap.add_argument('-e', '--end', required=True,
                    help="End date of the vacation (YYYY-MM-DD or ISO8601).")
    ap.add_argument('-c', '--schedules', default=[], action='append',
                    help="IDs of schedules in which to create overrides. If unspecified, all schedules will be included.")
    # Note: -h/--help is provided by argparse by default and will exit after printing this help.

    args = ap.parse_args()

    session = pagerduty.RestApiV2Client(args.api_key)
    vacationing_user = session.find('users', args.vacationer, attribute='email')
    replacement_user = session.find('users', args.substitute, attribute='email')
    if None in (vacationing_user, replacement_user):
        print("Invalid login email specified for the vacationing user and/or "
            "substitute user.")
        return
    schedules = args.schedules
    if not args.schedules:
        print("Getting schedules...")
        schedules = [s['id'] for s in session.iter_all('schedules')]
    print("Looking for shifts that will require coverage...")
    shifts = find_shifts(session, vacationing_user['id'], args.start, args.end, schedules)

    print("Looping over shifts...")
    for dates, schedule in shifts.items():
        start, end = dates
        sid = schedule.get('id')
        summary = schedule.get('summary', sid)
        print("Creating override on schedule %s (%s) from %s to %s..." % (sid, summary, start, end))
        try:
            create_response = session.post(
                '/schedules/%s/overrides' % sid,
                json={
                    'override': {
                        "start": start,
                        "end": end,
                        "user": {
                            "id": replacement_user['id'],
                            "type": "user_reference"
                        }
                    }
                }
            )
            # Normalize success across response types (requests.Response or dict)
            override_id = None
            is_success = False
            status_code = getattr(create_response, "status_code", None)
            text = getattr(create_response, "text", "")
            ok = getattr(create_response, "ok", None)

            if isinstance(create_response, dict):
                override_id = create_response.get('override', {}).get('id') or create_response.get('id')
                is_success = bool(override_id)
            else:
                if status_code is not None:
                    is_success = 200 <= status_code < 300
                elif ok is not None:
                    is_success = bool(ok)

            if is_success:
                msg_id = override_id if override_id else create_response.json().get('override', {}).get('id', '')
                if msg_id:
                    print(f"Successfully created override (id: {msg_id}).")
                else:
                    print("Successfully created override.")
            else:
                print("Error creating override: HTTP %s - %s" % (
                    status_code if status_code is not None else "unknown",
                    text
                ))
        except requests.exceptions.RequestException as e:
            print("Error creating override: %s" % str(e))
            continue
        except Exception as e:
            print("Unexpected error creating override: %s" % str(e))
            continue

if __name__ == "__main__":
    create_overrides()
