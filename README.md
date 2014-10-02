elaborate-lastfm-charts
=======================

Amazing Last.fm charts.

Installation
------------

To install the application you need Python 2.7 and a stable node.js.

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

-   Install development packages:

    ```bash
    pip install -r dev-requirements.txt
    ```

-   Install `elaborate-lastfm-charts` for development:

    ```bash
    python setup.py develop
    ```

-   Install bower and coffee-script:

    ```bash
    npm install -g bower coffee-script
    ```

-   Install front-end dependencies through bower:

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
