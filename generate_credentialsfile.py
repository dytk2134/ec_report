
#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from oauth2client.service_account import ServiceAccountCredentials
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from oauth2client.client import GoogleCredentials

# logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    lh = logging.StreamHandler()
    lh.setFormatter(logging.Formatter('%(levelname)-8s %(message)s'))
    logger.addHandler(lh)

__version__ = 'v1.0.0'

def authorize(input, output):
    gauth = GoogleAuth()
    gauth.DEFAULT_SETTINGS['client_config_file'] = input
    gauth.LoadCredentialsFile(output)
    if gauth.credentials is None:
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        gauth.Refresh()
    else:
        gauth.Authorize()
        gauth.SaveCredentialsFile(output)

def main():
    import argparse
    from textwrap import dedent
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=dedent("""\
    Usage:
    %(prog)s -i client_secrets.json -o mycreds.txt
    """))
    parser.add_argument('-i', '--input', type=str, help='OAuth 2.0 authentication file. Default: client_secrets.json', default='client_secrets.json')
    parser.add_argument('-o', '--output', type=str, help='Specify the output filename of the credentials file. Default: mycreds.txt', default='mycreds.txt')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)

    args = parser.parse_args()
    authorize(args.input, args.output)

if __name__ == '__main__':
    main()


