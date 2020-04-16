"""This module is used to do profiling for methods. profiling can be visulaized or just printed to stdout
How to use it 
```
profiled(visualized=True)
def foo(): 
  for i in range(5): 
    print("test")
```
to do visualizing, add (visualize=True) when u call profiled decorator
example
profiled() # this will print the profiling results to stdout
profiled(visualized=True) # will launce a server with the visualized profiling on `http://127.0.0.1:8080/snakeviz/%2Fsandbox%2Fcode%2Fgithub%2Fjs-next%2Fjs-ng%2Fresult.prof`
to change port and host 
profiled(visualized=True, port="8008", host="0.0.0.0", print_data=True)
this will print data to stdout and launce snakeviz server on this url
`http://127.0.0.1:8080/snakeviz/foo`
"""
import json
import os.path
from cProfile import Profile

try:
    from urllib.parse import quote
except ImportError:
    from urllib import quote
from pstats import Stats
from pstats import Stats
import snakeviz
from snakeviz.stats import table_rows, json_stats

from bottle import route, run, static_file
from jinja2 import Environment, FileSystemLoader, select_autoescape

quote = lambda x, safe=False: x  # TODO check later.


snakevizpath = snakeviz.__path__[0]
settings = {
    "static_path": os.path.join(snakevizpath, "static"),
    "template_path": os.path.join(os.path.dirname(__file__), "templates"),
    "debug": True,
    "gzip": True,
}

env = Environment(loader=FileSystemLoader(settings["template_path"]), autoescape=select_autoescape(["html", "xml"]))


def _list_dir(path):
    """
    Show a directory listing.

    """
    entries = os.listdir(path)
    dir_entries = [[["..", quote(os.path.normpath(os.path.join(path, "..")), safe="")]]]
    for name in entries:
        if name.startswith("."):
            # skip invisible files/directories
            continue
        fullname = os.path.join(path, name)
        displayname = linkname = name
        # Append / for directories or @ for symbolic links
        if os.path.isdir(fullname):
            displayname += "/"
        if os.path.islink(fullname):
            displayname += "@"
        dir_entries.append([[displayname, quote(os.path.join(path, linkname), safe="")]])
    print(dir_entries)
    return dir_entries


@route("/static/<filepath:path>")
def server_static(filepath):
    return static_file(filepath, root=settings["static_path"])


@route("/snakeviz")
@route("/snakeviz/<profile_name>")
def snakeviz(profile_name=""):
    abspath = os.path.abspath(profile_name)
    if os.path.isdir(abspath):
        template = env.get_template("dir.html")
        return template.render(dir_name=abspath, dir_entries=_list_dir(abspath))
    else:
        try:
            s = Stats(profile_name)
        except:
            raise RuntimeError("Could not read %s." % profile_name)
        template = env.get_template("viz.html")
        return template.render(profile_name=profile_name, table_rows=table_rows(s), callees=json_stats(s))


def visualize(filename, host="127.0.0.1", port="8080"):
    try:
        Stats(filename)
    except Exception as e:
        print(f"{filename} is not a valid stats file")
        raise e

    url = "http://{0}:{1}/snakeviz/{2}".format(host, port, filename)
    print(f"snakeviz web server started on {host}:{port}; enter Ctrl-C to exit")
    print(url)

    run(host="localhost", port=8080, debug=True)


def profiled(visualized=False, host="127.0.0.1", port="8080", print_data=False):
    def do_profiling(func):
        def wrapper(*args, **kwargs):
            profiler = Profile()
            result = profiler.runcall(func, *args, **kwargs)
            print("done calling..")
            if print_data:
                profiler.print_stats()
            filename = func.__name__
            profiler.dump_stats(filename)
            if visualized:
                visualize(filename, host, port)
            return result

        return wrapper

    return do_profiling
