#!/usr/bin/python

"""
Manipulates the current day's programming notebook entry.
"""

from  __future__ import print_function
import os, datetime, re, argparse, fileinput, subprocess, ConfigParser

NOTES_DIR = None
today = datetime.date.today()
entrytime = today.strftime("%Y-%m-%d")
filename = ""

def find_previous_entry(date):
    """Find the first entry previous to the given date."""

    day_of_year = today.timetuple().tm_yday
    year = today.timetuple().tm_year

    # Search backwards for the previous entry
    for day in range(day_of_year - 1, 0, -1):
        past_day = datetime.datetime(year, 1, 1) + datetime.timedelta(day - 1)
        past_day_filename = past_day.strftime("%Y-%m-%d") + ".md"
        
        if os.path.isfile(os.path.join(NOTES_DIR, past_day_filename)):
            return past_day_filename

    # Return blank string if none found
    return ""


def find_tasks_to_shift(date):
    """Returns a list of tasks that need to be shifted to the entry for the given date."""

    previous_entry = find_previous_entry(date)

    # If there is no previous entry, punt
    if previous_entry == "":
        return

    # Find all tasks and put in list
    task_section = False
    tasks = []
    
    for line in fileinput.input(os.path.join(NOTES_DIR, previous_entry)):        
        if "## Tasks.todo" in line:
            task_section = True
        elif line.startswith("##"):
            task_section = False
        elif task_section:
            line = line.strip()
            if line != "":
                tasks.append(line)

    # Iterate over tasks and fine undated and incomplete tasks to shift
    # TODO: Share with reminders.py somehow
    done_re = re.compile(r"\s@(done|cancell?ed)")
    reminder_re = re.compile(r"([^\s\"`'\(\[])remind(ed)?\((.*)(\s\"(.*?)\")?\)")

    tasks_to_shift = []
    for task in tasks:
        done = done_re.search(task)
        date_match = reminder_re.search(task)

        # Only shift incomplete and untimestamped tasks
        if (not done and not date_match):
            tasks_to_shift.append(task)

    return tasks_to_shift


def create_entry():
    """Create a new programming notebook entry for today."""
    
    with open(filename, "w") as logfile:
        logfile.write("Title: " + today.strftime("%b %d, %Y") + "\n");
        logfile.write("Date: " + entrytime + "\n");
        logfile.write("Tags:\n\n## Notes\n\n\n\n## Tasks.todo\n\n")
        
        # Get unfinished and undated tasks from previous entry
        logfile.write("\n".join(find_tasks_to_shift(today)))
        logfile.write("\n\n## Log\n\n");


def tag_line(line, tag):
    if "Tags:" not in line:
        return line
    tag_line = re.split("Tags:\s+", line)[1]
    tags = [s.strip() for s in re.split(",\s+", tag_line) if s != ""]
    tags.append(tag)
    tags = list(set(tags))  # Get unique values
    tags.sort()
    line = "Tags: " + ", ".join(tags) + "\n"
    return line

def add_tag(tag):
    for line in fileinput.input(filename, inplace=1):
        print(tag_line(line, tag), end="")

def add_log(entry):
    # This is inefficient, but this is the easiest
    line = subprocess.check_output(['tail', '-1', filename])
    newline = "\n" if ("\n" not in line) else ""

    timestamp = datetime.datetime.now().strftime("%I:%M %p").lstrip('0')
    with open(filename, "a") as logfile:
        logfile.write(newline + "- " + timestamp + " - " + entry)

def add_task(task):
    task_section = False
    for line in fileinput.input(filename, inplace=1):        
        if "## Tasks.todo" in line:
            task_section = True
            print(line, end="")
        elif task_section:
            print("")
            print("- " + task)
            task_section = False
        else:
            print(line, end="")

            
if __name__ == "__main__":
    config = ConfigParser.ConfigParser()
    config.read("config.ini")
    NOTES_DIR = config.get('Notebook', 'directory')
    NOTES_DIR = os.path.expanduser(NOTES_DIR)
    filename = os.path.join(NOTES_DIR, filename)


    parser = argparse.ArgumentParser(description="Add a tag or log entry.")
    parser.add_argument('-t', '--tag', dest='tag', type=str)
    parser.add_argument('-l', '--log', dest='log', type=str)
    parser.add_argument('--task', dest='task', type=str)
    args = parser.parse_args()

    filename = os.path.join(NOTES_DIR, entrytime + ".md")
    print(filename)

    # Before we operate on the file, create the entry if it doesn't     
    if not os.path.isfile(filename):
        create_entry()
    
    if (args.tag):
        add_tag(args.tag)
    if (args.log):
        add_log(args.log)
    if (args.task):
        add_task(args.task)
    
