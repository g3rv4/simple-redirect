# simple-redirect

An easy to use redirection script. What for? ehh... to have nice urls :D

## Features
* supports multiple domains
* exposes an endpoint to reload the URLs
* if needed, it's able to execute a different script for each domain after the URLs are reloaded (useful if you need to invalidate a cache on a different server)
* it integrates nicely with github and cloudflare (because well... that's *exactly* my use case)

## How it works
1. You define your URLs either using yaml or json files and make them accessible somewhere (see [my redirections file](https://raw.githubusercontent.com/g3rv4/redirections/master/urls.json) for an example... hosted by github!).
2. You hit the `/refresh` endpoint for the script to load the URLs into redis
3. If you want, it executes a script you define after the domain URLs are refreshed

## How I use it
* I have a free account with cloudflare, that's caching everything to get crazy speeds
* I store the redirections file in github
* I set up a webhook in the github repository so that when it receives a push it hits the `/refresh` endpoint
* * Github has a delay before it shows the updated file version, so I set up the webhook so that it sends `&wait=10`. What this does is just... well, waiting 10 seconds before grabbing the file from github :)
* * I also pass `&domain=gmc.uy`, so that when *my* repository gets updated, only my script is executed
* After the data is refreshed, I run a script that purges cloudflare's cache

## How to set it up
Well, this could be the hardest part... it uses python, it has a couple dependencies, it uses redis... you could totally set it up (it's fairly standard) but the recommended way is to use [the dockerized version](https://hub.docker.com/r/g3rv4/simple-redirect/) that takes care of everything. You can see the [Dockerfile](https://hub.docker.com/r/g3rv4/simple-redirect/~/dockerfile/) to see what I'm doing, but it's fairly straightforward.

If you set it up using docker-compose, then this is my `docker-compose.yml`

```yml
version: '2'
services:
  simple-redirect:
    image: 'g3rv4/simple-redirect'
    restart: always
    environment:
      - REDIS_HOST=localhost
      - REDIS_DB=1
      - CONFIG_FILE=/var/config/config.json
    volumes:
      - '/path/to/config:/var/config'
    ports:
      - '8000:8000'
```

Once you have that running, it exposes the app in the port 8000. You may probably want to put an nginx between the app server and internet. You should mount `/var/config` containing a configuration file... here's mine for reference

```json
{
    "key": "thisIsACrazySecretNobodyKnows",
    "domains": {
        "gmc.uy": {
            "urls": "https://raw.githubusercontent.com/g3rv4/redirections/master/urls.json",
            "afterRefresh": "/var/config/clear-cache.sh -zone myZoneId"
        },
        "dv.uy": {
            "urls": "https://raw.githubusercontent.com/d4tagirl/redirections/master/urls.yml",
            "afterRefresh": "/var/config/clear-cache.sh -zone anotherZoneId"
        }
    }
}
```

and if you're running scripts (as I am) they should also go in the config folder. Feel free to check out [my blog post about it](https://gmc.uy/nice-urls) :)