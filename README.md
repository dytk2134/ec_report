# ec_report

每日凌晨0:00爬取EC訂單資料至Google Sheet

## Set up a Environment
Create the virtual environment
```
$ virtualenv -p python3.6 env
```

To activate it:
```
$ source env/bin/activate
```

## Install Dependencies

```
$ pip install -r requirements.txt

# install google-chrome (若已安裝，請跳過以下步驟)
$ wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
$ sudo apt install -y -f ./google-chrome-stable_current_amd64.deb
$ rm ./google-chrome-stable_current_amd64.deb
```

## Authorization
1. 去[Google API](https://console.developers.google.com/apis)建立專案並啟用`Google Sheets API`
2. 在建立憑證點服務帳戶，新增一個服務帳戶，下載密鑰json檔並提供檔案路徑至`config.py`
3. 新增OAuth 2.0用戶端ID，類型選電腦版應用程式，下載密鑰json檔並命名為`client_secrets.json`
4. 執行`generate_credentialsfile.py`完成授權，並把結果路徑提供給`config.py`
5. 建立Google Sheet(有格式限定!可參考[此表格](https://docs.google.com/spreadsheets/d/12dPMU59tUZhVz9RjsxnoEwT3HuelrXLLOr89hUj3Dj4/edit?usp=sharing))並與剛剛建立的服務帳戶共用表單，並取得檔案ID給config.py
6. 在Google Drive建立存放報告與備份報告的資料夾將兩個資料夾ID給`config.py`

## Getting Start

```
$ python app.py & celery -A task worker --concurrency=1 -B
```

## Google Sheet格式

| 訂單編號 | 會員名稱 | 連絡電話 | 商品名稱 | 商品型號 | 數量 | 發票號碼 | 折扣碼 | 折扣金額 | 銷貨金額 | 訂單狀態 | 最後修改日 |
| ------ | ------ | ------ | ------ | ------ | ------ | ------ | ------ | ------ | ------ | ------ | ------ |
| 20201211266 | 範例 | 0912345678 | 特安康滴雞精 | 1 | 14010011 | UY12343901 | 15120 | 300 | 3200 | 已出貨 | 2020-12-15 |
| 20201211275 | 例範 | 0912345677 | 枕頭 | 1 | 140100 | UY12343801 | 15120 | 500 | 4200 | 已出貨 | 2020-12-15 |

