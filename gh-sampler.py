#!/bin/python3

import argparse
import json
import requests
import random
import sys
import time
import datetime
import math
import base64

parser = argparse.ArgumentParser('gh-sampler.py')
parser.add_argument('-t', dest='token', nargs='+', metavar='<API token>', help='one or more valid GitHub API token(s)', required=True)
parser.add_argument('-i', dest='input', metavar='<input file>', default=False, help='restrict search to a JSON encoded list of repositories, this can be used to refine results', required=False)
parser.add_argument('-o', dest='output', metavar='<output file>', default=False, help='output results to the specified file (otherwise STDOUT)', required=False)
parser.add_argument('-l', dest='language', metavar='<language>', default=False, help='restrict search to repositories in a certain programing language, e.g. C', required=False)
parser.add_argument('-f', dest='filename', metavar='<file name>', help='restrict search to certain file(s) in the repository', nargs='*', required=False)
parser.add_argument('-c', dest='keyword', metavar='<keyword>', help='restrict search to certain keyword(s) in the repository', nargs='*', required=False)
parser.add_argument('-s', dest='stars', metavar='<min stars>', default=5, type=int, help='minimum number of stars a repo must have', required=False)
arguments = parser.parse_args(sys.argv[1:])

# we need a API token, as the limits for non-autheticated users are way too restricted
# (we could also force the user to provide a token by setting the parameter 'required' in line 10 to True, but this error message is prettier)
if (not arguments.token):
    print('A GitHub API token is required - get it here: https://github.com/settings/tokens')
    parser.print_usage()
    exit(1)

def github_rest_call(query: str) -> tuple[int, dict]:
    # return the status code and the dict with the decoded JSON data
    while True:
        try:
            _response = requests.get(f'https://api.github.com/{ query }', headers={'Authorization': f'Bearer { random.choice(arguments.token) }'})
        except Exception as e:
            print(f'  Connection Error ({ e }) - waiting 15 seconds')
            time.sleep(20)
            continue
        if (_response.status_code != 200):
            try:
                if (int(_response.headers['x-ratelimit-remaining']) <= 1):
                    # GitHub API is not using UTC but local time ... why ...
                    _wait_time = max(int(_response.headers['x-ratelimit-reset']) - int(datetime.datetime.now().timestamp()), 2)
                    print(f'  API quota exceeded, waiting { _wait_time } seconds')
                    time.sleep(_wait_time)
                    continue
                # this could break if GitHub changes their phrasing
                elif ('rate limit' in _response.json()["message"]):
                    print(f'  Secondary rate limit exceeded, waiting 15 seconds')
                    time.sleep(15)
                    continue
                else:
                    print(f'  API returned status { _response.status_code }\n  Headers: { _response.headers }')
            except KeyError:
                time.sleep(15)
                print(f'  Unknown exception: API returned status { _response.status_code }')#\n  Headers: { _response.headers }\n  Message: { _response.json()["message"] }')
                continue
        return _response.status_code, _response.json()

def get_all_repos(query: str) -> dict:
    # as the GitHub search API only returns 1000 results per search, to get all results, we have to slice the search into chunks
    # this method is not perfect and will result in an endless loop if the number of projects with the same star count is larger than 1000
    try:
        status, response = github_rest_call(f'search/repositories?q={ query }stars:>={ arguments.stars }&sort=stars&order=desc&per_page=100')
        print(f'+ Getting { response["total_count"] } repositories')
        if (response["total_count"] == 0):
            return dict()
        repo_list = dict()
        number_of_pages = math.ceil(response["total_count"] / 100)
        chunks_remaining = math.ceil(number_of_pages / 10)
        last_stars = response["items"][0]["stargazers_count"]
    except:
        print(f'- Unexpected error, server sent status {status} and message:\n{response}')
        return dict()
    for n in range(0, chunks_remaining):
        print(f"  Chunk { n + 1 } of { chunks_remaining } (star count: { last_stars })")
        _chunk_last_stars = last_stars
        for p in range(1, 10 + 1):
            if (p + (n * 10) > number_of_pages): break
            print(f"+ Requesting page { p + (n * 10) } of { number_of_pages } (star count: { _chunk_last_stars })")
            #try:
            status, response = github_rest_call(f"search/repositories?q={ query }stars:<={ last_stars }&sort=stars&order=desc&per_page=100&page={ p }")
            for _repo in response["items"]:
                repo_list[_repo["full_name"]] = _repo
                _chunk_last_stars = int(_repo["stargazers_count"])
                _status, _response = github_rest_call(f"repos/{ _repo['full_name'] }/readme")
                if _status == 404:
                    print(f"  Repo { _repo['full_name'] } has no readme!")
                else:
                    with open(_repo['full_name'].replace('/','_') + '.readme', 'w', encoding='utf-8') as _fd:
                        try:
                            _fd.write(str(base64.b64decode(_response['content']).decode()))
                        except:
                            json.dump(_response, _fd)
                            print(f'  Could not parse readme for { _repo["full_name"] }, server sent:\n{ _response }')
                        
            #except:
            #    print(f'- Unexpected error, server sent status {status} and message:\n{response}')
            #    continue
        last_stars = min(_chunk_last_stars, last_stars - 1)
        if (last_stars) <= arguments.stars: break
    return repo_list


print('GitHub Project Search for all repositories ...')
if (arguments.language):
    print(f'  written mainly in the {arguments.language} programing language')
if (arguments.filename):
    print(f'  in file(s) »{ "« or »".join(arguments.filename) }«')
if (arguments.keyword):
    print(f'  with search keyword(s) »{ "« or »".join(arguments.keyword) }«')
if (arguments.language and arguments.input):
    print('Note: Language parameter is being ignored as a pre-existing input file is used')
print('---------------------------------------------------')

repository_list = dict()
repository_list_output = dict()

# if an input file is specified, we use it as the starting point - otherwise we crawl the GitHub API
if (arguments.input):
    with open(arguments.input, 'r', encoding='utf-8') as fd:
        _repository_list = json.load(fd)
    for _reponame in _repository_list:
        if (_repository_list[_reponame]["stargazers_count"] >= arguments.stars):
            repository_list[_reponame] = _repository_list[_reponame]
else:
    repository_list = get_all_repos(f'{ ("language:" + arguments.language + "+") if arguments.language else "" }')

print(f'+ Loaded { len(repository_list) } repositories')

if (arguments.filename or arguments.keyword):
    for _reponame in repository_list:
        _hit = False
        print(f'+ Checking { repository_list[_reponame]["full_name"] } for matches')
        for _keyword in arguments.keyword or ['']:
            # _hit -> definite, confirmed hit, _potential_hit -> hit in the search API, but not in the actual checked file
            _potential_keyword_hit = False
            _file_list = []
            for _file in arguments.filename or ['']:
                if (_hit): break
                print(f'  Querying for { _keyword }{ (" @ " + _file) if _file else "" }')

                # careful: we can't search for *both* keyword and in:path - the API just doesn't give any results, even if the files exist
                # should this behavior change, one could add "__path in:path" to the search string, making the verification of results redundant
                __file, __path = _file.split('/')[-1], '/'.join(_file.split('/')[:-1])

                # if we have no _potential_hit, but already checked the filename, we can skip, as the search API call does not include the path
                if (not _potential_keyword_hit and __file in _file_list): continue
                _file_list.append(__file)

                status, response = github_rest_call(f'search/code?q=repo:{ _reponame }+{ (_keyword + "+") if _keyword else ""  }{ ("filename:" + __file + "+") if __file else "" }{ ("language:" + arguments.language) if arguments.language else "" }')
                if (status != 200 or response['total_count'] == 0): continue
                print(f'  Hit for { _keyword }{ (" @ " + _file) if _file else "" }')
                _potential_keyword_hit = True

                # verify hit by getting the content of the file, as the search ignores some chars (making e.g. "Makefile.am" and "Makefile" the same)
                status, response = github_rest_call(f'repos/{ _reponame }/contents/{ _file }')
                if (status != 200): continue
                content = base64.b64decode(response["content"]).decode('utf-8')
                if (_keyword in content):
                    print(f'  Hit confirmed')
                    _hit = True
        if (_hit):
            repository_list_output[_reponame] = repository_list[_reponame]
            if (arguments.output):
                with open(arguments.output, 'w', encoding='utf-8') as fd:
                    json.dump(repository_list_output, fd)
        time.sleep(2)
else:
    # if no further filtering is required, we can just output the list of repos
    repository_list_output = repository_list

print(f'+ Done! Repositories:')
for _reponame in repository_list_output:
    print(f'  { _reponame }')

print('---------------------------------------------------')
if (arguments.output):
    with open(arguments.output, 'w', encoding='utf-8') as fd:
        json.dump(repository_list_output, fd)
    print(f'+ All repository data written to { arguments.output }')
else:
    print(json.dumps(repository_list_output))
