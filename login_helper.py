import re
import os
import json
import base64
import tempfile
import requests
from bs4 import BeautifulSoup


def get_csrf_token(response_text: str):
    soup = BeautifulSoup(response_text, 'html.parser')
    js_blocks = soup.select('script[language="javascript"]')
    csrf_token = js_blocks[-1]
    matched = re.findall(r'(var csrfToken = \'\w+\')', str(csrf_token))
    if len(matched) != 1:
        raise Exception('Cannot find the CSRF Token!')

    name_matched = re.findall(r'(nti_\w+)', str(csrf_token))
    if len(name_matched) != 1:
        raise Exception('Cannot find the CSRF Token hidden input name!')


    csrf_token = matched[0].replace('var csrfToken = \'', '').replace('\'', '')
    csrf_token_name = name_matched[0] 

    return {
        'name': csrf_token_name,
        'value': csrf_token,
    }

def get_captcha_code(captcha_img_path: str):
    api_key = os.getenv('cloud_vision_api_key', '')
    if api_key == '':
        raise Exception('The Cloud Vision API Key is not found or defined.')

    req_url = f'https://vision.googleapis.com/v1/images:annotate?key={api_key}'

    with open(captcha_img_path, mode='rb') as f:
        encoded_base64_image = base64.b64encode(f.read()).decode()

    headers = {
        'Content-Type': 'application/json',
    }
    request_body_json = {
      'requests': [
            {
                'image': {
                    'content': encoded_base64_image,
                },
                'features': [
                    {
                        'type':'TEXT_DETECTION',
                        'maxResults':10,
                    }
                ]
            }
        ]
    }

    response = requests.post(req_url, data=json.dumps(request_body_json), headers=headers)
    try:
        res_json = response.json()

        return res_json['responses'][0]['fullTextAnnotation']['text']
    except:
        raise Exception('Cloud Vision API error response: ' + response.text)

def login_helper(cell_phone_number: str, password: str, verify_ssl=True):
    req_login_url = 'https://www.rt-mart.com.tw/member/index.php?action=index'
    login_page = 'https://www.rt-mart.com.tw/member/index.php?action=member_login&r_byeurl=member'
    captcha_page = 'https://www.rt-mart.com.tw/member/images/authimg.php'

    req_session = requests.Session()
    response = req_session.get(login_page, verify=verify_ssl)

    captcha_response = req_session.get(captcha_page, verify=verify_ssl)
    captcha_img_path = f'{tempfile.gettempdir()}/authimg.png'
    with open(f'{captcha_img_path}', mode='wb') as f:
        f.write(captcha_response.content)

    captcha_code = get_captcha_code(captcha_img_path)
    csrf_token_info = get_csrf_token(response.text)
    payload = {
        'login_account': cell_phone_number,
        'login_password': password,
        'login_authimg_str': captcha_code,
        'btn_submit': f"{csrf_token_info['name']}={csrf_token_info['value']}",
    }
    headers = {
        'Referer': login_page,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    response = req_session.post(req_login_url, headers=headers, data=payload, verify=verify_ssl)

    return {
        'resp_text': response.text,
        'req_session': req_session,
    }
