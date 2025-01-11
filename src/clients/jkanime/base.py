import requests
import re
from bs4 import BeautifulSoup

class JKanimeClient():
    def __init__(self):
        self.base_url = "https://jkanime.net"

    def __get_headers(self, url):
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'referer': url
        }

    def __bs4_request(self, url):
        response = requests.get(url, headers=self.__get_headers(url))
        return BeautifulSoup(response.content, 'html.parser')

    def get_anime_episodes(self, name_slug):
        url = f"{self.base_url}/{name_slug}"
        episodes = []
        try:
            soup = self.__bs4_request(url)
            episodes =  [{'name':f"Episodio {x}"} for x in range(1, int((soup.find_all('a',{'class': 'numbers'})[-1]).text.strip().split(' - ')[1])+1)]
        except:
            pass
        return episodes

    def get_embed_url(self, name_slug, episode):
        regex_page_embed = r'<iframe .*?\bsrc="(/umv?.php\?.*)"\ w'
        regex_video_embed = r'url: \'(https://.*m3u8)\'|src="(https://.*m3u8)"'
        url = f"{self.base_url}/{name_slug}/{episode}"
        video_data = {
            'title': f"JKanime | {name_slug.replace('-',' ').title()} - Episodio {episode}"
        }
        try:
            soup = self.__bs4_request(url)
            script_url = ''.join(list(map(lambda script: script.text,soup.find_all('script',{"src":False}))))
            for idx, embed_path in enumerate(re.findall(regex_page_embed, script_url, re.M)):
                embed_url = f"{self.base_url}{embed_path}"
                soup = self.__bs4_request(embed_url)
                src = re.search(regex_video_embed, str(soup), re.M)
                video_data[f"option{idx+1}"] = src.group(idx+1)
        except:
            video_data['option1'] = ''
            video_data['option2'] = ''
        return video_data


    def get_last_added(self):
        recents = []
        try:
            soup = self.__bs4_request(self.base_url)
            for anime in soup.find('div', {'class':'trending__anime'}).find_all('div',{'class':'anime__item'}):
                status, type = anime.find('div', {'class':'anime__item__text'}).ul.find_all('li')
                recents.append({'name':f"[{status.text.strip()} - {type.text.strip()}] {anime.find('h5').a.text.strip()}", 'name_slug':anime.select_one('a')['href'].split('/')[-2]})
        except:
            pass
        return recents

    def get_programming(self):
        pattern = re.compile(r'\s+')
        programming = []
        try:
            soup = self.__bs4_request(self.base_url)
            for anime in soup.find('div', {'class':'anime_programing'}).find_all('a', {'class': 'bloqq'}):
                programming.append({'name': f"[Anime] {anime.select_one('h5').text.strip()}",'name_slug':anime['href'].split('/')[-3], 'episode':re.sub(pattern,' ',anime.select_one('h6').text.strip().replace('\n',''))})
            for donghua in soup.find('div', {'class':'donghuas_programing'}).find_all('a', {'class': 'bloqq'}):
                programming.append({'name': f"[Donghua] {donghua.select_one('h5').text.strip()}",'name_slug':donghua['href'].split('/')[-3], 'episode':re.sub(pattern,' ',donghua.select_one('h6').text.strip().replace('\n',''))})
        except:
            pass
        return programming

    def search_anime(self, name):
        animes = []
        try:
            for page in range(1,3):
                url = f"{self.base_url}/buscar/{name}/{page}"
                soup = self.__bs4_request(url)
                for anime in soup.find_all('div', {'class': 'anime__item__text'}):
                    status, type = anime.ul.find_all('li')
                    animes.append({'name':f"[{status.text.strip()} - {type.text.strip()}] {anime.find('h5').a.text.strip()}", 'name_slug':anime.select_one('a')['href'].split('/')[-2]})
        except:
            pass
        return animes
