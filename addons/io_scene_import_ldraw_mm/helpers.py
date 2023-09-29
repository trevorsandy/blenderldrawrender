import csv
import io
import re
import codecs
import json
import sys
import datetime
import configparser
from pathlib import Path
import os

try:
    from .definitions import APP_ROOT
except ImportError as e:
    print(e)
    import traceback
    print(traceback.format_exc())
    from definitions import APP_ROOT


# remove multiple spaces
def clean_line(line):
    return " ".join(line.split())


# assumes cleaned line being passed
def get_params(clean_line, lowercase=False):
    parts = clean_line.split()
    if lowercase:
        return [x.lower() for x in parts]
    return parts


def parse_csv_line(line, min_params=0):
    try:
        parts = list(csv.reader(io.StringIO(line), delimiter=' ', quotechar='"', skipinitialspace=True))
    except csv.Error as e:
        print(e)
        import traceback
        print(traceback.format_exc())
        parts = [re.split(r"\s+", line)]

    if len(parts) == 0:
        return None

    _params = parts[0]

    if len(_params) == 0:
        return None

    while len(_params) < min_params:
        _params.append("")
    return _params


def fix_string_encoding(string):
    new_string = string
    if type(string) is str:
        new_string = bytes(string.encode())
    for codec in [codecs.BOM_UTF8, codecs.BOM_UTF16, codecs.BOM_UTF32]:
        new_string = new_string.replace(codec, b'')
    new_string = new_string.decode()
    return new_string


def write_json(filepath, obj, indent=None, do_print=False):
    try:
        full_path = os.path.join(APP_ROOT, filepath)
        Path(os.path.dirname(full_path)).mkdir(parents=True, exist_ok=True)
        with open(full_path, 'w', encoding='utf-8', newline="\n") as file:
            j = json.dumps(obj, indent=indent, ensure_ascii=False)
            if do_print:
                print(j)
            file.write(j)
    except Exception as e:
        print(e)
        import traceback
        print(traceback.format_exc())


def read_json(filepath, default=None):
    try:
        full_path = os.path.join(APP_ROOT, filepath)
        with open(full_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        print(e)
        import traceback
        print(traceback.format_exc())
        return default


def read_ini(ini_file, default=None):
    assert ini_file != "", "LDrawRendererPreferences.ini file was not specified."
    try:
        section_name = 'ImportLDrawMM'
        config = configparser.RawConfigParser()
        read = config.read(ini_file)
        if read and config[section_name]:
            for section in config.sections():
                if section != section_name:
                    config.remove_section(section)
            return config
        else:
            return default
    except Exception as e:
        print(e)
        return default


def valid_lines(f):
    """Skip blank and commented lines"""
    for l in f:
        line = l.rstrip()
        if line and line[:1] != "#":
            yield line


def valid_value(value, decimal=False):
    """Ensure value is either integer or decimal as specified"""
    for s in value:
        if decimal:
            try:
                float(s)
            except ValueError:
                return False
        else:
            try:
                int(s)
            except ValueError:
                return False
    return True


def evaluate_value(x):
    if x == 'True':
        return True
    elif x == 'False':
        return False
    elif is_int(x):
        return int(x)
    elif is_float(x):
        return float(x)
    else:
        return x


def is_float(x):
    try:
        f = float(x)
    except (TypeError, ValueError):
        return False
    else:
        return True


def is_int(x):
    try:
        f = float(x)
        i = int(f)
    except (TypeError, ValueError):
        return False
    else:
        return f == i


def render_print(message,is_error=False):
    """Print output with identification timestamp."""

    # Current timestamp (with milliseconds trimmed to two places)
    timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-4]

    message = f"{timestamp} [loadldrawMM] {message}"

    if is_error:
        sys.stderr.write(f"{message}\n")
        sys.stderr.flush()
    else:
        sys.stdout.write(f"{message}\n")
        sys.stdout.flush()


def clamp(num, min_value, max_value):
    return max(min(num, max_value), min_value)


def ensure_bmesh(bm):
    bm.faces.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()


def finish_bmesh(bm, mesh):
    bm.to_mesh(mesh)
    bm.clear()
    bm.free()


def finish_mesh(mesh):
    mesh.validate()
    mesh.update(calc_edges=True)


def hide_obj(obj):
    obj.hide_viewport = True
    obj.hide_render = True


def show_obj(obj):
    obj.hide_viewport = False
    obj.hide_render = False
