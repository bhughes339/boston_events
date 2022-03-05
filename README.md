# Boston Event Scraper

- Note: This project is now defunct due to the COVID-19 pandemic halting most events in the Boston area. This repository is provided as documentation of the scraping methods used.

A collection of functions designed to retrieve and parse various venue calendars in the Boston area.

Most functions return an array of JSON-formattable event objects, which follow this template:
```json
{
    venue: string
    bands: [string]
    start: string date in ISO format (e.g. 2020-02-01T21:00:00-05:00)
    link: string
    soldout: boolean
}
```

## Installation

- Replace `python3` with `py` if using Windows

```bash
python3 -m pip install -r requirements.txt
```

## Usage

- Replace `python3` with `py` if using Windows

Parse the next twelve months of concerts and export to `events.json`:
```bash
python3 -m get_events
```
