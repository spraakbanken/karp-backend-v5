import sys
import karp_backend
from karp_backend.cli import create_metadata as metadata
from karp_backend.cli import upload_offline as upload
from karp_backend.cli import getmapping as gm

# TODO move stuff from upload_offline here, leave the real code there
usage = """
|SCRIPT| --create_metadata
    Generate 'config/fieldmappings.json' from the 'config/mappings/fieldmappings_*.json' files.

|SCRIPT| --create_mode MODE SUFFIX
|SCRIPT| --create_empty_index MODE SUFFIX
|SCRIPT| --import_mode MODE SUFFIX
|SCRIPT| --publish_mode MODE SUFFIX
|SCRIPT| --reindex_alias MODE SUFFIX
|SCRIPT| --getmapping ALIAS OUTFILE
|SCRIPT| --internalize_lexicon MODE LEXICON1 [LEXICON2 LEXICON3 ... LEXICONM]
|SCRIPT| --printlatestversion MODE [OUTFILE]
|SCRIPT| --exportlatestversion MODE [OUTFILE]
|SCRIPT| --version
    Prints the version and exits.
"""

def print_usage(script_name):
    print(usage.replace('|SCRIPT|', script_name))


def cli_main(argc, argv):
    if argc < 2:
        print('No argument given!')
        print_usage(argv[0])
        sys.exit(2)

    if argv[1] == '--create_metadata':
        outpath = 'config/fieldmappings.json'
        metadata.print_all(outpath)

    elif argv[1] == '--create_mode':
        mode = argv[2]
        suffix = argv[3]
        upload.create_mode(mode, suffix)
        print('Upload successful')

    elif argv[1] == '--create_empty_index':
        mode = argv[2]
        suffix = argv[3]
        upload.create_empty_index(mode, suffix)
        print('Index created successfully')

    elif argv[1] == '--import_mode':
        mode = argv[2]
        suffix = argv[3]
        upload.create_mode(mode, suffix, with_id=True)
        print('Upload successful')

    elif argv[1] == '--publish_mode':
        group = argv[2]
        suffix = argv[3]
        upload.publish_group(group, suffix)
        print('Upload successful')

    elif argv[1] == '--reindex_alias':
        print('reindex')
        index = argv[2]
        target_suffix = argv[3]
        upload.reindex_alias(index, target_suffix)

    elif argv[1] == '--getmapping':
        alias = argv[2]
        outfile = argv[3]
        gm.getmapping(alias, outfile)

    elif argv[1] == '--internalize_lexicon':
        # adds a lexicon to sql from es
        # can be done at any time, not noticable
        # to the end user
        mode = argv[2]
        to_upload = argv[3:]
        upload.internalize_lexicon(mode, to_upload)
        print('Upload successful')

    elif argv[1] == '--printlatestversion':
        lexicon = argv[2]
        filename = None
        if argc == 4:
            filename = argv[3]
        if filename:
            with open(filename, 'w') as fp:
                upload.printlatestversion(lexicon, file=fp)
        else:
            upload.printlatestversion(lexicon)

    elif argv[1] == '--exportlatestversion':
        lexicon = argv[2]
        filename = None
        if argc == 4:
            filename = argv[3]
        if filename:
            with open(filename, 'w') as fp:
                upload.printlatestversion(lexicon, debug=False, with_id=True, file=fp)
        else:
            upload.printlatestversion(lexicon, debug=False, with_id=True)

    elif argv[1] == '--version':
        print('{}, version {}'.format(argv[0], karp_backend.get_version()))
    # Commented since dangerous!
    # if argv[1] == '--delete_all':
    #    upload.delete_all()
    #    print('Deletion successful')
    #
    #
    # # Commented since dangerous!
    # if argv[1] == '--delete_mode':
    #    mode = argv[2]
    #    upload.delete_mode(mode)
    #    print('Deletion successful')

    else:
        print_usage(argv[0])