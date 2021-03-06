#!/usr/bin/env nextflow

/*
vim: syntax=groovy
-*- mode: groovy;-*-
*/

log.info "-----------------------------"
log.info "FoLiA Entity Linker Pipeline"
log.info "-----------------------------"

def env = System.getenv()

params.virtualenv =  env.containsKey('VIRTUAL_ENV') ? env['VIRTUAL_ENV'] : ""
params.extension = "folia.xml"
params.outputdir = "dbnl_output"
params.entitylinking = "slh"; //Methods correspond to FoliaEntity.exe -m option
params.entitylinkerurioptions = ""; //Extra options for entity linker, will be passed as -u to FoLiAEntity"

if (params.containsKey('help') || !params.containsKey('inputdir')) {
    log.info "Usage:"
    log.info "  entitylinker.nf [OPTIONS]"
    log.info ""
    log.info "Mandatory parameters:"
    log.info "  --inputdir DIRECTORY     Input directory (FoLiA documents)"
    log.info""
    log.info "Optional parameters:"
    log.info "  --virtualenv PATH        Path to Virtual Environment to load (usually path to LaMachine)"
    log.info "  --entitylinking METHODS  Do entity linking according to specified methods (see -m option of FoliaEntity)"
    log.info "  --entitylinkerurioptions X  Extra options to pass to entity linker -u"
    log.info "  --outputdir DIRECTORY    Output directory (FoLiA documents)"
    exit 2
}

foliadocuments = Channel.fromPath(params.inputdir+"/*." + params.extension)

process entitylinker {
    publishDir params.outputdir, mode: 'copy', overwrite: true

    input:
    file document from foliadocuments
    val virtualenv from params.virtualenv
    val methods from params.entitylinking
    val extraoptions from params.entitylinkerurioptions

    output:
    file "${document.simpleName}.linked.folia.xml" into entitylinker_output


    script:
    """
    set +u
    if [ ! -z "${virtualenv}" ]; then
        source ${virtualenv}/bin/activate
        rootpath=${virtualenv}
    else
        rootpath=/opt
    fi
    set -u

    mkdir out
    if [ ! -z "${extraoptions}" ]; then
        extraoptions="-u ${extraoptions}"
    else
        extraoptions=""
    fi
    \$rootpath/foliaentity/FoliaEntity.exe -w -a "foliaentity" -m ${methods} \$extraoptions -i "${document}" -o out/
    zcat out/\$(basename "${document}").gz > "${document.simpleName}.linked.folia.xml"
    """
}

entitylinker_output.subscribe { println "Output document written to " +  params.outputdir + "/" + it.name }
