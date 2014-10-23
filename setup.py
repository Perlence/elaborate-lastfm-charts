from setuptools import setup, find_packages

setup(
    name='elaborate-lastfm-charts',
    description='Amazing Last.fm charts.',
    version='0.1.0',
    author='Sviatoslav Abakumov, Anastasiya Kozayeva',
    author_email='dust.harvesting@gmail.com',
    url='https://github.com/Perlence/elaborate-lastfm-charts',
    platforms=['MacOS X', 'Unix', 'POSIX'],
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'startapp = elaboratecharts.app:start',
            'debugapp = elaboratecharts.app:debug',
        ],
    },
    install_requires=[
        'arrow',
        'Flask',
        'Flask-Assets',
        'gevent',
        'lastfmclient',
        'redis',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'License :: OSI Approved :: BSD License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Unix',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Framework :: Flask',
    ],
)
