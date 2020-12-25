from os import replace
from info import BusInfo, TrainInfo, HsrInfo, User
from transitions.extensions import GraphMachine
from datetime import datetime, timedelta
from utils import push_text_message, send_text_message, send_flex_message, push_flex_message
from json_data import *
import copy
from natsort import natsorted, ns  # for nature sort

class TocMachine(GraphMachine):
    def __init__(self, **machine_configs):
        self.machine = GraphMachine(model=self, **machine_configs)
        self.user = User()
        self.bus_info = BusInfo()
        self.train_info = TrainInfo()
        self.hsr_info = HsrInfo()
        self.prev = None

    def reset(self):
        self.machine.set_state(self.machine.initial)
        self.on_enter_user()

    def on_enter_user(self, event=None):
        if self.user.user_id != None:
            push_text_message(self.user.user_id, '歡迎使用時刻表查詢系統，輸入任意文字開始')

    def is_going_to_start(self, event=None):
        self.user.user_id = event.source.user_id
        return True

    def on_enter_start(self, event=None):
        contents = get_replay_flex('start')
        send_flex_message(event.reply_token, contents)

    def is_going_to_bus_start(self, event=None):
        if event.message.type == 'text' and event.message.text == '公車查詢':
            return True
        else:
            if not (event.message.type == 'text' and (event.message.text == 'reset' or event.message.text == 'bus' or event.message.text == '火車查詢' or event.message.text == '高鐵查詢')):
                push_text_message(self.user.user_id, '無法辨識...')
            return False

    def on_enter_bus_start(self, event=None):
        self.user.bus_stops = None
        self.user.bus_route = None
        self.user.bus_direction = None
        contents = get_replay_flex('bus')
        send_flex_message(event.reply_token, contents)

    def going_bus_by_stop(self, event=None):
        if event.message.type != 'text':
            return False
        if event.message.text == '以站牌搜尋':
            return True
        else:
            # if event.message.type != 'location' and not (event.message.type == 'text' and (event.message.text == 'reset' or event.message.text == '以路線搜尋')):
            if not (event.message.text == 'reset' or event.message.text == '以路線搜尋'):
                push_text_message(self.user.user_id, '請點選上方的選項\n如要重來')
            return False

    def on_enter_bus_by_stop(self, event=None):
        send_text_message(event.reply_token, "請輸入站牌名稱")

    def going_bus_by_stop2(self, event=None):
        if event.message.type == 'text':
            if event.message.text not in self.bus_info.stops_to_route:
                push_text_message(self.user.user_id,
                                  f'找不到 {event.message.text} 站牌，目前只支援台南地區的公車站')
                return False
            else:
                self.user.bus_stops = event.message.text
                return True
        else:
            push_text_message(self.user.user_id, '請輸入公車站名字')
            return False

    def on_enter_bus_by_stop2(self, event=None):
        contents = get_replay_flex('bus_route_by_stops')  # input
        routes_list = natsorted(
            self.bus_info.stops_to_route[self.user.bus_stops])
        contents['body']['contents'][0]['text'] = self.user.bus_stops
        for route in routes_list:
            template = copy.deepcopy(button_template)
            template['action']['label'] = template['action']['text'] = route
            contents['footer']['contents'].append(template)
        send_flex_message(event.reply_token, contents)

    def goint_bus_by_route(self, event=None):
        return event.message.type == 'text' and event.message.text == '以路線搜尋'

    def on_enter_bus_by_route(self, event=None):
        send_text_message(event.reply_token, "請輸入公車號碼")

    def goint_bus_by_route2(self, event=None):
        # get shop from number
        if event.message.type == 'text':
            if event.message.text not in self.bus_info.route_to_stops:
                push_text_message(
                    self.user.user_id, f'找不到公車路線為 {event.message.text} 的公車，目前只支援台南地區的公車')
                return False
            else:
                self.user.bus_route = event.message.text
                return True
        else:
            push_text_message(self.user.user_id, '請輸入公車路線')
            return False

    def on_enter_bus_by_route2(self, event=None):
        contents = get_replay_flex('bus_stops_by_route')  # input
        stops_list = self.bus_info.route_to_stops[self.user.bus_route]
        template = copy.deepcopy(bubble_template)
        template['body']['contents'][0]['text'] = self.user.bus_route
        for i, stop in enumerate(stops_list):
            if i >= 72:  # line can not sent message which exceed 12 bubble
                break
            if i % 6 == 0:
                contents['contents'].append(copy.deepcopy(template))
            dict_template = copy.deepcopy(button_template)
            dict_template['action']['label'] = dict_template['action']['text'] = stop
            contents['contents'][-1]['footer']['contents'].append(
                dict_template)
        send_flex_message(event.reply_token, contents)

    # need google map api
    # def goint_bus_by_location(self, event = None):
    #    # get shop from location
    #    if event.message.type == 'location':
    #        return True
    #    else:
    #        return False

    # def on_enter_bus_by_location(self, event = None):
    #    contents = get_replay_flex('stops_by_location') # 附近的公車站
    #    push_flex_message(self.user.user_id, contents)

    def going_bus_direction(self, event=None):
        # print result
        if self.user.bus_route == None:
            if event.message.type == 'text':
                if event.message.text in self.bus_info.route_to_stops:
                    self.user.bus_route = event.message.text
                    contents = get_replay_flex('bus_direction')
                    push_flex_message(self.user.user_id, contents)
                    return True
                else:
                    push_text_message(self.user.user_id, '請點選上方的路線')
                    return False
            else:
                push_text_message(self.user.user_id, '請點選上方的路線')
                return False
        else:
            if event.message.type == 'text':
                if event.message.text in self.bus_info.stops_to_route:
                    self.user.bus_stops = event.message.text
                    contents = get_replay_flex('bus_direction')
                    push_flex_message(self.user.user_id, contents)
                    return True
                else:
                    push_text_message(self.user.user_id, '請點選上方的站牌名稱')
                    return False
            else:
                push_text_message(self.user.user_id, '請點選上方的站牌名稱')
                return False

    def is_going_to_bus_end(self, event=None):
        if event.message.type == 'text':
            if event.message.text in ['去程', '回程']:
                self.user.bus_direction = event.message.text
                estimates = self.bus_info.calculate(
                    self.user.bus_route, self.user.bus_stops, self.user.bus_direction)
                contents = get_replay_flex('show_bus_time')
                contents['header']['contents'][0]['text'] = self.user.bus_route
                contents['header']['contents'][1]['text'] = self.user.bus_direction
                i = 1
                # contents['body']['contents'][0]['contents'][1]['contents'][1]['borderColor'] = '#00FF00'
                # contents['body']['contents'][0]['contents'][1]['contents'][1]['backgroundColor'] = '#00FF00'
                real_time = 0
                for key, value in estimates.items():
                    if i == 3:
                        real_time = value[0]
                    contents['body']['contents'][i]['contents'][2]['text'] = key
                    if value[1] == 0:
                        # 末班車已過 or 交管
                        contents['body']['contents'][i]['contents'][0][
                            'text'] = f'{(timedelta(seconds =  value[0])).seconds // 60} 分' if value[0] != None else '不停靠'
                    elif value[1] == 1:
                        contents['body']['contents'][i]['contents'][0][
                            'text'] = f'{(timedelta(seconds =  value[0])).seconds // 60} 分' if value[0] != None else '未發車'
                    elif value[1] == 2:
                        contents['body']['contents'][i]['contents'][0]['text'] = '交管不停靠'
                    elif value[1] == 3:
                        contents['body']['contents'][i]['contents'][0]['text'] = '末班車已過'
                    elif value[1] == 4:
                        contents['body']['contents'][i]['contents'][0]['text'] = '今日未營運'
                    else:
                        # 末班車已過 or 交管
                        contents['body']['contents'][i]['contents'][0]['text'] = '不停靠'
                    i += 2
                contents['header']['contents'][1]['text'] = self.user.bus_direction
                contents['body']['contents'][0][
                    'text'] = f'預計到達時間: {int(real_time / 60)} 分鐘' if real_time != None else ' '
                send_flex_message(event.reply_token, contents)
                return True
            else:
                push_text_message(self.user.user_id, '請輸入正確的方向')
                return False
        else:
            push_text_message(self.user.user_id, '請輸入正確的方向')
            return False

    def on_enter_bus_end(self, event=None):
        self.machine.set_state(self.machine.initial)

    def is_going_to_train(self, event=None):
        return event.message.type == 'text' and event.message.text == '火車查詢'

    def on_enter_train_start(self, event=None):
        self.train_info.start_station = None
        self.train_info.end_station = None
        contents = get_replay_flex('train_start')
        send_flex_message(event.reply_token, contents)

    def going_train_start_station(self, event=None):
        if event.message.type == 'text' and event.message.text in self.train_info.available_station:
            self.user.train_start_station = event.message.text
            return True
        else:
            push_text_message(self.user.user_id, '請選擇上方的車站')
            return False

    def on_enter_train_start_station(self, event=None):
        contents = get_replay_flex('train_end')
        send_flex_message(event.reply_token, contents)

    def going_train_end_station(self, event=None):
        if event.message.type == 'text' and event.message.text in self.train_info.available_station:
            if event.message.text == self.user.train_start_station:
                push_text_message(self.user.user_id, "起訖站不可相同")
                return False
            else:
                self.user.train_end_station = event.message.text
                return True
        else:
            push_text_message(self.user.user_id, '請選擇上方的車站')
            return False

    def on_enter_train_end_station(self, event=None):
        contents = get_replay_flex('train_date')
        contents['header']['contents'][0]['contents'][1]['text'] = self.user.train_start_station
        contents['header']['contents'][1]['contents'][1]['text'] = self.user.train_end_station
        send_flex_message(event.reply_token, contents)

    def going_train_time(self, event=None):
        if event.type == 'postback':
            self.user.train_date = event.postback.params['datetime']
            times = self.train_info.calculate(
                self.user.train_start_station, self.user.train_end_station, self.user.train_date)
            contents = get_replay_flex('show_train_time')

            for t in times:
                copy_template = copy.deepcopy(train_time_template)
                copy_template['header']['contents'][0]['contents'][0]['contents'][1]['text'] = self.user.train_start_station
                copy_template['header']['contents'][0]['contents'][1]['contents'][1]['text'] = self.user.train_end_station
                copy_template['header']['contents'][1][
                    'contents'][0]['text'] = f'車號 {t[2]}'
                # too long
                copy_template['header']['contents'][1][
                    'contents'][1]['text'] = f'{t[3][:2]}'
                delay = self.train_info.delay(t[2])
                if delay != 0:
                    copy_template['body']['contents'][0]['contents'][1]['contents'][1]['borderColor'] = '#EF4520'
                    copy_template['body']['contents'][0]['contents'][1]['contents'][1]['backgroundColor'] = '#EF4520'
                    copy_template['body']['contents'][0]['contents'][
                        2]['text'] = f'誤點 {int(delay / 60)} 分鐘'
                else:
                    copy_template['body']['contents'][0]['contents'][2]['text'] = f'正常'
                td = datetime.strptime(t[1], "%H:%M") - \
                    datetime.strptime(t[0], "%H:%M")
                copy_template['body']['contents'][2][
                    'text'] = f'Total: {td.seconds // 3600} hours {(td.seconds // 60) % 60} minutes'
                copy_template['body']['contents'][3]['contents'][0]['text'] = t[0]
                copy_template['body']['contents'][3]['contents'][2]['text'] = self.user.train_start_station
                copy_template['body']['contents'][5]['contents'][0]['text'] = t[1]
                copy_template['body']['contents'][5]['contents'][2]['text'] = self.user.train_end_station

                contents['contents'].append(copy_template)

            if len(times) == 0:
                send_text_message(event.reply_token,
                                  f"{self.user.train_date} 之後沒有可以搭乘的列車")
            else:
                send_flex_message(event.reply_token, contents)
            return True
        else:
            push_text_message(self.user.user_id, '請輸入正確的日期')
            return False

    def on_enter_train_time(self, event=None):
        self.machine.set_state(self.machine.initial)

    def is_going_to_hsr(self, event=None):
        return event.message.type == 'text' and event.message.text == '高鐵查詢'

    def on_enter_hsr_start(self, event=None):
        self.train_info.start_station = None
        self.train_info.end_station = None
        contents = get_replay_flex('hsr_start')
        send_flex_message(event.reply_token, contents)

    def going_hsr_start_station(self, event=None):
        if event.message.type == 'text' and event.message.text in self.hsr_info.available_station:
            self.user.hsr_start_station = event.message.text
            return True
        else:
            push_text_message(self.user.user_id, '請選擇上方的車站')
            return False

    def on_enter_hsr_start_station(self, event=None):
        contents = get_replay_flex('hsr_end')
        send_flex_message(event.reply_token, contents)

    def going_hsr_end_station(self, event=None):
        if event.message.type == 'text' and event.message.text in self.hsr_info.available_station:
            if event.message.text == self.user.hsr_start_station:
                push_text_message(self.user.user_id, "起訖站不可相同")
                return False
            else:
                self.user.hsr_end_station = event.message.text
                return True
        else:
            push_text_message(self.user.user_id, '請選擇上方的車站')
            return False

    def on_enter_hsr_end_station(self, event=None):
        contents = get_replay_flex('train_date')
        contents['header']['contents'][0]['contents'][1]['text'] = self.user.hsr_start_station
        contents['header']['contents'][1]['contents'][1]['text'] = self.user.hsr_end_station
        send_flex_message(event.reply_token, contents)

    def going_hsr_time(self, event=None):
        if event.type == 'postback':
            self.user.hsr_date = event.postback.params['datetime']
            times = self.hsr_info.calculate(
                self.user.hsr_start_station, self.user.hsr_end_station, self.user.hsr_date)
            contents = get_replay_flex('show_hsr_time')

            for t in times:
                copy_template = copy.deepcopy(rail_time_template)
                copy_template['header']['contents'][0]['contents'][0]['contents'][1]['text'] = self.user.hsr_start_station
                copy_template['header']['contents'][0]['contents'][1]['contents'][1]['text'] = self.user.hsr_end_station
                copy_template['header']['contents'][1][
                    'contents'][0]['text'] = f'{t[2]}'
                available = self.hsr_info.available_seats(
                    t[2], t[3], self.user.hsr_date, self.user.hsr_start_station)
                if not available:
                    copy_template['body']['contents'][0]['contents'][1]['contents'][1]['borderColor'] = '#EF4520'
                    copy_template['body']['contents'][0]['contents'][1]['contents'][1]['backgroundColor'] = '#EF4520'
                    copy_template['body']['contents'][0]['contents'][2]['text'] = '沒有空位'
                td = datetime.strptime(t[1], "%H:%M") - \
                    datetime.strptime(t[0], "%H:%M")
                copy_template['body']['contents'][2][
                    'text'] = f'Total: {td.seconds // 3600} hours {(td.seconds // 60) % 60} minutes'
                copy_template['body']['contents'][3]['contents'][0]['text'] = t[0]
                copy_template['body']['contents'][3]['contents'][2]['text'] = self.user.hsr_start_station
                copy_template['body']['contents'][5]['contents'][0]['text'] = t[1]
                copy_template['body']['contents'][5]['contents'][2]['text'] = self.user.hsr_end_station
                contents['contents'].append(copy_template)

            if len(times) == 0:
                send_text_message(event.reply_token,
                                  f'{self.user.hsr_date} 之後沒有可以搭乘的列車')
            else:
                send_flex_message(event.reply_token, contents)
            return True
        else:
            push_text_message(self.user.user_id, '請輸入正確的日期')
            return False

    def on_enter_hsr_time(self, event=None):
        self.machine.set_state(self.machine.initial)