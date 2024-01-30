import os
import re
import time
from bs4 import BeautifulSoup
from login_helper import login_helper


def get_order_info():
    credential_path = 'credential.txt'
    if os.path.isfile(f'{credential_path}') is False:
        raise Exception(f'Cannot find the {credential_path}')

    with open(credential_path, mode='r', encoding='utf-8') as f:
        credential = f.readlines()

    cell_phone_number = credential[0][0:-1]
    password = credential[1][0:-1]

    login_response = login_helper(cell_phone_number=cell_phone_number, password=password, verify_ssl=False)
    login_response_text = login_response['resp_text']
    req_session = login_response['req_session']
    is_login_keyword = '登出'
    retry_counter = 0


    while is_login_keyword not in login_response_text and retry_counter < 3:
        print(f'Login has been retried. (counter: {retry_counter})')
        retry_counter += 1
        time.sleep(5)
        login_response_text = login_helper(cell_phone_number='0910144906', password='peter82630', verify_ssl=False)


    if is_login_keyword not in login_response_text:
        print(f'The login retry counter is exceed!')
        exit(1)


    orders = []
    orders_append = orders.append
    page = 1
    no_data_keyword = '沒有資料'
    resp_text = ''
    req_url = 'https://www.rt-mart.com.tw/member/index.php?action=order_inquiry&page={}'
    while no_data_keyword not in resp_text:
        response = req_session.get(req_url.format(page))
        resp_text = response.text
        if no_data_keyword in resp_text:
            break

        soup = BeautifulSoup(resp_text, 'html.parser')
        order_table = soup.select('table.chk_order > tbody > tr')
        for order_row in order_table:
            order_info = order_row.select('td')
            orders_append(
                {
                    'date': order_info[0].text,
                    'number': order_info[1].select_one('a').text,
                    'status': re.sub(r'[\n,\t\r]', '', order_info[2].text),
                    'pay_method': order_info[3].text,
                    'total_price': order_info[4].text,
                }
            )

        page += 1

    return orders
