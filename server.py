import json
import os
import redis
import requests
import yaml
import subprocess
import time
from flask import Flask, request, redirect, abort

app = Flask(__name__)
redis_cli = None

config_file = os.environ['CONFIG_FILE']
with open(config_file) as data_file:
    config = json.load(data_file)


def init_redis_cli():
    global redis_cli
    if redis_cli is None:
        redis_cli = redis.StrictRedis(host=os.environ['REDIS_HOST'], db=os.environ['REDIS_DB'])


@app.route('/refresh', methods=['GET', 'POST'])
def refresh():
    if config['key'] != request.args.get('key'):
        abort(401)

    if request.args.get('wait'):
        time.sleep(int(request.args.get('wait')))

    init_redis_cli()
    redis_cli.flushdb()
    for domain in config['domains'].keys():
        domain_data = config['domains'][domain]
        domain_file = domain_data['urls']

        try:
            data = requests.get(domain_file + '?_=%i' % int(round(time.time() * 1000))).content
            if domain_file.endswith('.yml'):
                data = yaml.load(data)
            else:
                data = json.loads(data)
        except:
            continue

        for slug in data.keys():
            redis_cli.set('url:%s:%s' % (domain, slug), data[slug])

        # only clear the cache if there's no domain specified or if the domain specified matches the domain we've just processed
        if 'afterRefresh' in domain_data and (request.args.get('domain') is None or domain == request.args.get('domain')):
            subprocess.Popen(domain_data['afterRefresh'])

    return 'OK'


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    init_redis_cli()
    dest = redis_cli.get('url:%s:%s' % (request.headers['Host'], path))
    if dest:
        return redirect(dest, 301)
    return 'Page not found', 404

if __name__ == "__main__":
    app.run(debug=True)
