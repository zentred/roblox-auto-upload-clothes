import requests, json, os, time, ctypes

with open('config.json') as config:
    config = json.load(config)

log = {
    'unableToUpload': [],
    'unableToConfigure': []
}

class Bot:

    def __init__(self):
        self.uploadedShirts = self.uploadedPants = 0
        self.session = None
        self.update_session()
        self.check()

    def update_session(self):
        session = requests.Session()
        session.cookies['.ROBLOSECURITY'] = config['cookie']
        session.headers['X-CSRF-TOKEN'] = session.post(
            'https://auth.roblox.com/v2/login'
        ).headers['X-CSRF-TOKEN']
        self.session = session

    def upload(self, filename, asset_type):
        item_config = {
            "name": "untitled",
            "description": config['assetTags'],
            "creatorTargetId": str(config['groupId']),
            "creatorType": "Group"
        }
        if config['tryToUseFileNameAsAssetName']:
            filtered = filename.replace('-', ' ').replace('_', ' ').replace('.png', '').replace('.jpg', '').replace('.jpeg', '')
            if filtered.replace(' ', '').isalpha(): # checks if name is fully english
                item_config['name'] = " ".join(filtered.split())
        if asset_type == '11': item_config['name'] = 'Shirt'
        elif asset_type == '12': item_config['name'] = 'Pants'

        while True:
            resp = self.session.post(
                f'https://itemconfiguration.roblox.com/v1/avatar-assets/{asset_type}/upload',
                files = {
                    'media': open(f'clothes/shirts/{filename}', 'rb'),
                    'config': json.dumps(item_config, indent=2).encode('utf-8')
                }
            )
            if resp.status_code == 200:
                assetId = resp.json()['assetId']
                print(f'{filename} was uploaded, assetId: {assetId}, assetName: {item_config["name"]}')
                self.configure(assetId)
                break
            else:
                error = resp.json()['errors'][0]['message']
                if error == 'TooManyRequests':
                    print(f'{filename} was unable to be uploaded -> reason: TooManyRequests -> retrying in 60 seconds')
                    time.sleep(60)
                else:
                    print(f'{filename} was unable to be uploaded -> reason: {error}')
                    log['unableToUpload'].append(filename)
                    break

    def configure(self, assetId):
        while True:
            resp = self.session.post(
                f'https://itemconfiguration.roblox.com/v1/assets/{assetId}/release',
                json = {
                    "price": config['price'],
                    "priceConfiguration": {
                        "priceInRobux": config['price']
                    },
                    "saleStatus": "OnSale"
                }
            )
            if resp.status_code == 200:
                print(f'{assetId} was put on sale and updated to {config["price"]} robux sale price\n')
                break
            else:
                error = resp.json()['errors'][0]['message']
                if error == 'TooManyRequests':
                    print(f'{assetId} was unable to be configured -> reason: TooManyRequests -> retrying in 60 seconds')
                    time.sleep(60)
                else:
                    print(f'{assetId} was unable to be configured -> reason: {error}\n')
                    log['unableToConfigure'].append(assetId)
                    break

    def check(self):
        totalShirts = len(os.listdir('clothes/shirts'))
        totalPants = len(os.listdir('clothes/pants'))
        ctypes.windll.kernel32.SetConsoleTitleW(f'Total Shirts: {totalShirts} / Total Pants: {totalPants}')

        for a, b, c in os.walk('clothes/shirts'):
            for file in c:
                self.upload(file, '11')
        for a, b, c in os.walk('clothes/pants'):
            for file in c:
                self.upload(file, '12')
Bot()
with open('log.json', 'w') as m:
    json.dump(log, m, indent=4)
print(f'Saved log to log.json, this will tell you which assets were not uploaded / configured')
