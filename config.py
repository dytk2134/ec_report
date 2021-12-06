# -*- coding: utf-8 -*-
# Contributed by Li-Mei Chiang <dytk2134 [at] gmail [dot] com> (2021)

# App
DEBUG = True
TESTING = True
SECRET_KEY = 'put your secret key'
HOST = '0.0.0.0'
PORT = 3000

# Authorization
SERVER_ACCOUNT_JSON = 'credentials.json'
OAUTH2_CLIENTID_JSON = 'client_secrets.json'
GDRIVE_CREDENTIALSFILE = 'mycreds.txt'

SHEET_ID = 'SHEET ID'

# Celery
REDIS = 'redis://127.0.0.1:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_RESULT_BACKEND = REDIS
CELERY_BROKER_URL = REDIS

# EC
EC_USERNAME = 'EC username'
EC_PASSWORD = 'EC password'

# crontab
# CRONTAB_MINUTE = '*/5'
# CRONTAB_HOUR = ''
