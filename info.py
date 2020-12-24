import requests
import sys
from datetime import datetime
from hashlib import sha1
import hmac
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import base64
from requests import request
from pprint import pprint
import urllib.parse


class Auth():

    def __init__(self):
        self.app_id = 'd1aeb0bced9944daa490d2678b5e419f'
        self.app_key = 'QeY3pEDsfoH1chqh7z9Cbqm-PFE'

    def get_auth_header(self):
        xdate = format_date_time(mktime(datetime.now().timetuple()))
        hashed = hmac.new(self.app_key.encode('utf8'),
                          ('x-date: ' + xdate).encode('utf8'), sha1)
        signature = base64.b64encode(hashed.digest()).decode()

        authorization = 'hmac username="' + self.app_id + '", ' + \
                        'algorithm="hmac-sha1", ' + \
                        'headers="x-date", ' + \
                        'signature="' + signature + '"'
        return {
            'Authorization': authorization,
            'x-date': format_date_time(mktime(datetime.now().timetuple())),
            'Accept - Encoding': 'gzip'
        }


class WebAPI():
    def __init__(self) -> None:
        super().__init__()
        self.auth = Auth()
        #self.headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
        self.headers = self.auth.get_auth_header()


class BusInfo(WebAPI):
    def __init__(self) -> None:
        super().__init__()
        self.stops_to_route = {}  # key: bus stops name, value: a list of routes name
        self.route_to_stops = {}  # key: route name, value: a list of stops name
        # key: route name, value: a list of dictionary which has
        self.bus_route_stops_infomation = {}
        # 1. key: "Direction" and value: route direction
        # 2. key: "Stops"     and value: a list of tuple(stops id, stops name) that is ordered

        self.stop_route_url = 'https://ptx.transportdata.tw/MOTC/v2/Bus/DisplayStopOfRoute/City/Tainan?$select=RouteID%2CRouteName%2CStops&$top=10000&$format=JSON'
        self.estimate_url = 'https://ptx.transportdata.tw/MOTC/v2/Bus/EstimatedTimeOfArrival/City/Tainan/'
        self.subroute_url = 'https://ptx.transportdata.tw/MOTC/v2/Bus/Route/City/Tainan/'
        self.prepare()

    def prepare(self):
        # get tainan bus routes and stops
        response = requests.get(self.stop_route_url,
                                headers=self.headers).json()
        for route in response:
            stops = []

            for stop in route['Stops']:
                stops.append((stop['StopID'], stop['StopName']['Zh_tw']))

                if not self.stops_to_route.get(stop['StopName']['Zh_tw']):
                    self.stops_to_route[stop['StopName']['Zh_tw']] = set()
                self.stops_to_route[stop['StopName']['Zh_tw']].add(
                    route['RouteName']['Zh_tw'])

                if not self.route_to_stops.get(route['RouteName']['Zh_tw']):
                    self.route_to_stops[route['RouteName']['Zh_tw']] = set()
                self.route_to_stops[route['RouteName']['Zh_tw']].add(
                    stop['StopName']['Zh_tw'])

            tmp = {"Direction": route["Direction"]}
            tmp["Stops"] = stops

            if self.bus_route_stops_infomation.get(route["RouteName"]["Zh_tw"]) == None:
                self.bus_route_stops_infomation[route["RouteName"]["Zh_tw"]] = [
                ]
            self.bus_route_stops_infomation[route["RouteName"]["Zh_tw"]].append(
                tmp)

    def calculate(self, route, stop, direction):
        """
        given route and stop, return three stop which is the nearest stop with input stop and their estimate time
        """
        three_stops = []  # the stops which would be show on timetable
        _direction = 0 if direction == "去程" else 1
        stops_len = 0

        # find the nearest three stops base on input stop
        for item in self.bus_route_stops_infomation[route]:
            pos = -1
            if item["Direction"] == _direction:
                stops_len = len(item["Stops"])
                for i, _stop in enumerate(item["Stops"]):
                    if _stop[1] == stop:
                        pos = i
                        break
                pos = min(pos, stops_len - 2)
                pos = max(1, pos)
                for i in range(pos - 1, pos + 2):
                    three_stops.append(item['Stops'][i][1])
                break

        # TODO sub route don't exist
        sub_response = requests.get(
            self.subroute_url + route + '?$top=1000&$format=JSON', headers=self.headers).json()

        subroute_to_dir = {}  # {"100190": 0, "100191": 1, "100192": 0, "100193": 1}
        # {'10160': ['101600', '101601', '101602'], ...}
        route_to_subroute = {}

        # prepare data
        print(sub_response)
        for _route in sub_response:
            for sub_route in _route['SubRoutes']:
                subroute_to_dir[sub_route['SubRouteID']
                                ] = sub_route['Direction']
                if route_to_subroute.get(_route['RouteName']['Zh_tw']) == None:
                    route_to_subroute[_route['RouteName']['Zh_tw']] = [
                        sub_route['SubRouteID']]
                else:
                    route_to_subroute[_route['RouteName']['Zh_tw']].append(
                        sub_route['SubRouteID'])

        # prepare url from subroute
        # TODO shouldn't use subroute to find because some bus stops infomation does not have this attribute
        append_str = ''
        dict_len = len(route_to_subroute[route])
        for i, sub in enumerate(route_to_subroute[route]):
            append_str += urllib.parse.quote(f"SubRouteID eq '{sub}'")
            if i != dict_len - 1:
                append_str += urllib.parse.quote(" or ")
        url = f'{self.estimate_url}{route}?$select=RouteName%2CStopName%2CSubRouteID%2CEstimateTime%2CStopStatus%2CDirection&$filter={append_str}&$top=1000&$format=JSON'

        response = requests.get(url, headers=self.headers).json()

        estimate = [None, None, None]
        stop_status = [None, None, None]

        for _route in response:
            if _route['RouteName']["Zh_tw"] == route and _route['StopName']['Zh_tw'] in three_stops:
                # because bus don't always departure, this will handle this situation and find correspondence direction
                if _route['Direction'] == 255:
                    route_direction = subroute_to_dir[_route['SubRouteID']]
                else:
                    route_direction = _route['Direction']
                if _direction == route_direction:
                    idx = three_stops.index(_route['StopName']['Zh_tw'])
                    stop_status[idx] = _route.get('StopStatus')
                    estimate[idx] = _route.get('EstimateTime')

        return {three_stops[0]: [estimate[0], stop_status[0]], three_stops[1]: [estimate[1], stop_status[1]], three_stops[2]: [estimate[2], stop_status[2]]}


class TrainInfo(WebAPI):
    def __init__(self) -> None:
        super().__init__()
        self.available_station = None  # store current support train station
        self.station_to_id = {}  # key: station name, value: station id

        self.train_station_url = 'https://ptx.transportdata.tw/MOTC/v2/Rail/TRA/Station?$select=StationName%2C%20StationID&$top=1000&$format=JSON'
        self.train_url = 'https://ptx.transportdata.tw/MOTC/v2/Rail/TRA/DailyTimetable/OD/'
        self.delay_url = 'https://ptx.transportdata.tw/MOTC/v2/Rail/TRA/LiveTrainDelay?$top=1000&$format=JSON'
        self.prepare()

    def prepare(self):
        self.available_station = ['基隆', '七堵', '南港', '松山', '臺北', '萬華',
                                  '板橋', '樹林', '桃園', '新竹', '中壢', '竹南',
                                  '苗栗', '豐原', '臺中', '彰化', '員林', '斗六',
                                  '嘉義', '新營', '臺南', '岡山', '新左營', '高雄',
                                  '屏東', '潮州', '臺東', '玉里', '花蓮', '蘇澳新',
                                  '宜蘭', '瑞芳']
        response = requests.get(self.train_station_url,
                                headers=self.headers).json()
        for station in response:
            if station['StationName']['Zh_tw'] in self.available_station:
                self.station_to_id[station['StationName']
                                   ['Zh_tw']] = station['StationID']

    def calculate(self, start_station, end_station, date):
        """
        given start, end station and date, return timetable accroding to date
        """
        _date = date[:10]  # year-month-day
        hour = date[11:]  # hour:minute

        response = requests.get(self.train_url + self.station_to_id[start_station] + '/to/' +
                                self.station_to_id[end_station] + '/' + _date + '?$top=1000&$format=JSON',  headers=self.headers).json()

        time = []
        for train in response:
            time.append((train['OriginStopTime']['DepartureTime'], train['DestinationStopTime']['ArrivalTime'],
                         train['DailyTrainInfo']['TrainNo'], train['DailyTrainInfo']['TrainTypeName']['Zh_tw']))

        hours_datetime = datetime.strptime(hour, "%H:%M")
        time = [i for i in time if datetime.strptime(
            i[0], "%H:%M") >= hours_datetime]  # remove past time data
        time.sort(key=lambda x: hours_datetime -
                  datetime.strptime(x[0], "%H:%M"))  # sort
        time.reverse()  # small first

        if len(time) > 3:
            time = time[:4]  # cut the list to show most three data

        return time

    def delay(self, train_no):
        """
        get the delay infomation
        """
        response = requests.get(self.delay_url,  headers=self.headers).json()
        for train in response:
            if train["TrainNo"] == train_no:
                return train["DelayTime"]
        else:
            return 0


class HsrInfo(WebAPI):
    def __init__(self) -> None:
        super().__init__()
        self.available_station = None
        self.start_station = None
        self.end_station = None
        self.station_to_id = {}  # key: station name, value: station id

        self.hsr_station_url = 'https://ptx.transportdata.tw/MOTC/v2/Rail/THSR/Station?$select=StationName%2C%20StationID&$top=1000&$format=JSON'
        self.seat_url = 'https://ptx.transportdata.tw/MOTC/v2/Rail/THSR/AvailableSeatStatus/Train/Leg/TrainDate/'
        self.hsr_url = 'https://ptx.transportdata.tw/MOTC/v2/Rail/THSR/DailyTimetable/OD/'
        self.prepare()

    def prepare(self):
        self.available_station = ['南港', '台北', '板橋', '桃園',
                                  '新竹', '苗栗', '台中', '彰化', '雲林', '嘉義', '台南', '左營']
        response = requests.get(self.hsr_station_url,
                                headers=self.headers).json()
        for station in response:
            if station['StationName']['Zh_tw'] in self.available_station:
                self.station_to_id[station['StationName']
                                   ['Zh_tw']] = station['StationID']

    def calculate(self, start_station, end_station, date):
        """
        given start, end station and date, return timetable accroding to date
        """
        _date = date[:10]
        hour = date[11:]

        response = requests.get(self.hsr_url + self.station_to_id[start_station] + '/to/' +
                                self.station_to_id[end_station] + '/' + _date + '?$top=1000&$format=JSON',  headers=self.headers).json()

        time = []
        for rail in response:
            time.append((rail['OriginStopTime']['DepartureTime'], rail['DestinationStopTime']
                         ['ArrivalTime'], rail['DailyTrainInfo']['TrainNo'], rail['DailyTrainInfo']['Direction']))

        hours_datetime = datetime.strptime(hour, "%H:%M")
        time = [i for i in time if datetime.strptime(
            i[0], "%H:%M") >= hours_datetime]
        time.sort(key=lambda x: hours_datetime -
                  datetime.strptime(x[0], "%H:%M"))
        time.reverse()

        if len(time) > 3:
            time = time[:4]
        return time

    def available_seats(self, train_no, direction, date, station):
        response = requests.get(
            self.seat_url + date[:10] + '?$top=1000&$format=JSON',  headers=self.headers).json()
        for train in response['AvailableSeats']:
            if train["TrainNo"] == train_no and train['Direction'] == direction:
                for end in train['StopStations']:
                    if end['StationName']['Zh_tw'] == station:
                        return end['StandardSeatStatus'] == 'O'
        else:
            return False


class User():
    def __init__(self) -> None:
        super().__init__()
        self.bus_stops = None
        self.bus_route = None
        self.bus_direction = None
        self.train_start_station = None
        self.train_end_station = None
        self.train_date = None
        self.hsr_start_station = None
        self.hsr_end_station = None
        self.hsr_date = None
        self.user_id = None