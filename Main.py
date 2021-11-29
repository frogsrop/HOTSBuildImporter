from pathlib import Path
import pandas as pd
import os
import platform
import requests
from Levenshtein import ldistance


def get_data():
    response = requests.get(
        'https://docs.google.com/spreadsheet/ccc?key=1kiHfe0obByIt5qBvLNeVwrKr2SLl_laTCDqbfJwI9X8&output=csv')
    assert response.status_code == 200, 'Wrong status code'
    print(response.content)


def find_files(filename, search_path):
    result = []
    for root, dir, files in os.walk(search_path):
        if filename in files:
            result.append(os.path.join(root, filename))
    return result


def hots_root_directory():
    system = platform.system()
    if system == 'Windows':
        relative_path = 'Documents/Heroes of the Storm/Accounts/'
    elif system == 'Darwin':
        relative_path = 'Library/Application Support/Blizzard/Heroes of the Storm/Accounts/'
    else:
        raise RuntimeError(f'Unsupported OS: {system}')
    return Path.joinpath(Path.home(), relative_path)


def get_heroes_names(path):
    names = []
    with open(path) as lines:
        for line in lines:
            names.append(list())
            data = line.split('/')
            for name in data:
                names[-1].append(name.strip())
    return names


def get_builds(url):
    data = pd.read_csv(url)
    cols = data.iloc[0] == "HotS Build Link"
    data = data.loc[:, cols]
    data.drop(0, inplace=True)
    return list(data.stack().reset_index()[0])


def get_name_to_builds(builds, names):
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
                dist = min(dist, ldistance(hotsName, name))
            if dist < bestScore:
                bestScore = dist
                bestName = hotsNames[0]
        if bestName not in nameToBuild:
            nameToBuild[bestName] = []
        nameToBuild[bestName].append(ready_build)
    return nameToBuild


def get_hashes(path):
    hashes = {}
    with open(path) as lines:
        for line in lines:
            data = line.split('=')
            hashes[data[0]] = data[1].strip()
    return hashes


def get_current_hashes(path):
    current_hashes = {}
    with open(str(path), "r") as f:
        lines = f.readlines()
        for line in lines:
            line = line.split('=')
            name = line[0].strip()
            hash = line[1].split('|')[-1].strip()
            current_hashes[name] = hash
    return current_hashes


if __name__ == '__main__':
    names = get_heroes_names('names.txt')
    builds = get_builds(
        'https://docs.google.com/spreadsheet/ccc?key=1kiHfe0obByIt5qBvLNeVwrKr2SLl_laTCDqbfJwI9X8&output=csv')
    nameToBuild = get_name_to_builds(builds, names)
    old_hashes = get_hashes('hashes.txt')
    hots_root = hots_root_directory()

    new_hashes = None

    for account in os.listdir(str(hots_root)):
        path = Path.joinpath(hots_root, account + '/TalentBuilds.txt')
        current_hashes = get_current_hashes(path)
        if len(current_hashes) == len(old_hashes):
            new_hashes = current_hashes.copy()

        result = list()
        for name in nameToBuild:
            builds = nameToBuild[name]
            amount = min(len(builds), 3)
            while len(builds) < 3:
                builds.append("\"\"")
            while len(builds) > 3:
                builds.pop()

            hash = None
            if name in current_hashes:
                hash = current_hashes[name]
            else:
                hash = old_hashes[name]

            result.append('{}=Build{}|{}|{}|{}|{}'.format(name, amount, builds[0], builds[1], builds[2], hash))

        with open(str(path), "w") as f:
            for line in result:
                f.write(line)
                f.write('\n')

        # with open('hashes.txt', "w") as f:
        #     for name, hash in new_hashes.items():
        #         f.write(name + '=' + hash + '\n')
