import json
import os
import traceback

import telebot
import requests
from telebot import types

TOKEN = 'telegram_bot_tokem'
URL = 'https://api.telegram.org/bot'
ADMIN_CHAT_ID = 0  # get your chat id here: @chat_id_echo_bot
MY_NODE_ADDRESS = 'http://localhost:6870'
WAVES_NODE_ADDRESS = 'https://nodes.wavesnodes.com'
NODE_CONFIG_DIRECTORY = '/usr/share/waves/conf'
beneficiaryAddress = ''  # your beneficiaryAddress

bot = telebot.TeleBot(TOKEN, parse_mode=None)


def start(message):
    markup = types.ReplyKeyboardMarkup(row_width=2)
    btn_1 = types.KeyboardButton('check node height')
    btn_2 = types.KeyboardButton('check node version')
    btn_3 = types.KeyboardButton('check node features')
    btn_4 = types.KeyboardButton('restart node')
    btn_5 = types.KeyboardButton('update node')
    btn_6 = types.KeyboardButton('enable next feature')
    btn_7 = types.KeyboardButton('check beneficiary address balance')
    markup.add(btn_1, btn_2, btn_3, btn_4, btn_5, btn_6, btn_7)

    bot.send_message(message.from_user.id, 'Hi!', reply_markup=markup)


def check_node_height():
    waves_node_result = requests.get(f'{WAVES_NODE_ADDRESS}/blocks/height').json()['height']
    my_node_result = requests.get(f"{MY_NODE_ADDRESS}/blocks/height").json()['height']
    return f"Waves node height: {waves_node_result}\nMy node height: {my_node_result}"


def check_node_version():
    return requests.get(f'{MY_NODE_ADDRESS}/node/version').json()['version']


def check_node_features():
    features = requests.get(f'{MY_NODE_ADDRESS}/activation/status').json()['features']
    return json.dumps(features, indent=2)


def check_ben_balance():
    balance = requests.get(f'{MY_NODE_ADDRESS}/addresses/balance/{beneficiaryAddress}').json()['balance'] / 100000000
    return f'Beneficiary address balance: {balance} waves'


def enable_next_feature(message):
    node_features = json.loads(check_node_features())

    if node_features[-1]['nodeStatus'] == 'VOTED':
        bot.send_message(message.from_user.id, 'Already enabled')
    else:
        with open(f'{NODE_CONFIG_DIRECTORY}/waves.conf') as file:
            file_str = file.read()
            feature_id = node_features[-1]['id']
            file_str = file_str.replace('supported = [', f'supported = [{feature_id},')

            with open(f'{NODE_CONFIG_DIRECTORY}/waves.conf', 'w') as outfile:
                outfile.write(file_str)

            bot.send_message(message.from_user.id, f'Feature {feature_id} successfully enabled')

            restart_node(message)


def restart_node(message):
    os.system('systemctl restart waves.service')
    bot.send_message(message.from_user.id, 'node restarted')


@bot.message_handler(content_types=['text'], chat_types=['private'])
def get_text_messages(message):
    if message.from_user.id != ADMIN_CHAT_ID:
        return

    try:
        if message.text == '/start':
            start(message)

        elif message.text == 'check node height':
            bot.send_message(message.from_user.id, check_node_height())

        elif message.text == 'check node version':
            bot.send_message(message.from_user.id, check_node_version())

        elif message.text == 'check node features':
            bot.send_message(message.from_user.id, check_node_features())

        elif message.text == 'check beneficiary address balance':
            bot.send_message(message.from_user.id, check_ben_balance())

        elif message.text == 'restart node':
            restart_node(message)

        elif message.text == 'enable next feature':
            enable_next_feature(message)

        elif message.text == 'update node':
            bot.send_message(message.from_user.id,
                             'please use command "/updatenode github_link_to_deb_package"\n\nexample: \n/updatenode '
                             'https://github.com/wavesplatform/Waves/releases/download/v1.4.6/waves_1.4.6_all.deb')

        elif '/updatenode https://github.com/wavesplatform/Waves/' in message.text:
            url = message.text.split(' ')[1]
            version = url.split('/')[-1]
            os.system(
                f'wget {url} && systemctl stop waves && dpkg -i {version} && systemctl start waves && rm {version}')
            bot.send_message(message.from_user.id, 'node updated')
    except:
        ex = traceback.format_exc()

        try:
            bot.send_message(message.from_user.id, ex)
        except:
            # todo: file logging
            print(ex)


def run():
    bot.infinity_polling()


if __name__ == '__main__':
    run()
