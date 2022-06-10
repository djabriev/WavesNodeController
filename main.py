# made by @entrypoint
# works on waves service (docker not supported), tested on ubuntu only
# node update through deb package
# your node .conf file should contain features settings (waves.features)
#   waves {
#       ...
#       features {
#           supported = [17]
#       }
#       ...
#   }
# script looks for string 'supported = [' then replaces it with 'supported = [id,' // hardcoded like this to avoid
#                                                                                     external package imports

import json
import os
import threading

import requests
import time

TOKEN = 'telegram_bot_tokem'
URL = 'https://api.telegram.org/bot'
ADMIN_CHAT_ID = 0  # get your chat id here: @chat_id_echo_bot
MY_NODE_ADDRESS = 'http://localhost:6870'
WAVES_NODE_ADDRESS = 'https://nodes.wavesnodes.com'
DISTRIBUTE_REWARDS = False  # Distribute rewards functionality
DISTRIBUTE_REWARDS_AUTO = False  # Distributing rewards automatically in n seconds
DISTRIBUTE_REWARDS_SCRIPT = '/home/distribute.py'  # path to your distribute rewards python script
DISTRIBUTE_REWARDS_INTERVAL = 21600  # auto rewards distribution interval (seconds), only if DISTRIBUTE_REWARDS_AUTO = True
NODE_CONFIG_DIRECTORY = '/usr/share/waves/conf'


def get_updates(offset=0):
    result = requests.get(f'{URL}{TOKEN}/getUpdates?offset={offset}').json()
    return result['result']


def send_text(bot_message):
    url = f'{URL}{TOKEN}/sendMessage?chat_id={ADMIN_CHAT_ID}&text={bot_message}'
    requests.get(url)


def start():
    kb = json.dumps(
        {"keyboard":
            [
                [
                    {"text": "check node height"},
                    {"text": "check node version"},
                ],
                [
                    {"text": "check node features"},
                    {"text": "check node balance"},
                ],
                [
                    {"text": "restart node"},
                    {"text": "distribute rewards"},
                ],
                [
                    {"text": "update node"},
                    {"text": "enable next feature"},
                ]
            ]
        }
    )

    # Create data dict
    data = {
        'text': (None, 'Hi!'),
        'chat_id': (None, ADMIN_CHAT_ID),
        'reply_markup': (None, kb)
    }

    requests.post(url=f'{URL}{TOKEN}/sendMessage', headers={}, files=data)


def check_node_height():
    waves_node_result = requests.get(f'{WAVES_NODE_ADDRESS}/blocks/height').json()['height']
    my_node_result = requests.get(f"{MY_NODE_ADDRESS}/blocks/height").json()['height']
    return f"Waves node height: {waves_node_result}\nMy node height: {my_node_result}"


def check_node_version():
    return requests.get(f'{MY_NODE_ADDRESS}/node/version').json()['version']


def check_node_features():
    features = requests.get(f'{MY_NODE_ADDRESS}/activation/status').json()['features']
    return json.dumps(features, indent=2)


def check_node_balance():
    main_address = requests.get(f'{MY_NODE_ADDRESS}/addresses').json()[0]
    balance = requests.get(f'{MY_NODE_ADDRESS}/addresses/balance/{main_address}').json()['balance'] / 100000000
    return f'Node balance: {balance} waves'


def distribute_rewards():
    if DISTRIBUTE_REWARDS:
        exec(open(DISTRIBUTE_REWARDS_SCRIPT).read())
        send_text('rewards distributed')
    else:
        send_text('functionality disabled')


def restart_node():
    os.system('systemctl restart waves.service')
    send_text('node restarted')


def enable_next_feature():
    node_features = json.loads(check_node_features())

    if node_features[-1]['nodeStatus'] == 'VOTED':
        send_text('Already enabled')
    else:
        with open(f'{NODE_CONFIG_DIRECTORY}/waves.conf') as file:
            file_str = file.read()
            feature_id = node_features[-1]['id']
            file_str = file_str.replace('supported = [', f'supported = [{feature_id},')

            with open(f'{NODE_CONFIG_DIRECTORY}/waves.conf', 'w') as outfile:
                outfile.write(file_str)

            send_text(f'Feature {feature_id} successfully enabled')

            restart_node()


def run_telegram_bot():
    update_id = get_updates()[-1]['update_id']
    while True:
        time.sleep(3)

        try:
            messages = get_updates(update_id)
            for message in messages:
                if update_id < message['update_id']:
                    update_id = message['update_id']
                    message_chat_id = message['message']['chat']['id']
                    message = message['message']['text']

                    if ADMIN_CHAT_ID == message_chat_id:
                        if message == '/start':
                            start()

                        elif message == 'check node height':
                            send_text(check_node_height())

                        elif message == 'check node version':
                            send_text(check_node_version())

                        elif message == 'check node features':
                            send_text(check_node_features())

                        elif message == 'check node balance':
                            send_text(check_node_balance())

                        elif message == 'restart node':
                            restart_node()

                        elif message == 'distribute rewards':
                            if DISTRIBUTE_REWARDS:
                                distribute_rewards()
                            else:
                                send_text('DISTRIBUTE_REWARDS disabled')

                        elif message == 'enable next feature':
                            enable_next_feature()

                        elif message == 'update node':
                            send_text('please use command "/updatenode github_link_to_deb_package"\n\nexample: \n'
                                      '/updatenode '
                                      'https://github.com/wavesplatform/Waves/releases/download/v1.4.6/waves_1.4'
                                      '.6_all.deb')

                        elif '/updatenode https://github.com/wavesplatform/Waves/' in message:
                            url = message.split(' ')[1]
                            version = url.split('/')[-1]
                            os.system(
                                f'wget {url} && systemctl stop waves && dpkg -i {version} && systemctl start waves && rm {version}')
                            send_text('node updated')

        except requests.exceptions.ConnectionError:
            print("Connection refused to telegram endpoint")


def run_distribute_rewards():
    while True:
        distribute_rewards()
        time.sleep(DISTRIBUTE_REWARDS_INTERVAL)


def run():
    tg_bot_thread = threading.Thread(target=run_telegram_bot)
    tg_bot_thread.start()

    dist_rewards_thread = threading.Thread(target=run_distribute_rewards)
    if DISTRIBUTE_REWARDS_AUTO and DISTRIBUTE_REWARDS:
        dist_rewards_thread.start()


if __name__ == '__main__':
    run()
