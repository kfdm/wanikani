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

    def profile(client, args):
        p = client.profile()
        print 'Username:', p['username']
        print 'Level:', p['level']
    profile.parser = subparsers.add_parser('profile')
    profile.parser.set_defaults(func=profile)

    def level_progress(client, args):
        p = client.level_progress()
        print p['user_information']['username'], 'level', p['user_information']['level']
        print 'Radicals:', p['radicals_total']
        print 'Kanji:', p['kanji_total']
    level_progress.parser = subparsers.add_parser('progress')
    level_progress.parser.set_defaults(func=level_progress)

    args = parser.parse_args()
    client = WaniKani(args.api_key)
    args.func(client, args)
