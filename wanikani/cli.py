import argparse
import os
import logging

from wanikani.core import WaniKani

CONFIG_PATH = os.path.join(os.path.expanduser('~'), '.wanikani')

logger = logging.getLogger(__name__)

def config():
    if os.path.exists(CONFIG_PATH):
        logger.debug('Loading config from %s', CONFIG_PATH)
        with open(CONFIG_PATH) as f:
            return f.read().strip()
    return ''


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    # Global Options
    parser.add_argument('-a', '--api-key', default=config())

    profile_parser = subparsers.add_parser('profile')
    def profile(client, args):
        p = client.profile()
        print 'Username:', p['username']
        print 'Level:', p['level']
    profile_parser.set_defaults(func=profile)


    args = parser.parse_args()
    client = WaniKani(args.api_key)
    args.func(client, args)
