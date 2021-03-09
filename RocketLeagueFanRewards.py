import argparse, datetime, json, PyRSS2Gen
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

      reward_stream = {'user_login': user_login, 'user_name': user_name, 'title': title, 'thumbnail_url': thumbnail_url, 'started_at': started_at}

      if reward_streams_count % 4 == 0:
        reward_streams.append([reward_stream])
      else:
        reward_streams[-1].append(reward_stream)

      reward_streams_count += 1

  last_update = datetime.datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %z')

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
