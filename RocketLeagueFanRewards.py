import argparse, datetime
from jinja2 import Template
from twitchAPI.twitch import Twitch

template = '''<!doctype html>
<html class="h-100" lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootswatch/4.5.2/darkly/bootstrap.min.css" integrity="sha384-nNK9n28pDUDDgIiIqZ/MiyO3F4/9vsMtReZK39klb/MtkZI3/LtjSjlmyVPS3KdN" crossorigin="anonymous">
    <title>Rocket League Fan Rewards</title>
  </head>
  <body class="h-100">
    <nav class="navbar navbar-dark bg-dark">
      <a class="navbar-brand" href="#"><img src="https://i.imgur.com/IoNjWYZ.png" width="36" height="36" class="" alt=""> Rocket League Fan Rewards</a>
    </nav>
    {%- if reward_streams|length > 0 %}
      <div class="cards container-fluid pt-3">
      {%- for row in reward_streams %}
        <div class="row pt-1">
        {%- for reward_stream in row %}
          <div class="col-sm d-flex align-items-stretch">
            <div class="card mb-2 border-secondary shadow-sm">
              <a href="https://www.twitch.tv/{{ reward_stream.user_login }}"><img src="{{ reward_stream.thumbnail_url }}" class="card-img-top"></a>
              <div class="card-body">
                <a href="https://www.twitch.tv/{{ reward_stream.user_login }}" class="text-reset"><h5 class="card-title">{{ reward_stream.title }}</h5></a>
                <a href="https://www.twitch.tv/{{ reward_stream.user_login }}" class="text-muted"><p class="card-text">{{ reward_stream.user_name }}</p></a>
              </div>
            </div>
          </div>
        {%- endfor %}
        </div>
      {%- endfor %}
      </div>
    {%- else %}
    <div class="container-fluid d-flex justify-content-center align-items-center" style="height: calc(100% - 80px);">
      <div class="row">
        <div class="col text-center">
          <p>No live streams with Rocket League Fan Rewards are active right now.</p>
          <p class="text-muted">Last update: {{ last_update }}</p>
        </div>
      </div>
    </div>
    {%- endif %}
  </body>
</html>'''

parser = argparse.ArgumentParser()
parser.add_argument('--appid', required=True)
parser.add_argument('--appsecret', required=True)
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

      reward_stream = {'user_login': user_login, 'user_name': user_name, 'title': title, 'thumbnail_url': thumbnail_url}

      if reward_streams_count % 4 == 0:
        reward_streams.append([reward_stream])
      else:
        reward_streams[-1].append(reward_stream)

      reward_streams_count += 1

  with open('index.html', 'w') as html_file:
    html_file.write(Template(template).render(reward_streams=reward_streams, last_update=datetime.datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %z')) + '\n')
