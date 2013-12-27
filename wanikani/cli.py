import argparse
import datetime
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


class Subcommand(object):
    def __init__(self, subparser):
        self.parser = subparser.add_parser(self.name, help=self.help)
        self.parser.set_defaults(func=self.execute)
        self.add_parsers()

    def add_parsers(self):
        pass

    def execute(self, client, args):
        raise NotImplementedError


class Profile(Subcommand):
    name = 'profile'
    help = 'Show simple profile information'

    def execute(self, client, args):
        p = client.profile()
        print 'Username:', p['username']
        print 'Level:', p['level']


class LevelProgress(Subcommand):
    name = 'progress'
    help = 'Show level progress'

    def execute(self, client, args):
        p = client.level_progress()
        print p['user_information']['username'], 'level', p['user_information']['level']
        print 'Radicals: {0}/{1}'.format(p['radicals_progress'], p['radicals_total'])
        print 'Kanji: {0}/{1}'.format(p['kanji_progress'], p['kanji_total'])


class RecentUnlocks(Subcommand):
    name = 'unlocks'
    help = 'Show recently unlocked items'

    def execute(self, client, args):
        p = client.recent_unlocks()
        print p['user_information']['username'], 'level', p['user_information']['level']
        for item in p['items']:
            print item['level'], item['character']


class Upcoming(Subcommand):
    name = 'upcoming'
    help = 'Show report of upcoming reviews'

    def add_parsers(self):
        self.parser.add_argument('-r', '--rollup', action='store_true')

    def execute(self, client, args):
        queue = client.upcoming()

        if args.rollup:
            now = datetime.datetime.now().replace(microsecond=0)
            # now += datetime.timedelta(hours=5) #  Future date for testing
            rollup = []
            for ts in queue.keys():
                if ts < now:
                    rollup += queue.pop(ts)
            if rollup:
                queue[now] = rollup
                print 'Rolled up reviews'

        for ts in sorted(queue)[:10]:
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
                print '{0} Total: {1:>3}     Radicals: {2:>3} Kanji: {3:>3} Vocab: {4:>3}'.format(
                    ts,
                    total,
                    radicals,
                    kanji,
                    vocab
                    )


class SetAPIKey(Subcommand):
    name = 'set_key'
    help = 'Set API Key'

    def add_parsers(self):
        self.parser.add_argument('api_key', help="New API Key")

    def execute(self, client, args):
        with open(CONFIG_PATH, 'w') as f:
            f.write(args.api_key)
        print 'Wrote {0} to {1}'.format(args.api_key, CONFIG_PATH)


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    # Global Options
    parser.add_argument('-a', '--api-key', default=config())
    parser.add_argument(
        '-d', '--debug',
        action='store_const',
        const=logging.DEBUG,
        default=logging.WARNING
    )

    # Add our sub commands
    Profile(subparsers)
    LevelProgress(subparsers)
    RecentUnlocks(subparsers)
    Upcoming(subparsers)
    SetAPIKey(subparsers)

    args = parser.parse_args()
    logging.basicConfig(level=args.debug)
    client = WaniKani(args.api_key)
    args.func(client, args)
