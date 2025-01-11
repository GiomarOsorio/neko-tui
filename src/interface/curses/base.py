import curses
import json
import os
from datetime import datetime, timezone
from clients import JKanimeClient
from consts import VERSION, NEKO_LOGO, NEKO_NAME
from pathlib import Path
from players import MpvPlayer 

class InterfaceClient:
    def __init__(self):
        self.anime_client = JKanimeClient()
        self.content_stack = {}
        self.hw = self.cw = self.fw = None
        self.favs = []
        self.favs_file_name = 'favs.json'
        self.favs_path_file = f"{Path.home()}/.local/share/nekotui"
        self.logo = None
        self.menu = ['Programación','Ultimos añadidos', 'Favoritos', 'Buscar']
        self.menu_int = {
            'prog': [ord('p'), ord('P')],
            'last': [ord('u'), ord('U')],
            'fav': [ord('f'), ord('F')],
            'search': [ord('b'), ord('B')],
        }
        self.level_selected = "level1"
        self.menu_selected = -1
        self.player = MpvPlayer()
        self.status_message_text = ''
        self.version_text = f"Version: {VERSION}"

    def __can_update_data(self, saved_time):
        if saved_time is None:
            return True
        current_time = self.__get_time()
        return True if (current_time - saved_time) > 60 else False

    def __clear_windows(self, *args):
        for win in args:
            win.clear()
            win.border()

    def __get_from_path(self, data, path):
        curr = data
        path = path.split(".")[1:]
        while(len(path)):
            key = path.pop(0)
            curr = curr.get(key)
            if (type(curr) is not dict and len(path)):
                return None 
        return curr

    def __get_time(self):
        return datetime.now(timezone.utc).timestamp() * 1000

    def __refresh_windows(self, *args):
        for win in args:
             win.refresh()

    def __render_header_bar(self):
        _, w = self.hw.getmaxyx()
        y = 1
        mitems = len(self.menu)
        menu_keys = list(self.menu_int.keys())
        for idx, menu in enumerate(self.menu):
            x = w//(4*mitems) + (idx*w//mitems)
            if menu_keys[idx] == self.menu_selected:
                self.hw.attron(curses.color_pair(1))
                self.hw.addstr(y, x, f"[{menu[0]}]{menu[1:]}")
                self.hw.attroff(curses.color_pair(1))
            else:
                self.hw.addstr(y, x, f"[{menu[0]}]{menu[1:]}")
        self.__refresh_windows(self.hw)

    def __render_content(self, selected=0):
        h, w = self.cw.getmaxyx()
        data = None
        if len(self.content_stack.keys()) == 0:
            lnlines = len(self.logo.split('\n'))
            lncols = len(self.logo.split('\n')[0])
            bnlines = (h-2-lnlines)//2 + 1
            bncols = (w-2-lncols)//2 + 1
            self.__clear_windows(self.cw)
            for idx, line in enumerate(self.logo.split('\n')):
                self.cw.addstr(bnlines + idx, bncols, line)
        else:
            self.content_stack[self.menu_selected][self.level_selected]['data'] = self.content_stack[self.menu_selected][self.level_selected]['data']
            data = self.content_stack[self.menu_selected][self.level_selected]['data']
            x = 1
            self.__clear_windows(self.cw)
            for idx, line in enumerate(data):
                if idx == (h-2):
                    break
                y = 1 + idx
                max_wlength = w-5
                name = line['name'] if max_wlength >= len(line['name']) else f"{line['name'][0:max_wlength]}..."
                if idx == selected:
                    self.cw.attron(curses.color_pair(1))
                    self.cw.addstr(y, x, name)
                    self.cw.attroff(curses.color_pair(1))
                else:
                    self.cw.addstr(y, x, name)

        self.__refresh_windows(self.cw)

    def __render_search_anime(self,screen):
        h, w = self.cw.getmaxyx()
        self.__clear_windows(self.cw)
        data = []
        self.cw.addstr(1, 1, 'Buscar Anime:')
        curses.echo()
        search_query = self.cw.getstr(1, 15, w-17).decode('utf-8')
        self.cw.addstr(2, 1, 'Buscando por favor espere...')
        curses.noecho()
        if search_query:
            data = self.anime_client.search_anime(search_query)
        self.content_stack[self.menu_selected] = {}
        self.content_stack[self.menu_selected][self.level_selected] = {
            'data': data[0:h-2],
            'ts': self.__get_time()
        }

    def __render_status_bar(self):
        h, w = self.fw.getmaxyx()
        self.fw.addstr(h-2, 1, self.status_message_text)
        self.fw.addstr(h-2, w-(len(self.version_text)+1), self.version_text)
        self.__refresh_windows(self.fw)

    def __render_windows(self, screen):                                         
        h, w = screen.getmaxyx()
        hnlines = 3
        hncols = w
        fnlines= 3
        fncols = w
        cnlines = h - hnlines - fnlines 
        cncols = w
        # header window
        self.hw = curses.newwin(hnlines, hncols, 0, 0)
        self.hw.border()
        # content window
        self.cw = curses.newwin(cnlines, cncols, hnlines, 0)
        self.cw.border()
        # footer window
        self.fw = curses.newwin(fnlines, fncols, hnlines+cnlines, 0)
        self.fw.border()
        # refresh screen and wins
        self.__refresh_windows(screen, self.hw, self.cw, self.fw)

    def __read_favs(self):
        if os.path.isfile(f"{self.favs_path_file}/{self.favs_file_name}") and os.access(f"{self.favs_path_file}/{self.favs_file_name}", os.R_OK):
            pass
            with open(f"{self.favs_path_file}/{self.favs_file_name}") as f:
                self.favs = json.load(f)
        else:
            self.__save_favs()

    def __save_favs(self):
        if not os.path.exists(self.favs_path_file):
            os.makedirs(self.favs_path_file)
        with open(f"{self.favs_path_file}/{self.favs_file_name}", 'w', encoding='utf-8') as f:
            json.dump(self.favs, f, ensure_ascii=False, indent=4)

    def main(self, screen):
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.curs_set(0)
        
        self.status_message_text = "Presione 'q' para salir."
        self.__render_windows(screen)
        self.logo = NEKO_LOGO if len(NEKO_LOGO.split('\n')[0]) < (self.cw.getmaxyx()[0]-2) else NEKO_NAME
        self.__render_header_bar()
        self.__render_content()
        self.__render_status_bar()

        k = 0
        selected = 0
        while k != ord('q'):
            h = self.cw.getmaxyx()[0]-2
            k = screen.getch()
            if k in self.menu_int['prog'] and self.menu_selected != 'prog':
                self.menu_selected = 'prog'
                self.level_selected = 'level1'
                self.__render_header_bar()
                if self.__can_update_data(self.__get_from_path(self.content_stack, f"{self.menu_selected}.level1.ts")):
                    self.content_stack[self.menu_selected] = {'level1':{'data': self.anime_client.get_programming()[0:h],'ts': self.__get_time()}}
            elif k in self.menu_int['last'] and self.menu_selected != 'last':
                self.menu_selected = 'last'
                self.level_selected = 'level1'
                self.__render_header_bar()
                if self.__can_update_data(self.__get_from_path(self.content_stack, f"{self.menu_selected}.level1.ts")):
                    self.content_stack[self.menu_selected] = {'level1': {'data': self.anime_client.get_last_added()[0:h],'ts': self.__get_time()}}
            elif k in self.menu_int['fav'] and self.menu_selected != 'fav':
                self.menu_selected = 'fav'
                self.level_selected = 'level1'
                self.__read_favs()
                self.content_stack[self.menu_selected] = {}
                self.content_stack[self.menu_selected][self.level_selected] = {
                    'data': self.favs[0:h]
                }
                self.__render_header_bar()
                selected = 0
            elif k in self.menu_int['search'] and self.menu_selected != 'search':
                self.level_selected = 'level1'
                self.menu_selected = 'search'
                self.__render_header_bar()
                self.__render_search_anime(screen)
            elif k  == ord('ć') and self.level_selected == 'level2':
                self.level_selected = 'level1'
                selected = 0
            elif k == curses.KEY_UP and selected > 0:
                selected -= 1
            elif k == curses.KEY_DOWN and selected < len(self.content_stack[self.menu_selected][self.level_selected]['data']) - 1:
                selected += 1
            elif k == ord('a') and self.menu_selected != -1 and self.level_selected == 'level1':
                self.favs.append(self.content_stack[self.menu_selected][self.level_selected]['data'][selected])
                self.__save_favs()
            self.__render_content(selected)
            if k == 10:
                if  self.level_selected == 'level2':
                    video_data = self.anime_client.get_embed_url(name_slug, selected+1)
                    title = video_data['title']
                    video_url = video_data['option1']
                    self.player.player_video(title, video_url)
                elif self.__can_update_data(self.__get_from_path(self.content_stack, f"{self.menu_selected}.level2.ts")):
                    name_slug = self.content_stack[self.menu_selected][self.level_selected]['data'][selected]['name_slug']
                    self.content_stack[self.menu_selected]['level2'] = {'data': self.anime_client.get_anime_episodes(name_slug), 'ts': self.__get_time()}
                self.level_selected = 'level2'
                selected = 0
            self.__render_content(selected)

    def run(self):
        curses.wrapper(self.main)
