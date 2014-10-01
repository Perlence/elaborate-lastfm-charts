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

`elaborate-lastfm-charts` creates following scripts:

-   `ec-start` &ndash; start the server
-   `ec-debug` &ndash; start the server and enable debugging
-   `ec-build` &ndash; build assets
-   `ec-watch` &ndash; watch for changes in asset files
