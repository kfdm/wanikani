import argparse
import logging
import os

from wanikani.core import WaniKani, Radical, Kanji, Vocabulary

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
    parser.add_argument('-d', '--debug',
        action='store_const',
        const=logging.DEBUG,
        default=logging.WARNING
    )

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

    def recent_unlocks(client, args):
        p = client.recent_unlocks()
        print p['user_information']['username'], 'level', p['user_information']['level']
        for item in p['items']:
            print item['level'], item['character']
    recent_unlocks.parser = subparsers.add_parser('unlocks')
    recent_unlocks.parser.set_defaults(func=recent_unlocks)

    def upcoming(client, args):
        queue = client.upcoming()

        for ts in sorted(queue):
            if len(queue[ts]):
                radicals, kanji, vocab, total = 0, 0, 0, 0
                for obj in queue[ts]:
                    total += 1
                    if isinstance(obj, Radical):
                        radicals += 1
                    if isinstance(obj, Kanji):
                        kanji += 1
                    if isinstance(obj, Vocabulary):
                        vocab += 1

                # Note the trailing commas,
                # We only want a newline for the last one
                print ts,
                print 'Total:', total,
                print 'Radials:', radicals,
                print 'Kanji:', kanji,
                print 'Vocab:', vocab

    upcoming.parser = subparsers.add_parser('upcoming')
    upcoming.parser.set_defaults(func=upcoming)

    args = parser.parse_args()
    logging.basicConfig(level=args.debug)
    client = WaniKani(args.api_key)
    args.func(client, args)
