import argparse
import logging
import os

# If the tzlocal package is installed, then we will help the user out
# and print things out in the local timezone
LOCAL_TIMEZONE = None
try:
    import tzlocal
    LOCAL_TIMEZONE = tzlocal.get_localzone()
except ImportError:
    pass

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
    profile.parser = subparsers.add_parser(
        'profile', help="Show basic profile information")
    profile.parser.set_defaults(func=profile)

    def level_progress(client, args):
        p = client.level_progress()
        print p['user_information']['username'], 'level', p['user_information']['level']
        print 'Radicals:', p['radicals_total']
        print 'Kanji:', p['kanji_total']
    level_progress.parser = subparsers.add_parser(
        'progress', help="Show level progress")
    level_progress.parser.set_defaults(func=level_progress)

    def recent_unlocks(client, args):
        p = client.recent_unlocks()
        print p['user_information']['username'], 'level', p['user_information']['level']
        for item in p['items']:
            print item['level'], item['character']
    recent_unlocks.parser = subparsers.add_parser(
        'unlocks', help="Show recent unlocks")
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

                if LOCAL_TIMEZONE:
                    ts.replace(tzinfo=LOCAL_TIMEZONE)
                # Note the trailing commas,
                # We only want a newline for the last one
                print ts,
                print 'Total:', total,
                print 'Radials:', radicals,
                print 'Kanji:', kanji,
                print 'Vocab:', vocab

    upcoming.parser = subparsers.add_parser(
        'upcoming', help="Show report of upcoming reviews")
    upcoming.parser.set_defaults(func=upcoming)

    def set_key(client, args):
        with open(CONFIG_PATH, 'w') as f:
            f.write(args.api_key)
        print 'Wrote {0} to {1}'.format(args.api_key, CONFIG_PATH)
    set_key.parser = subparsers.add_parser(
        'set_key', help="Set API Key")
    set_key.parser.set_defaults(func=set_key)
    set_key.parser.add_argument('api_key', help="New API Key")

    args = parser.parse_args()
    logging.basicConfig(level=args.debug)
    client = WaniKani(args.api_key)
    args.func(client, args)
