#!/usr/bin/env python3

"""A collection of functions designed to retrieve and parse various venue calendars in the Boston area.

Most functions return an array of JSON-formattable event objects, which follow this template:
    {
        venue: string
        bands: array of strings
        start: string date in ISO format
        link: string
        soldout: boolean
    }
"""

import datetime
import json
import re

import requests

import dateutil
import dateutil.parser
import demjson
from bs4 import BeautifulSoup


class Event:
    """A single event parsed from an event calendar.

    Attributes:
        venue: (str) where the event will take place
        bands: (list) array of bands performing at the event
        start: (datetime) when the event starts
        link: (str) a hyperlink to the event website
        soldout: (bool) whether the event is sold out or not
    """

    def __init__(self, venue='', bands=[], start=datetime.datetime.today(),
                 link='', soldout=False):
        """Init Event with optional attributes."""
        # self.venue = venue
        # self.bands = bands
        # self.start = start
        # self.link = link
        # self.soldout = soldout
        self.__dict__.update({k: v for k, v in locals().items() if k != 'self'})

    def to_json(self):
        """Convert Event to a generic object.

        Returns:
            Object
        """
        return {
            'venue': self.venue,
            'bands': self.bands,
            'start': self.start.isoformat(),
            'link': self.link,
            'soldout': self.soldout
        }


def bowery_shows():
    """Retrieve all events for the next 12 months that are managed by Bowery Boston.

    Returns:
        an array of JSON event objects
    """
    
    print("Parsing Bowery Boston event calendar...")
    events_list = []
    r = requests.get(
        'https://www.boweryboston.com/info/events/get?scope=all&page=0&rows=9999&venues=boston')
    soup = BeautifulSoup(r.text, 'html.parser')
    events = soup.find_all('div', class_='show-item')
    for e in events:
        events_list.append(bowery_event_process(e))
    return events_list


def bowery_event_process(e):
    """Parse a single BeautifulSoup-formatted event from the Bowery Boston event calendar.

    Args:
        e: a single event (div class show-item) from the Bowery Boston event calendar in HTML format
    Returns:
        a JSON-formattable event object
    """

    # HTML example fields:
    #             Venue: <p class="list-location"><strong>The Sinclair
    #              Link: <a href="/boston/shows/detail/347671-lucy-dacus">
    #         Headliner: <div class="info-title"><h3><a href="/boston/shows/detail/347671-lucy-dacus">Lucy Dacus
    #  Supporting bands: <div class="supporting-acts"><span>with And The Kids, Adult Mom
    # Time (data-start): <a class="calendar-dropdown-item google" data-description="18 &amp; Over" data-end="2018-04-12T02:15:00Z" data-location="52 Church St., Cambridge, MA 02138"
    #                       data-start="2018-04-12T00:15:00Z" data-title="Lucy Dacus" href="" target="_blank">
    #          Sold Out: <a class="button event ticket primary" href="http://www.axs.com/events/347671/lucy-dacus-tickets" id="48591" target="_blank">Sold Out

    ev = Event()
    bands = []

    cursor = e.find('a')
    if cursor:
        ev.link = 'https://www.boweryboston.com{0}'.format(
            cursor['href'])

    cursor = e.select_one("a.calendar-dropdown-item.google")
    if cursor:
        ev.start = dateutil.parser.parse(
            cursor['data-start']).astimezone(dateutil.tz.tzlocal())

    cursor = e.find('p', class_='list-location').find('strong')
    if cursor:
        ev.venue = cursor.get_text(strip=True)

    artist_info = e.find('div', class_='info-title')
    if artist_info:
        cursor = artist_info.find('a')
        if cursor:
            if cursor.get_text(strip=True):
                bands.append(cursor.get_text(strip=True))

        cursor = e.find('div', 'supporting-acts')
        if cursor:
            supp_arr = re.sub(
                r'^with\s*', '', cursor.find('span').get_text(strip=True)).split(', ')
            for i in supp_arr:
                if i:
                    bands.append(i)

    ev.bands = bands

    cursor = e.select_one('a.button.event.ticket.primary')
    if cursor:
        if cursor.get_text(strip=True).lower() == 'sold out':
            ev.soldout = True

    return ev.to_json()


def houseofblues():
    """Retrieve all events for the next 12 months that are managed by House of Blues Boston.

    Returns:
        an array of JSON-formattable event objects
    """

    print("Parsing House of Blues event calendar...")
    events_list = []
    start_date = datetime.datetime.today()
    base_url = 'http://www.houseofblues.com/boston/api/EventCalendar/GetEvents'
    url_params = {'startDate': start_date.strftime('%m/%d/%Y'), 'endDate': start_date.replace(year=start_date.year+1).strftime('%m/%d/%Y'),
                  'venueIds': 9044, 'limit': 9999, 'offset': 1, 'genre': '', 'artist': '', 'offerType': 'STANDARD,STANDARD - Priority'}
    r = requests.get(base_url, params=url_params)
    ftext = re.sub(r'\\"', '"', r.text[1:-1], flags=re.S)
    rawobj = json.loads(ftext)
    for i in rawobj['result']:
        artist_array = i['artists']
        bands = [artist_array.pop(0)['name']]
        for a in artist_array:
            if a['name'].lower().encode('ascii', 'ignore') != i['title'].lower().encode('ascii', 'ignore'):
                bands.append(a['name'])
        ev = Event(venue=i['venueName'], bands=bands, start=dateutil.parser.parse(i['eventDate']).replace(tzinfo=dateutil.tz.tzlocal()),
                   link='http://www.houseofblues.com/boston/EventDetail?tmeventid={0}&offerid=0'.format(i['eventID']))
        if i['soldOut']:
            ev.soldout = True
        events_list.append(ev.to_json())
    return events_list


def monthly_cals():
    """Parse the venue calendars with request structures that are limited to one month at a time.

    Returns:
        An array of JSON-formattable event objects
    """

    events_list = []
    today = datetime.datetime.today().replace(day=1)
    cur_date = [today.month, today.year]
    for period in range(0, 12):
        cur_date[0] += 1
        if cur_date[0] > 12:
            cur_date[0] = 1
            cur_date[1] += 1
        date_string = '{0}/{1}'.format(cur_date[0], cur_date[1])
        r = requests.get(
            'http://www.mideastoffers.com/all-shows/?cal-month={0}&cal-year={1}'.format(cur_date[0], cur_date[1]))
        if r.status_code == 200:
            print('Parsing Middle East event calendar for {0}...'.format(
                date_string))
            events_list += middleeast(r.text)
        r = requests.get(
            'http://events.crossroadspresents.com/venues/paradise-rock-club/month_events.json?period={0}'.format(period))
        if r.status_code == 200:
            print('Parsing Paradise Rock Club event calendar for {0}...'.format(
                date_string))
            events_list += crossroads_parse(r.json())
        r = requests.get(
            'http://events.crossroadspresents.com/venues/brighton-music-hall/month_events.json?period={0}'.format(period))
        if r.status_code == 200:
            print('Parsing Brighton Music Hall event calendar for {0}...'.format(
                date_string))
            events_list += crossroads_parse(r.json())
    return events_list


def middleeast(data):
    """Retrieve all events for the next 12 months happening at the Middle East venue.

    Returns:
        an array of JSON-formattable event objects
    """
    events_list = []
    regtest = re.search(r'events: (\[.*?])', data, flags=re.S)
    if regtest:
        obj = demjson.decode(regtest.group(1))
        for i in obj:
            try:
                ventext = re.search(r'<div[^<>]*>([^<]+)', i['venue']).group(1)
                ev = Event(venue=ventext, bands=[x.strip() for x in re.split(r',|\|', i['title'])],
                           start=datetime.datetime.strptime(
                               i['start'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=dateutil.tz.tzlocal()),
                           link='http://www.mideastoffers.com/event/' + i['id'])
                events_list.append(ev.to_json())
            except:
                pass
    return events_list


def crossroads_parse(data):
    """Parse a raw JSON object returned from a request to a Crossroads-managed venue calendar.

    Args:
        data: the raw JSON data to parse
    Returns:
        an array of JSON-formattable event objects
    """

    # JSON object format example (truncated):
    # {
    #     "permalink": "/events/2018/3/2/the-expendables-through-the-roots-pacific-dub",
    #     "tz_adjusted_begin_date": "2018-03-02T18:00:00-05:00",
    #     "venue": {
    #         "title": "Paradise Rock Club"
    #     },
    #     "title": "The Expendables, Through the Roots, Pacific Dub",
    #     "sold_out": false,
    #     "artists": [{
    #             "title": "The Expendables"
    #         },{
    #             "title": "Through the Roots"
    #         },{
    #             "title": "Pacific Dub"
    #     }]
    # }

    events_list = []
    for g in data['event_groups']:
        for e in g['events']:
            if e['category_param'] == 'music':
                ev = Event(venue=e['venue']['title'], bands=[x['title'] for x in e['artists']] if e['artists'] else [e['title']],
                           start=dateutil.parser.parse(e['tz_adjusted_begin_date']), link='http://events.crossroadspresents.com' + e['permalink'])
                if e['sold_out']:
                    ev.soldout = True
                events_list.append(ev.to_json())
    return events_list
