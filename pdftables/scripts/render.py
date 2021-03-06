#!/usr/bin/env python

"""pdftables-render: obtain pdftables debugging information from pdfs

Usage:
    pdftables-render [options] <pdfpath>...
    pdftables-render (-h | --help)
    pdftables-render --version

Example page number lists:

    <pdfpath> may contain a [:page-number-list].

    pdftables-render my.pdf:1
    pdftables-render my.pdf:2,5-10,15-

Example JSON config options:

    '{ "n_glyph_column_threshold": 3, "n_glyph_row_threshold": 5 }'

Options:
    -h --help                   Show this screen.
    --version                   Show version.
    -D --debug                  Additional debug information
    -O --output-dir=<path>      Path to write debug data to
    -a --ascii                  Show ascii table
    -p --pprint                 pprint.pprint() the table
    -i --interactive            jump into an interactive debugger (ipython)
    -c --config=<json>          JSON object of config parameters

"""

# Use $ pip install --user --editable pdftables
# to install this util in your path.

import sys
import os
import json

import pdftables

from os.path import basename
from pprint import pprint

from docopt import docopt

from pdftables.pdf_document import PDFDocument
from pdftables.diagnostics import render_page, make_annotations
from pdftables.display import to_string
from pdftables.pdftables import page_to_tables
from pdftables.config_parameters import ConfigParameters


def main(args=None):

    if args is not None:
        argv = args
    else:
        argv = sys.argv[1:]

    arguments = docopt(
        __doc__,
        argv=argv,
        version='pdftables-render experimental')

    if arguments["--debug"]:
        print(arguments)

    if arguments["--config"]:
        kwargs = json.loads(arguments["--config"])
    else:
        kwargs = {}
    config = ConfigParameters(**kwargs)

    for pdf_filename in arguments["<pdfpath>"]:
        render_pdf(arguments, pdf_filename, config)


def ensure_dirs():
    try:
        os.mkdir('png')
    except OSError:
        pass

    try:
        os.mkdir('svg')
    except OSError:
        pass


def parse_page_ranges(range_string, npages):
    ranges = range_string.split(',')
    result = []

    def string_to_pagenumber(s):
        if s == "":
            return npages
        return int(x)

    for r in ranges:
        if '-' not in r:
            result.append(int(r))
        else:
            # Convert 1-based indices to 0-based and make integer.
            points = [string_to_pagenumber(x) for x in r.split('-')]

            if len(points) == 2:
                start, end = points
            else:
                raise RuntimeError(
                    "Malformed range string: {0}"
                    .format(range_string))

            # Plus one because it's (start, end) inclusive
            result.extend(xrange(start, end + 1))

    # Convert from one based to zero based indices
    return [x - 1 for x in result]


def render_pdf(arguments, pdf_filename, config):
    ensure_dirs()

    page_range_string = ''
    page_set = []
    if ':' in pdf_filename:
        pdf_filename, page_range_string = pdf_filename.split(':')

    doc = PDFDocument.from_path(pdf_filename)

    if page_range_string:
        page_set = parse_page_ranges(page_range_string, len(doc))

    for page_number, page in enumerate(doc.get_pages()):
        if page_set and page_number not in page_set:
            # Page ranges have been specified by user, and this page not in
            continue

        svg_file = 'svg/{0}_{1:02d}.svg'.format(
            basename(pdf_filename), page_number)
        png_file = 'png/{0}_{1:02d}.png'.format(
            basename(pdf_filename), page_number)

        table_container = page_to_tables(page, config)
        annotations = make_annotations(table_container)

        render_page(
            pdf_filename, page_number, annotations, svg_file, png_file)

        print "Rendered", svg_file, png_file

        if arguments["--interactive"]:
            from ipdb import set_trace
            set_trace()

        for table in table_container:

            if arguments["--ascii"]:
                print to_string(table.data)

            if arguments["--pprint"]:
                pprint(table.data)


