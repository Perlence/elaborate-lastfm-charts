elaborate-lastfm-charts
=======================

Amazing Last.fm charts.

Installation
------------

To install the application you need Python 3.5 or later and a stable Node.js.
Also you need Redis to cache the data from Last.fm.

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
    pip install -r requirements.txt
    ```

-   Install Bower, CoffeeScript, and Sass:

    ```bash
    npm install
    export PATH="$PWD/node_modules/.bin:$PATH"
    ```

-   Install front-end dependencies using Bower:

    ```bash
    bower install
    ```

-   Create a config from template:

    ```bash
    cp elaboratecharts/default.json elaboratecharts/config.json
    ```

-   Put the actual values into the config.

- Run the server:

    ```bash
    gunicorn elaboratecharts.app:app
    ```
