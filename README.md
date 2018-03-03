Garmin ARchiver (`gar`)
=======================

Archive your Garmin Connect data, specifically `.tcx` activity files.

Description
-----------
This script will download your personal Garmin Connect activities as `.tcx` files.

Installation
------------
You will need python 3 -- many modern systems already have this installed.

Usage
-----

```shell
% ./gar.py -h
usage: gar.py [-h] [-V] [-v] [-n MAX_ACTIVITIES] [-P PASSCMD] [-e] [-p PATH]
              [-t] [-f]
              username

Garmin Connect activity archiver

positional arguments:
  username              username to use when logging into Garmin Connect

optional arguments:
  -h, --help            show this help message and exit
  -V, --version         display version information and exit
  -v, --verbosity       display verbose output
  -n MAX_ACTIVITIES, --max-activities MAX_ACTIVITIES
                        display verbose output
  -P PASSCMD, --passcmd PASSCMD
                        command to get password for logging into Garmin
                        Connect
  -e, --endtimestamp    set downloaded file timestamps to activity end
  -p PATH, --path PATH  root path to download into
  -t, --tcx             download exported .tcx files
  -f, --fit             download (original) .fit files
%
```

### Examples

To put your last seven activities in `/tmp/gar`:

```shell
% ./gar.py -v -n 7 -p ~/tmp/gar onoda@sohoku.jp.edu
```

(This will prompt you for your password, and nothing will show in the
terminal when you type it.)

To get all available activities, just don't use the `-n` option.

```shell
% ./gar.py -v -p ~/activities onoda@sohoku.jp.edu
```

If you use a [password manager][pass], use the `-P` option.

```shell
% ./gar.py -v -p ~/activities -P "pass garmin" onoda@sohoku.jp.edu
```

This is useful for automated archiving.

Entering your password in cleartext on the command line is left as an exercise,
if you insist.


Notes
-----

* This script is intended for personal use, and comes with no warranty.

* Garmin may make changes to their API that break this script.

  - If you're looking for a more reliable option, particularly for a
    production service, Garmin offers a [paid API].


TO-DO
-----

* consider using [requests](http://docs.python-requests.org) instead of urllib

* include an option to output a list of activities and summary statistics,
  sorted by date

History
-------
To create this script, I refactored [marcomenzel]'s [fork] of [kjkjava]'s
[garmin-connect-export], which ran in python 2, but needed some revisions to
work more reliably and add features I wanted. This is all visible in the git
history.

At this point (2ec27cc8 in the refactor branch) I've migrated to python3,
stubbed the primary steps out into their own methods, removed some
unneccesary bits, added logging, and changed the command-line options.

The original [garmin-connect-export] was a great starting point and resource,
but [gar] has turned into more of a rewrite.

Contributions
-------------
Contributions are welcome. Please fork & send a pull request.

License
-------
[MIT](https://github.com/bluesquall/garmin-connect-export/blob/master/LICENSE) &copy; 2017 M J Stanway

-------------
[gar]: https://github.com/bluesquall/gar
[pass]: https://www.passwordstore.org
[kjkjava]: https://github.com/kjkjava/
[garmin-connect-export]: https://github.com/kjkjava/garmin-connect-export
[marcomenzel]: https://github.com/marcomenzel/
[fork]: https://github.com/marcomenzel/garmin-connect-export
[paid API]: https://developer.garmin.com/garmin-connect-api/overview/
