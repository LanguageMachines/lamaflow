#!/usr/bin/env python3

import sys
import os
import json
import argparse
import folia.main as folia
from foliatools import VERSION as TOOLVERSION
from foliatools.foliaid import assignids


def process(inputfile, outputfile, metadatadir,oztfile):
    docid = os.path.basename(inputfile).split('.')[0]
    metadatafile = os.path.join(metadatadir, docid + '.json')
    hasmetadata = os.path.exists(metadatafile)
    doc = folia.Document(file=inputfile)
    doc.provenance.append( folia.Processor.create("PICCL/nederlab.nf/addmetadata.py") )

    if hasmetadata:
        with open(metadatafile,'r') as f:
            data = json.load(f)
        for key, value in sorted(data.items()):
            doc.metadata[key] = value
        print("Added metadata from JSON file for " + id,file=sys.stderr)

    if oztfile:
        addsubmetadata_ozt(doc, oztfile, metadatadir)

    assignids(doc)
    doc.provenance.processors[-1].append( folia.Processor.create(name="foliaid", version=TOOLVERSION, src="https://github.com/proycon/foliatools") )

    if outputfile == '-':
        print(doc.xmlstring())
    else:
        doc.save(outputfile)

def addsubmetadata_ozt(doc, oztfile, metadatadir):
    expected = 0
    with open(oztfile,'r') as f:
        for line in f:
            fields = line.strip().split("\t")
            if len(fields) == 2:
                if fields[0] == doc.id:
                    expected = int(fields[1])
                    break
    #verify
    found = 0
    if found:
       # "divs of type chapter with descendant head of type h3 will be put in a separate documents (ozt: onzelfstandige titels)" (ETKS)
        for div in doc.select(folia.Division, "https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/tei2folia/divisions.foliaset.ttl"):
            if div.cls == "chapter":
                if any( True for head in div.select(folia.Head, "https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/tei2folia/heads.foliaset.ttl") if head.cls == "h3"):
                    found += 1
                    seq_id = str(found).zfill(4)
                    ozt_id = doc.id + "_" + seq_id
                    div.id = ozt_id  + ".text"
                    div.metadata = ozt_id  + ".metadata"
                    doc.submetadata[ozt_id + ".metadata"] = folia.NativeMetaData()
                    metadatafile = os.path.join(metadatadir, ozt_id + '.json')
                    if os.path.exists(metadatafile):
                        with open(metadatafile,'r') as f:
                            data = json.load(f)
                        for key, value in sorted(data.items()):
                            doc.submetadata[ozt_id + ".metadata"][key] = value
                        print("Added submetadata from JSON file for " + ozt_id,file=sys.stderr)
                    else:
                        print("No submetadata for " + ozt_id,file=sys.stderr)

    if found != expected:
        print("WARNING: Found " + str(found) + " OZT chapters, expected " + str(expected) ,file=sys.stderr)
    return found == expected

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-d','--metadatadir', type=str,help="Collect JSON metadata files from this directory (with a similar basename as the input document)", action='store',default=".",required=False)
    parser.add_argument('-o','--output', type=str,help="Output file (defaults to stdout)", action='store',default="-",required=False)
    parser.add_argument('--oztfile', type=str,help="Input file containing 'Onzelfstandige Titels'", action='store',default=None,required=False)
    parser.add_argument('file', nargs=1, help='input document')
    args = parser.parse_args()
    process(args.file, args.output, args.metadatadir,args.oztfile)
