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
    formatter = '{0:<10} {1:<5} {2}'

    def execute(self, client, args):
        print self.formatter.format('type', 'level', 'character')
        for item in client.recent_unlocks():
            print self.formatter.format(item['type'], item['level'], item)


class Upcoming(Subcommand):
    name = 'upcoming'
    help = 'Show report of upcoming reviews'
    formatter = '{0:<20} {1:>10} {2:>10} {3:>10} {4:>10}'

    def add_parsers(self):
        self.parser.add_argument('-r', '--rollup', action='store_true')
        self.parser.add_argument('-c', '--current', action='store_true')
        self.parser.add_argument('-s', '--show', action='store_true')
        self.parser.add_argument('-l', '--limit', type=int)
        self.parser.add_argument('-b', '--blocker', action='store_true')

    def execute(self, client, args):
        level = None
        if args.current or args.blocker:
            level = client.profile()['level']

        queue = client.upcoming(level)

        if args.current or args.blocker:
            print 'Showing upcoming items for level', level
            logger.info('Filtering out items that are not level %s', level)
            for ts in queue.keys():
                keep = []
                for item in queue[ts]:
                    if args.blocker and isinstance(item, Vocabulary):
                        logger.debug('Filtered out %s (Vocabulary)', item)
                        continue

                    if args.blocker and item.srs != u'apprentice':
                        logger.debug('Filtered out %s (srs %s)', str(item), str(item.srs))
                        continue

                    if item['level'] != level:
                        logger.debug('Filtered out %s (level %d)', item, item['level'])
                        continue

                    keep.append(item)

                queue[ts] = keep

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

        counter = 0
        print self.formatter.format('Timestamp', 'Radicals', 'Kanji', 'Vocab', 'Total')
        totals = {
            Radical: 0,
            Kanji: 0,
            Vocabulary: 0,
            'total': 0,
        }
        for ts in sorted(queue):
            if args.limit and counter == args.limit:
                break
            if len(queue[ts]):
                counter += 1
                counts = {
                    Radical: 0,
                    Kanji: 0,
                    Vocabulary: 0,
                }

                for obj in queue[ts]:
                    totals['total'] += 1
                    if isinstance(obj, Radical):
                        counts[Radical] += 1
                        totals[Radical] += 1
                    if isinstance(obj, Kanji):
                        counts[Kanji] += 1
                        totals[Kanji] += 1
                    if isinstance(obj, Vocabulary):
                        counts[Vocabulary] += 1
                        totals[Vocabulary] += 1

                if LOCAL_TIMEZONE:
                    ts.replace(tzinfo=LOCAL_TIMEZONE)
                # Note the trailing commas,
                # We only want a newline for the last one
                print self.formatter.format(
                    str(ts),
                    counts[Radical],
                    counts[Kanji],
                    counts[Vocabulary],
                    len(queue[ts]),
                )

                if args.show:
                    print '\t',
                    print ', '.join([str(x) for x in queue[ts]])
        print self.formatter.format(
            'Totals',
            totals[Radical],
            totals[Kanji],
            totals[Vocabulary],
            totals['total']
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
