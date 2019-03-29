# picoCTF-web

The picoCTF-web component consists of a competitor facing web site, the API for running a CTF, as well as management functionality for CTF organizers.

## Features

The picoCTF-web component provides a number of core features that are common across jeopardy style CTFs such as:

- Problem List
  - Presents challenges (with optional hints)
  - Accepts flag submissions
  - Allows custom unlocking behavior where challenges can be "locked" and hidden until a competitor hits a certain threshold
- Scoreboard
  - Across a competition
  - Within a "Classroom" or sub organization
  - For individual progress within a challenge category

Additionally, the picoCTF-web component provides a number of features that are useful for running CTFs in an educational setting:

- Classrooms
  - Useful to manage multiple distinct groups of competitors as in a school setting.
- Shell server integration
  - Integration with the [picoCTF-shell component](../picoCTF-shell) allows competitors full access to a Linux machine with the necessary tools from within a web browser

## Components

1. [api](./api): This is the picoCTF-web Flask API.
2. [tests](./tests): Automated tests for picoCTF-web components.
3. [daemons](./daemons): Separate scripts that essentially run as cronjobs on the web server.
4. [web](./ansible). A frontend for interacting with the Flask API.

## Local Development <!-- markdownlint-disable MD014 -->

You can easily bring up an instance of the picoCTF-web API in Flask's development mode, which enables live reloading, a debugger, and enables debug mode within the app. To do so:

1. Ensure all development dependencies are installed (a virtual environment is recommended):

    ```shell
    $ pip install -e .[dev]
    ```

2. The picoCTF-web API has a dependency on a MongoDB server, and by default looks for one at `127.0.0.1:27017`. An easy way to bring one up is to use Docker:

    ```shell
    $ docker run -p 27017:27017 mongo
    ```

3. Point Flask to the app entrypoint, and enable development mode if desired:

    ```shell
    $ export FLASK_APP=api
    $ export FLASK_ENV=development
    $ flask run
    ```

## Testing

A MongoDB server also needs to be available at `127.0.0.1:27017` when running the tests. They will use the `ctf_test` database, so any data in the main `ctf` database from not be impacted by running the tests.

Once a MongoDB server is running, simply run `pytest` from within the `picoCTF-web` root directory.
