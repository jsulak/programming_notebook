#!/usr/bin/python

"""
Script to process and create reminders for programming notebook.
"""

from  __future__ import print_function
import sys, os, fileinput, re, time, datetime, ConfigParser


def process_directory(dir):
    os.chdir(os.path.expanduser(dir))
    files = os.popen('grep -El "[^\\s]remind\\(.*?\\)" *.{md,txt,taskpaper,ft,doentry} 2>/dev/null').read().strip()

    # Iterate over matched filesn
    for file in files.split("\n"):
        process_file(file)


def process_file(file):
    done_re = re.compile(r"\s@(done|cancell?ed)")
    reminder_re = re.compile(r"([^\s\"`'\(\[])remind\((.*)(\s\"(.*?)\")?\)")

    # Store access and modification times so we can preserve them
    mod_times = (os.path.getatime(file), os.path.getmtime(file))
    current_time_string = time.strftime("%Y-%m-%d")

    # For each matched file, open, and iterate over lines
    for line in fileinput.input(file, inplace=1):
        done = done_re.search(line)
        date_match = reminder_re.search(line)

        # Tagged with a reminder and not marked done?
        if (date_match and not done):
            try:
                remind_date_epoch = time.mktime(time.strptime(date_match.groups()[1], "%Y-%m-%d"))
            except ValueError:
                print(line, end="")
                continue

            # Is it timely?  If yes, then remind!
            if (remind_date_epoch <= time.time()):
                stripped_line = line[:date_match.start()] + line[date_match.end():]
                stripped_line = re.sub(r"^[\-\*\+] ", "", stripped_line).strip()
                remind(stripped_line, file)

                # @remind(..) -> @reminded(..) in original file
                line = line[:date_match.start()] + "@reminded(" + current_time_string + ")" + line[date_match.end():]

        print(line, end="")

    # Preserve original timestamp
    os.utime(file, mod_times)


def remind(name, body):
    os.popen("""osascript <<'APPLESCRIPT'
        tell application "Reminders"
        if name of lists does not contain "Reminders" then
          set _reminders to item 1 of lists
        else
          set _reminders to list "Reminders"
        end if
        make new reminder at end of _reminders with properties {name:"%s", body:"%s"}
      end tell
    APPLESCRIPT""" % (name, body))


if __name__ == "__main__":
    config = ConfigParser.ConfigParser()
    config.read("config.ini")
    dir = config.get('Notebook', 'directory')
    process_directory(dir)
