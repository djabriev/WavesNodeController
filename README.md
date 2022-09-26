```pip install -r requirements.txt```

Control panel for waves node (ubuntu only i guess), implemented through telegram bot api (bot will react only to your chat_id, so no one besides you can interact with bot)

Yeah shitcode, but i'm trying be helpful xD

## Functionality
![alt text](https://i.ibb.co/C1BwMbJ/image.png)

## How it works

- Works on waves service (docker not supported), tested on ubuntu only
- Uses telegram get_updates method, to avoid dances with ssl certificate to use webhooks
- Node update through deb package
- Node height/version/features through local rest api
- Restart/update through ```os.system```
- Enable next feature - script open waves.conf file and looks for string ```supported = [``` then replaces it with ```supported = [id,``` (hardcoded like this to avoid external package imports)
- [Can be turned off by ```DISTRIBUTE_REWARDS = False```] Distribute rewards just runs external script that you should provide (example: https://github.com/waves-exchange/neutrino-utilities/blob/main/neutrino_nodes/payment.py)

## Requirements
- ``pip install -r requirements.txt``
- Correctly installed node (https://docs.waves.tech/en/waves-node/how-to-install-a-node/on-ubuntu)
- Ubuntu
- Python 3
- Your node .conf file should contain features settings (waves.features)
```
waves {
       ...
       features {
           supported = [17]
       }
       ...
} 
```
- Telegram bot (bot token and your user_id, user_id can be found using @chat_id_echo_bot)
- Fill variable values at the top of file, required to change: ```TOKEN```, ```ADMIN_CHAT_ID```, the rest of the constants as you wish

## Tips
I'm using this script as service to keep it alive and run automatically after restart of server

Steps to reproduce:
- Create file /lib/systemd/system/test-py.service
- Check your python executable path to be correct ExecStart=/usr/bin/python3.10
- Right after the executable path change path to this script, by default it's: /home/main.py
```
[Unit]
Description=Test Service
Requires=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3.10 /home/main.py
Restart=always
RestartSec=60
User=root
PermissionsStartOnly=true
TimeoutStopSec=90

[Install]
WantedBy=multi-user.target
```
- ```sudo systemctl daemon-reload```
- ```sudo systemctl enable test-py.service``` (or how you called it while creating service file)
- ```sudo systemctl start test-py.service```