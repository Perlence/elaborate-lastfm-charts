from setuptools import setup, find_packages

setup(
    name='Elaborate-Last.fm-Charts',
    description='Amazing Last.fm charts.',
    version='0.1',
    author='Sviatoslav Abakumov',
    author_email='dust.harvesting@gmail.com',
    url='https://github.com/Perlence/elaborate-lastfm-charts',
    platforms=['MacOS X', 'Unix', 'POSIX'],
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'arrow',
        'Flask',
        'gevent',
        'mongokit',
        'pylast',
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
