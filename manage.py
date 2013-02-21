from flask.ext.script import Manager
from mgserver import create_app


app = create_app()
manager = Manager(app)


@manager.command
def run():
    """Run local server."""

    app.run()


if __name__ == "__main__":
    manager.run()
