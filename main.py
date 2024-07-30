from os import system, name
import time
import urllib.request
import json
import re

from dateutil import parser
import unidecode

staticStops = 'https://welbits.github.io/static_stops.json'
stopTimes = 'https://api.transit.welbits.com/stops/times/'


def clear():
    if name == 'nt':
        system('cls')
    else:
        system('clear')


def main():
    clear()
    search = input('Enter (l:)line, (s:)stop number or (n:)stop name.\n'
                   'Use n:<name>,l:<line>,s:<stop> separated with comas to use a complex filter.\n'
                   '([X] to exit): ')
    if search == 'X' or search == 'x':
        exit()

    search_name = ""
    search_stop = ""
    search_line_number = ""

    index = -1

    if len(search.split(',')) <= 1:
        if search.startswith("n:"):
            search = search.split('n:')[1]
            line_data = search_line_complex(search, '', '')
        elif search.startswith("s:"):
            search = search.split('s:')[1]
            line_data = search_line_complex('', search, '')
        elif search.startswith("l:"):
            search = search.split('l:')[1]
            line_data = search_line_complex('', '', search)
        else:
            line_data = search_line(search)
    else:
        for s in search.split(','):
            if s.startswith("n:"):
                search_name = s.split('n:')[1]
            elif s.startswith("s:"):
                search_stop = s.split('s:')[1]
            elif s.startswith("l:"):
                search_line_number = s.split('l:')[1]
        line_data = search_line_complex(search_name, search_stop, search_line_number)

    for d in line_data:
        index += 1
        print("[" + str(index) + "] " + str(d))
    if index > -1:
        stop_input = input(f'Enter stop index [0]' + (f' - [{index}]' if index > 0 else '') + '\n' +
                           '([X] to exit, [F] to filter again): ')
        if stop_input == 'X' or stop_input == 'x':
            exit()
        elif stop_input == 'F' or stop_input == 'f':
            main()
        else:
            clear()
            get_stop_data(str(line_data[int(stop_input)][0]))
            update_input = input('\n[U] to update, [ENTER] to restart: ')
            if update_input == 'U' or update_input == 'u':
                while True:
                    clear()
                    get_stop_data(str(line_data[int(stop_input)][0]))
                    update_input = input('\n[U] to update, [ENTER] to restart: ')
                    if update_input == 'U' or update_input == 'u':
                        continue
                    else:
                        clear()
                        break
            main()
    else:
        main()


def get_stop_by_stop_code(datum, search_filter):
    engine = re.compile(unidecode.unidecode(search_filter), re.UNICODE | re.IGNORECASE)
    if engine.search(unidecode.unidecode(list(datum)[0])):
        return list(datum)


def get_stop_by_stop_name(datum, engine):
    if engine.search(unidecode.unidecode(list(datum)[1])):
        return list(datum)
    elif engine.search(unidecode.unidecode(list(datum)[1]).split(' - ')[0]):
        return list(datum)
    elif len(list(unidecode.unidecode(list(datum)[1]).split(' - '))) > 1 and engine.search(
            unidecode.unidecode(list(datum)[1]).split(' - ')[1]):
        return list(datum)


def get_stop_by_line_number(datum, search_filter):
    for d in list(datum)[4]:
        if d == search_filter:
            return list(datum)


def search_line(search_filter):
    with urllib.request.urlopen(staticStops) as url:
        data = list(json.load(url))

    lines_data = []
    for datum in data:
        if get_stop_by_stop_code(datum, search_filter) is not None:
            lines_data.append(list(datum))
        engine = re.compile(unidecode.unidecode(search_filter), re.IGNORECASE)
        if get_stop_by_stop_name(datum, engine) is not None:
            lines_data.append(list(datum))
        if get_stop_by_line_number(datum, search_filter) is not None:
            lines_data.append(list(datum))
    return lines_data


def search_line_complex(search_name, search_stop, search_line_number):
    with urllib.request.urlopen(staticStops) as url:
        data = list(json.load(url))
    lines_data = []
    engine = re.compile(unidecode.unidecode(search_name), re.UNICODE | re.IGNORECASE)
    for datum in data:
        if search_stop != "":
            if get_stop_by_stop_code(datum, search_stop) is not None:
                if search_name != "":
                    if get_stop_by_stop_name(datum, engine) is not None:
                        if search_line_number != "":
                            if get_stop_by_line_number(datum, search_line_number) is not None:
                                lines_data.append(list(datum))
                                continue
                        else:
                            lines_data.append(list(datum))
                            continue
                elif search_line_number != "":
                    if get_stop_by_line_number(datum, search_line_number) is not None:
                        lines_data.append(list(datum))
                        continue
                else:
                    lines_data.append(list(datum))
                    continue
        elif search_name != "":
            if get_stop_by_stop_name(datum, engine) is not None:
                if search_line_number != "":
                    if get_stop_by_line_number(datum, search_line_number) is not None:
                        lines_data.append(list(datum))
                        continue
                else:
                    lines_data.append(list(datum))
                    continue
        elif search_line_number != "":
            if get_stop_by_line_number(datum, search_line_number) is not None:
                lines_data.append(list(datum))
                continue
    return lines_data


def get_stop_data(stop_code):
    with (urllib.request.urlopen(stopTimes + stop_code) as url):
        data = json.load(url)
        routes = data['routes']
        for route in routes:
            route_info = route['lineCode'] + ' direction ' + (route['routeName'].split(' - ')[1]
                                                              if len(route['routeName'].split(' - ')) > 1
                                                              else route['routeName'])
            date = route['times'][0]['arrivalDate']
            parsed = parser.parse(date)
            seconds = int(parsed.timestamp()) - int(time.time())
            minutes = seconds / 60
            hours = minutes / 60
            if int(hours) > 0:
                print(f'The next {route_info} will arrive in {int(hours)} ' +
                      ('hours' if int(hours) > 1 else 'hour') +
                      (f" at {route['platform']}" if dict(route).keys().__contains__('platform') else ''))
            elif int(minutes) > 0:
                print(f'The next {route_info} will arrive in {int(minutes)} ' +
                      ('minutes' if int(minutes) > 1 else 'minute') +
                      (f" at {route['platform']}" if dict(route).keys().__contains__('platform') else ''))
            elif int(seconds) > 1:
                print(f'The next {route_info} will arrive in {int(seconds)} seconds' +
                      (f" at {route['platform']}" if dict(route).keys().__contains__('platform') else ''))
            else:
                print(f"The next {route_info} it's arriving" +
                      (f" at {route['platform']}" if dict(route).keys().__contains__('platform') else ''))


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
