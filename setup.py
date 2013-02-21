"""
MGServer Web API
----------------

Web application that exports RESTful API for MGServer
"""

from setuptools import setup

setup(
    name='MGServer',
    version='0.0.1',
    url='https://www.github.com/Avamagic/mgserver-web-api/',
    license='BSD',
    author='Ron Huang',
    author_email='ronhuang@avamagic.com',
    description='Web application that exports RESTful API for MGServer',
    long_description=__doc__,
    packages=['mgserver'],
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        'Flask',
        'Flask-Bcrypt',
        'flask-OAuthProvider',
        'Flask-RESTful',
        'Flask-WTF',
        'flask-Login',
        'Flask-Script',
        'Flask-Babel',
        'Flask-Testing',
        'pymongo',
        'pyotp',
        'nose',
    ]
)
