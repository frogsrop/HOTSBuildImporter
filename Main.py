import io
from pathlib import Path
# import requests
# from html.parser import HTMLParser
# from bs4 import BeautifulSoup
import pandas as pd
import Levenshtein
import os
import platform


# class MyHTMLParser(HTMLParser):
#
#     def handle_starttag(self, tag, attrs):
#         if tag == 'table' and attrs['id'] == 'ctl00_MainContent_RadGridHeroTalentStatistics_ctl00':
#             self.allow = True
#         else:
#             self.allow = False
#
#     def handle_endtag(self, tag):
#         print("Encountered an end tag :", tag)
#
#     def handle_data(self, data):
#         if (self.allow):
#             print(data)
#
#
# def executeInfo(tr):
#     data = list(tr.children)
#     return data[4].text, data[6].text
#
#
# def getHeroInfo(name):
#     url = 'https://www.hotslogs.com/Sitewide/HeroDetails'
#     r = requests.get(url=url, params='Hero=' + name)
#     soup = BeautifulSoup(r.content, features='lxml')
#     tbody = soup.find('tbody')
#     levels = list()
#     for child in tbody.find_all('tr'):
#         if child.get('class')[0] == "rgGroupHeader":
#             levels.append(list())
#             continue
#         levels[-1].append(executeInfo(child))
#     t = 1
#     for level in levels:
#         print(t)
#         t += 1
#         print(level)
#     return levels
#
#
# def getNames():
#     url = 'https://www.hotslogs.com/Sitewide/HeroDetails'
#     r = requests.get(url=url)
#     soup = BeautifulSoup(r.content, features='lxml')
#     heroesList = soup.find_all('ul', {'class': 'rddlList'})[1]
#     names = list()
#     for name in heroesList.find_all("li"):
#         names.append(name.text)
#     return names
#
#
# def loadAllData():
#     names = getNames()
#     for name in names:
#         getHeroInfo(name)


def find_files(filename, search_path):
    result = []
    for root, dir, files in os.walk(search_path):
        if filename in files:
            result.append(os.path.join(root, filename))
    return result


def hots_root_directory():
    system = platform.system()
    if system == 'Windows':
        relative_path = 'Documents/Heroes of the Storm'
    elif system == 'Darwin':
        relative_path = 'Library/Application Support/Blizzard/Heroes of the Storm/Accounts/'
    else:
        raise RuntimeError(f'Unsupported OS: {system}')
    return Path.joinpath(Path.home(), relative_path)


if __name__ == '__main__':
    hashes = {}
    with open('hashes.txt') as lines:
        for line in lines:
            data = line.split('=')
            hashes[data[0]] = data[1].strip()
    names = []
    with open('names.txt') as lines:
        for line in lines:
            names.append(list())
            data = line.split('/')
            for name in data:
                names[-1].append(name.strip())

    data = pd.read_csv('data.csv')
    cols = data.iloc[0] == "HotS Build Link"
    data = data.loc[:, cols]
    data.drop(0, inplace=True)
    builds = list(data.stack().reset_index()[0])
    nameToBuild = {}
    for build in builds:
        info = build[2:-1].split(',')
        talents = info[0]
        name = info[1]
        ready_build = ""
        for talent in talents:
            ready_build += str(2 ** (int(talent) - 1)).zfill(2)
        bestName = ""
        bestScore = 100
        for hotsNames in names:
            dist = 100
            for hotsName in hotsNames:
                dist = min(dist, Levenshtein.distance(hotsName, name))
            if dist < bestScore:
                bestScore = dist
                bestName = hotsNames[0]
        if bestName not in nameToBuild:
            nameToBuild[bestName] = []
        nameToBuild[bestName].append(ready_build)
    result = list()
    for name in nameToBuild:
        builds = nameToBuild[name]
        amount = min(len(builds), 3)
        while len(builds) < 3:
            builds.append("\"\"")
        while len(builds) > 3:
            builds.pop()
        result.append('{}=Build{}|{}|{}|{}|{}'.format(name, amount, builds[0], builds[1], builds[2], hashes[name]))

    hots_root = hots_root_directory()
    for file in find_files('TalentBuilds.txt', hots_root):
        with open(file, "w") as f:
            for line in result:
                f.write(line)
                f.write('\n')
