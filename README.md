elaborate-lastfm-charts
=======================

Amazing Last.fm charts.

Installation
------------

To install the application you need Python 2.7, Ruby, and a stable node.js.
Also you need Redis to cache data from Last.fm.

-   Clone the repository:

    ```bash
    git clone https://github.com/Perlence/elaborate-lastfm-charts.git
    cd elaborate-lastfm-charts
    ```

-   Create and activate virtual environment:

    ```bash
    virtualenv env
    . env/bin/activate
    ```

-   Install requirements:

    ```bash
    pip install -r requirements.txt -r dev-requirements.txt
    ```

-   Install `elaborate-lastfm-charts` for development:

    ```bash
    python setup.py develop
    ```

-   Install Bower, CoffeeScript, Sass, and Autoprefixer:

    ```bash
    npm install -g bower coffee-script autoprefixer
    gem install sass
    ```

-   Install front-end dependencies using Bower:

    ```bash
    bower install
    ```

-   Create a config from template:

    ```bash
    cp elaboratecharts/default.json elaboratecharts/config.json
    ```

-   Put actual values into the config.

`elaborate-lastfm-charts` creates following entry points:

-   `startapp` &ndash; start the web server.
-   `debugapp` &ndash; start the server and enable debugging.
