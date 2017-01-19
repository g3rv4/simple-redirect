import json
import os
import redis
import requests
import yaml
from flask import Flask, request, redirect, abort

app = Flask(__name__)
redis_cli = redis.StrictRedis(host=os.environ['REDIS_HOST'], db=os.environ['REDIS_DB'])


@app.route('/refresh')
def refresh():
    config_file = os.environ['CONFIG_FILE']
    with open(config_file) as data_file:
        config = json.load(data_file)

    if config['key'] != request.args.get('key'):
        abort(401)

    redis_cli.flushdb()
    for domain in config['domains'].keys():
        domain_file = config['domains'][domain]

        try:
            data = requests.get(domain_file).content
            if domain_file.endswith('.yml'):
                data = yaml.load(data)
            else:
                data = json.loads(data)
        except:
            continue

        for slug in data.keys():
            redis_cli.set('url:%s:%s' % (domain, slug), data[slug])

    return 'OK'


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    dest = redis_cli.get('url:%s:%s' % (request.headers['Host'], path))
    if dest:
        return redirect(dest, 301)
    return 'Page not found', 404

if __name__ == "__main__":
    app.run(debug=True)
