try:
    from setuptools import setup
    kwargs = {
        'entry_points': {
            'console_scripts': [
                'wk = wanikani.cli:main'
            ]
        }
    }
except ImportError:
    from distutils.core import setup
    kwargs = {
        'scripts': ['scripts/wk']
    }

__version__ = '0.1'

setup(
    name='wanikani',
    description='Python Library for WaniKani',
    long_description=open('README.md').read(),
    author='Paul Traylor',
    url='http://github.com/kfdm/wanikani/',
    version=__version__,
    packages=['wanikani'],
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
    **kwargs
)
