#!/usr/bin/env python3

import json
import getvenue as gv
from pathlib import Path


def main():
    """Retrieve all events starting within the next 12 months using the getvenue module and output them to a JSON file."""

    events_output = []
    events_output += gv.bowery_shows()
    # events_output += gv.houseofblues()
    events_output += gv.monthly_cals()
    with open(Path(__file__).parent / 'events.json', 'w') as f:
        json.dump(events_output, f)


if __name__ == '__main__':
    main()
