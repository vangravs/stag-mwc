#!/usr/bin/env python3
"""Make count table of all samples from BBMap pileup.sh rpkm tables, and two-column annotation file."""
__author__ = "Fredrik Boulund"
__date__ = "2018-04-24"
__version__ = "1.2.1"

from sys import argv, exit, stderr
from collections import defaultdict
import os.path
import argparse


def parse_args():
    desc = "{} Version v{}. Copyright (c) {}.".format(__doc__, __version__, __author__, __date__[:4])
    parser = argparse.ArgumentParser(description=desc)
    
    parser.add_argument("RPKM", nargs="+",
            help="RPKM file(s) from BBMap pileup.sh.")
    parser.add_argument("-a", "--annotations", required=True,
            help="Two-column tab-separated annotation file.")

    if len(argv) < 2:
        parser.print_help()
        exit(1)

    return parser.parse_args()


def parse_rpkm(rpkm_file):
    read_counts = {}
    with open(rpkm_file) as f:
        firstline = f.readline()
        if not firstline.startswith("#File"):
            print("ERROR: File does not look like a BBMap pileup.sh RPKM: {}".format(rpkm_file),
                    file=stderr)
        _ = [f.readline() for l in range(4)] # Skip remaining header lines: #Reads, #Mapped, #RefSequences, Table header
        for line_no, line in enumerate(f, start=1):
            try:
                ref, length, bases, coverage, reads, RPKM, frags, FPKM = line.strip().split("\t")
            except ValueError:
                print("ERROR: Could not parse RPKM file line {}:\n{}".format(line_no, rpkm_file),
                        file=stderr)
            if int(reads) != 0:
                read_counts[ref] = int(reads)
    return read_counts


def parse_annotations(annotation_file):
    annotations = {}
    with open(annotation_file) as f:
        for line_no, line in enumerate(f, start=1):
            try:
                ref, annotation = line.strip().split("\t")
            except ValueError:
                print("ERROR: Could not parse annotation file line {}:\n{}".format(line_no, annotation_file),
                        file=stderr)
            annotations[ref] = annotation
    return annotations


def merge_counts(annotations, rpkms):
    output_table = {"Unknown": [0 for n in range(len(rpkms))]}
    for annotation in set(annotations.values()):
        output_table[annotation] = [0 for n in range(len(rpkms))]
    for idx, rpkm in enumerate(rpkms):
        for ref, count in rpkm.items():
            try:
                output_table[annotations[ref]][idx] += count
            except KeyError:
                print("WARNING: Found no annotation for '{}', assigning to 'Unknown'".format(ref),
                        file=stderr)
                output_table["Unknown"][idx] += count
    return output_table


def print_table(table_data, sample_names):
    header = "\t".join(["Annotation"] + [sample_name for sample_name in sample_names])
    print(header)
    for ref, counts in table_data.items():
        print("{}\t{}".format(ref, "\t".join(str(count) for count in counts)))


if __name__ == "__main__":
    args = parse_args()

    rpkms = []
    for rpkm_file in args.RPKM:
        rpkms.append(parse_rpkm(rpkm_file))

    annotations = parse_annotations(args.annotations)
    table_data = merge_counts(annotations, rpkms)
    sample_names = [os.path.basename(fn).split(".")[0] for fn in args.RPKM]
    print_table(table_data, sample_names)

