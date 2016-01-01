from setuptools import setup, find_packages

__version__ = '0.1'

setup(
    name='wanikani',
    description='WaniKani Tools for Python',
    long_description=open('README.md').read(),
    author='Paul Traylor',
    url='http://github.com/kfdm/wanikani/',
    version=__version__,
    packages=find_packages(),
    install_requires=['requests'],
    # http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
    ],
    entry_points={
        'console_scripts': [
            'wk = wanikani.cli:main',
            'wanikani = wanikani.django.manage:main [django]',
        ]
    },
    extras_require={
        'django': [
            'dj_database_url',
            'Django >= 1.9, < 1.10',
            'django-cache-url',
            'envdir',
            'icalendar',
            'python-social-auth',
            'raven',
        ],
    }
)
