import argparse
from bam_alignment import *
from flask import Flask
from flask import request
from display_html import *
import os
import re
import sys
app = Flask(__name__)
app.debug = True

BAMDIR = "."
REFFILE = ""
PORT = 5000
HOST = "127.0.0.1"
BAMFILE_TO_BAMVIEW = {}
SETTINGS = {}

@app.route("/")
def listbams(methods=['POST','GET']):
    bamfiles = request.args.getlist("bamfiles")
    if len(bamfiles) > 0:
        return display_bam(bamfiles)
    files = os.listdir(BAMDIR)
    bamfiles = [f for f in files if re.match(".*.bam$", f) is not None]
    bamfiles = [f for f in bamfiles if f+".bai" in files]
    html = "<h1>Indexed bam files in this directory</h1>"
    html += "<form>"
    html += "<input type='submit', value='View selected bams'><br>"
    for f in bamfiles:
        html += "<input type='checkbox' name='bamfiles', value=%s><a href='/%s' target='_blank'>%s</a><br>"%(f,f,f)
    html += "</form>"
    return html

@app.route('/<string:bamfiles>', methods=['POST', 'GET'])
def display_bam(bamfiles):
    if type(bamfiles) != list:
        bamfiles = [bamfiles]
    region = request.args.get("region","")
    region.replace("%3A",":")
    return display_bam_region(bamfiles, region)

@app.route('/<string:bamfile>:<string:region>')
def display_bam_region(bamfiles, region):
    if type(bamfiles) != list: bamfiles = [bamfiles]
    if ";".join(bamfiles) not in BAMFILE_TO_BAMVIEW:
        bv = BamView(["%s/%s"%(BAMDIR, bam) for bam in bamfiles], REFFILE)
        BAMFILE_TO_BAMVIEW[";".join(bamfiles)] = bv
    else: bv = BAMFILE_TO_BAMVIEW[";".join(bamfiles)]
    try:
        chrom, pos = region.split(":")
        pos = int(pos)
    except: 
        try:
            chrom, pos = sorted(bv.reference.keys())[0], 0
        except: chrom, pos = "None", 0
    bv.LoadAlignmentGrid(chrom, pos, _settings=SETTINGS)
    positions = bv.GetPositions(pos)
    region = "%s:%s"%(chrom, pos)
    SETTINGS["region"] = region
    html = GetHeader(bamfiles, region, REFFILE, set(bv.read_groups.values()))
    html += GetToolbar(chrom, pos, bamfiles, SETTINGS)
    html += GetReference(bv.GetReferenceTrack(pos), chrom, positions)
    html += GetAlignment(bv.GetAlignmentTrack(pos), len(bv.GetReferenceTrack(pos)), chrom, positions)
    html += GetFooter()
    return html

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='pybamview')
    parser.add_argument('--bamdir', help='Directory to look for bam files. Bam files must be indexed.')
    parser.add_argument('--ref', help='Path to reference fasta file. If no reference is given, the reference track is displayed as "N"\'s')
    parser.add_argument('--ip', help='Host IP. 127.0.0.1 for local host (default). 0.0.0.0 to have the server available externally.')
    parser.add_argument('--port', help='The port of the webserver. Defaults to 5000.')
    args = parser.parse_args()
    if args.bamdir is not None:
        BAMDIR = args.bamdir
    if args.ref is not None:
        REFFILE = args.ref
    if args.port is not None:
        PORT = int(args.port)
    if args.ip is not None:
        HOST = args.ip
    app.run(port=PORT, host=HOST)
