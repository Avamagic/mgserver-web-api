# MGServer Web API

Web application that exports RESTful API for MGServer.

## Installation

Please refer to [Install][] for detail.

[Install]: https://github.com/Avamagic/mgserver-web-api/wiki/Install

## Development

### Prepare environment

    $ git clone git@github.com:Avamagic/mgserver-web-api
    $ cd mgserver-web-api
    $ virtualenv venv
    $ source venv/bin/activate
    $ pip install -r requirements.txt

### Run on local machine

    $ python manager.py runserver

### Unit test

    $ nosetests --with-coverage --cover-package=mgserver
