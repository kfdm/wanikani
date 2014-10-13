from setuptools import setup

setup(
    name='django-wanikani',
    description='Django App for wanikani tools',
    author='Paul Traylor',
    url='http://github.com/kfdm/django-wanikani/',
    packages=['django_wanikani'],
    install_requires=[
        'Django>=1.7',
        'icalendar',
        'wanikani',
    ],
    entry_points={
        'console_scripts': [
            'django-wanikani = django_wanikani.manage:main'
        ]
    }
)
