import argparse, datetime, json, praw, PyRSS2Gen
from jinja2 import Template
from twitchAPI.twitch import Twitch

class DateTimeEncoder(json.JSONEncoder):
  def default(self, datetime_object):
    if isinstance(datetime_object, datetime.datetime):
      return datetime_object.strftime('%Y-%m-%d %H:%M:%S +0000')
    else:
      return super().default(datetime_object)

parser = argparse.ArgumentParser()

parser.add_argument('--appid', required=True)
parser.add_argument('--appsecret', required=True)

parser.add_argument('--html', action='store_true')
parser.add_argument('--api', action='store_true')
parser.add_argument('--feed', action='store_true')
parser.add_argument('--reddit', action='store_true')

args = parser.parse_args()

if args.appid is not None and args.appsecret is not None:
  twitch = Twitch(app_id=args.appid, app_secret=args.appsecret)
  twitch.authenticate_app([])

  streams = twitch.get_streams(game_id='30921')

  reward_streams = []
  reward_streams_count = 0

  for stream in streams['data']:
    if 'c2542d6d-cd10-4532-919b-3d19f30a768b' in stream['tag_ids']:
      user_login = stream['user_login']
      user_name = stream['user_name']
      title = stream['title'].strip()
      thumbnail_url = stream['thumbnail_url'].format(width=1280, height=720)
      started_at = datetime.datetime.strptime(stream['started_at'], '%Y-%m-%dT%H:%M:%SZ')
      id = stream['id']

      reward_stream = {'user_login': user_login, 'user_name': user_name, 'title': title, 'thumbnail_url': thumbnail_url, 'started_at': started_at, 'id': id}

      if reward_streams_count % 4 == 0:
        reward_streams.append([reward_stream])
      else:
        reward_streams[-1].append(reward_stream)

      reward_streams_count += 1

  last_update = datetime.datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %z')

  if args.reddit and reward_streams_count > 0:
    try:
      with open('reddit_stream_ids.json') as json_file:
        reddit_stream_ids = json.load(json_file)['ids']
    except IOError:
      reddit_stream_ids = []

    ids = list(set([reward_stream['id'] for row in reward_streams for reward_stream in row]) - set(reddit_stream_ids))

    if len(ids) > 0:
      with open('reddit.json') as json_file:
        reddit_settings = json.load(json_file)

      reddit = praw.Reddit(
        client_id=reddit_settings['client_id'],
        client_secret=reddit_settings['client_secret'],
        user_agent=reddit_settings['user_agent'],
        username=reddit_settings['username'],
        password=reddit_settings['password']
      )

      title = 'Streams with Rocket League Fan Rewards active are live right now!'
      selftext = 'The following streams with Rocket League Fan Rewards active are live right now:\n\n'

      for reward_stream in [reward_stream for row in reward_streams for reward_stream in row]:
        selftext += '* [{}: {}](https://twitch.tv/{}) (Started at: {})\n\n'.format(reward_stream['user_name'], reward_stream['title'], reward_stream['user_login'], reward_stream['started_at'])

      selftext += 'For more information about Rocket League Fan Rewards, please visit [https://rewards.rocketleague.com/](https://rewards.rocketleague.com/)'

      try:
        submission = reddit.subreddit(reddit_settings['subreddit']).submit(title=title, selftext=selftext)
      except RedditAPIException as exception:
        print(exception)
      else:
        with open('reddit_stream_ids.json', 'w') as json_file:
          reddit_stream_ids.extend(ids)

          json.dump({'ids': reddit_stream_ids}, json_file)

  if args.html:
    with open('index.jinja2') as jinja2_file:
      template = Template(jinja2_file.read())

    with open('index.html', 'w') as html_file:
      html_file.write(template.render(reward_streams=reward_streams, last_update=last_update) + '\n')

  if args.api:
    with open('api.json', 'w') as json_file:
      json.dump({'last_update': last_update, 'streams': [reward_stream for row in reward_streams for reward_stream in row]}, json_file, cls=DateTimeEncoder)

      json_file.write('\n')

  if args.feed:
    feed = PyRSS2Gen.RSS2(title='Rocket League Fan Rewards',
      link='https://haltepunkt.github.io/RocketLeagueFanRewards/feed.xml',
      description='Streams with Rocket League Fan Rewards active',
      docs=None, generator=None)

    for reward_stream in [reward_stream for row in reward_streams for reward_stream in row]:
      item = PyRSS2Gen.RSSItem(title=reward_stream['title'],
        description=reward_stream['user_name'],
        link='https://www.twitch.tv/' + reward_stream['user_login'],
        pubDate=reward_stream['started_at'],
        guid=PyRSS2Gen.Guid('https://www.twitch.tv/{}#{}'.format(reward_stream['user_login'], reward_stream['started_at'].strftime('%Y-%m-%dT%H:%M:%SZ'))))

      feed.items.append(item)

    with open('feed.xml', 'w') as feed_file:
      feed.write_xml(feed_file)

      feed_file.write('\n')
