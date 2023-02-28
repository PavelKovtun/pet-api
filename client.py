import json
import sys
import requests
import os
from dotenv import load_dotenv
from pathlib import Path
import argparse


def main():
    parser = create_parser()
    namespace = parser.parse_args()

    dotenv_path = Path('.env')
    load_dotenv(dotenv_path=dotenv_path)

    url = os.getenv('SERVER_ADDRESS') + '/pets'
    api_key_header = os.getenv('API_KEY_HEADER')
    api_key = os.getenv('API_KEY')
    try:
        params = {'has_photos': namespace.has_photos} if namespace.has_photos is not None else {}
        params.update({'limit': sys.maxsize})
        resp = requests.get(url, headers={api_key_header: api_key}, params=params)
        if resp.status_code == 401:
            print('API KEY is not valid', file=sys.stderr)
            sys.exit(1)
        elif resp.status_code == 200:
            json_data = resp.json()
            pets = json_data['data']
            for pet in pets:
                pet['photos'] = [x['image'] for x in pet['photos']]
            new_data = {'pets': pets}
            print(json.dumps(new_data, indent=4))
    except requests.exceptions.RequestException:
        print('ERROR: Server is not available', file=sys.stderr)


def create_parser():
    parser = argparse.ArgumentParser(
        description='''The program-client to get pets from the command line to stdout in json format.'''
    )
    parser.add_argument('has_photos', nargs='?', type=str_to_bool, default=None,
                        help='Boolean value to filter pets with/without photos.')
    return parser


def str_to_bool(arg):
    if arg.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif arg.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


if __name__ == '__main__':
    main()
