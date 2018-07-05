#!/usr/bin/env python3
import requests
import re
import json
from config import ACCT, PASS
"""
need following from config:
    ACCT - account for autodesk360
    PASS - password for autodesk360
"""


SIGNON_URL = 'https://accounts.autodesk.com/Authentication/LogOn'

# root download dir
# the program will request download link for every model file under
# this folder recursively
# this can be found in the url
PROJ_DATA = input('Enter data field for the directory to download\n'
                  'NOTE: This can be found in the url after .../data/\n'
                  'when you log in your myhub and select a project or\n'
                  'a directory within the project\n'
                  'This should be a long sequece of both lower case '
                  'and upper case letters\n'
                  'and digits\n')

# {}: csrf token
ROOT_DIR_URL = 'https://myhub.autodesk360.com/ue2b6623b/data/api/folders/' +\
        PROJ_DATA +\
        '/nodes?csrf-token={}&count=100&orderBy=name&sortOrder=asc&start=0'

HUB_URL = 'https://myhub.autodesk360.com'

# csrf token with POST payload
EXPORT_URL_TEMPLATE = \
    'https://myhub.autodesk360.com/ue2b6623b/data/api/export?csrf-token={}'

VERIFY_TOKEN_RE = \
    r'<input.*name=\"__RequestVerificationToken\".*value=\"(.*)\".*\/>'

count = 0


def model_filter(node):
    return node['directory'] == 'false' and \
            node['application'] == 'DATA'


def folder_filter(node):
    return node['directory'] == 'true'


def retrive_model_files(node_url, csrf_token, model_list):
    """
    recursively request for download link for all model files under
    the dir in node_url
    """
    global count
    res = s.get(node_url)
    res_json = json.loads(res.text)

    if 'objects' not in res_json['success']['body']:
        print('Empty folder')
        return
    nodes = res_json['success']['body']['objects']
    models = list(filter(model_filter, nodes))
    for model in models:
        print('[{}] - Found model file {}'.format(count, model['name']))
        # node['properties'] => obj with name being 'tipVersion' => 'value'
        urn = [_property['value']
               for _property in model['properties']
               if _property['name'] == 'tipVersion'][0]
        export_model_file(urn, csrf_token)
        count += 1

    model_list.extend(models)
    for node in [node for node in nodes if folder_filter(node)]:
        print('===== Processing folder: {} ====='.format(node['name']))
        url = node['links']['link'][1]['href'] + \
            '?csrf-token={}&count=100&orderBy=name&sortOrder=asc&start=0' \
            .format(csrf_token)
        retrive_model_files(url, csrf_token, model_list)


# send export link email
def export_model_file(urn, csrf_token):
    data = {
        'format': 'stp',
        'sendEmail': 'true',
        'type': 'download',
        'urn': urn
    }

    headers = {'content-type': 'application/json'}
    res = s.post(EXPORT_URL_TEMPLATE.format(csrf_token),
                 data=json.dumps(data), headers=headers)
    res_json = json.loads(res.text)
    if(not (res.status_code == 200 and 'success' in res_json)):
        raise Exception("Error on sending export request:\n{}"
                        .format(res_json))


print('Logging on...')

s = requests.session()

res = s.get(SIGNON_URL)
if res.status_code != 200:
    raise Exception("Error on requesting log on page")

# retrive verification token
verify_token = re.findall(VERIFY_TOKEN_RE, res.text)[0]

# logon POST payload
data = {
    '__RequestVerificationToken': verify_token,
    'UserName': ACCT,
    'Password': PASS,
    'RememberMe': 'false'
}
# simualate logon
res = s.post(SIGNON_URL, data=data)
if res.status_code != 200:
    raise Exception("Error when sending log on request")
res = s.get(HUB_URL)
csrf_token = s.cookies.get('a360_csrf_cookie')

# model nodes buffer
model_list = []
print('retriving all model files')
print('===== Processing given root dir =====')
retrive_model_files(ROOT_DIR_URL.format(csrf_token),
                    csrf_token,
                    model_list)
