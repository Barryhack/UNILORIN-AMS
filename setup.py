from setuptools import setup, find_packages

setup(
    name="attendance_system",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'flask',
        'flask-sqlalchemy',
        'flask-login',
        'werkzeug',
    ],
)
