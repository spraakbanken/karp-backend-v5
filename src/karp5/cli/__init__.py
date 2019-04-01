import logging
import logging.handlers
import os
import sys

import click

import karp5
from karp5.cli import create_metadata as metadata
from karp5.cli import upload_offline as upload
from karp5.cli import getmapping as gm


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


def create_cli(config = karp5.Config):
    logger = logging.getLogger('karp5')
    logger.setLevel(config.LOG_LEVEL)
    formatter = logging.Formatter(
        fmt = config.LOG_FMT,
        datefmt = config.LOG_DATEFMT
    )

    if config.TESTING or config.DEBUG or config.LOG_TO_STDERR:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(config.LOG_LEVEL)
        logger.addHandler(stream_handler)
    else:
        log_dir = config.LOG_DIR
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)

        file_handler = logging.handlers.TimedRotatingFileHandler(
            os.path.join(log_dir, 'karp5-admin.log'),
            when='d',
            interval=1,
            backupCount=0
        )
        file_handler.setLevel(config.LOG_LEVEL)
        logger.addHandler(file_handler)

    @click.group()
    @click.version_option(
        karp5.get_version(),
        prog_name='karp5'
    )
    def cli():
        pass

    register_commands(cli)

    return cli


def register_commands(cli):
    @cli.command(
        'create_metadata',
        short_help='Generate fieldmappings.'
    )
    def create_metadata():
        """Generate 'config/fieldmappings.json' from the 'config/mappings/fieldmappings_*.json' files."""
        outpath = 'config/fieldmappings.json'
        metadata.print_all(outpath)

    @cli.command('create_mode')
	@click.argument('mode')
	@click.argument('suffix')
	def create_mode(mode, suffix):
        upload.create_mode(mode, suffix)
        print('Upload successful')

    @cli.command('create_empty_index')
    @click.argument('mode')
    @click.argument('suffix')
    def create_empty_index(mode, suffix):
        upload.create_empty_index(mode, suffix)
        print('Index created successfully')

    @cli.command('import_mode')
	@click.argument('mode')
	@click.argument('suffix')
	def import_mode(mode, suffix):
        upload.create_mode(mode, suffix, with_id=True)
        print('Upload successful')

    @cli.command('publish_mode')
	@click.argument('group')
	@click.argument('suffix')
	def publish_mode(group, suffix):
        upload.publish_group(group, suffix)
        print('Upload successful')

    @cli.command('reindex_alias')
	@click.argument('print')
	@click.argument('index')
	def reindex_alias(print, index):
        target_suffix = argv[3]
        upload.reindex_alias(index, target_suffix)

    @cli.command('getmapping')
	@click.argument('alias')
	@click.argument('outfile')
	def getmapping(alias, outfile):
        gm.getmapping(alias, outfile)

    @cli.command('internalize_lexicon')
	@click.argument('mode', nargs=1)
	@click.argument('to_upload', nargs=-1)
	def internalize_lexicon(mode, to_upload):
        """ Add a lexicon to sql from es.
        Can be done at any time, not noticable to the end user.
        """

        upload.internalize_lexicon(mode, to_upload)
        print('Upload successful')

    @cli.command('printlatestversion')
	@click.argument('lexicon')
	@click.option('filename', default=None)
	def printlatestversion(lexicon, filename):
        if argc == 4:
            filename = argv[3]
        if filename:
            with open(filename, 'w') as fp:
                upload.printlatestversion(lexicon, file=fp)
        else:
            upload.printlatestversion(lexicon)

    @cli.command('exportlatestversion')
	@click.argument('lexicon')
	@click.option('filename', default=None)
	def exportlatestversion(lexicon, filename):
        if argc == 4:
            filename = argv[3]
        if filename:
            with open(filename, 'w') as fp:
                upload.printlatestversion(lexicon, debug=False, with_id=True, file=fp)
        else:
            upload.printlatestversion(lexicon, debug=False, with_id=True)


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
        print('{}, version {}'.format(argv[0], karp5.get_version()))
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

    if config.TESTING or config.DEBUG or config.LOG_TO_STDERR:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(config.LOG_LEVEL)
        logger.addHandler(stream_handler)
    else:
        log_dir = config.LOG_DIR
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)

        file_handler = logging.handlers.TimedRotatingFileHandler(
            os.path.join(log_dir, 'karp5-admin.log'),
            when='d',
            interval=1,
            backupCount=0
        )
        file_handler.setLevel(config.LOG_LEVEL)
        logger.addHandler(file_handler)

@click.group()
@click.version_option(
    karp5.get_version(),
    prog_name='karp5'
)
def cli():
    setup_cli()

    # return cli


# def register_commands(cli):
@cli.command(
    'create_metadata',
    short_help='Generate fieldmappings.'
)
def create_metadata():
    """Generate 'config/fieldmappings.json' from the 'config/mappings/fieldmappings_*.json' files."""
    outpath = 'config/fieldmappings.json'
    metadata.print_all(outpath)

@cli.command('create_mode')
@click.argument('mode')
@click.argument('suffix')
def create_mode(mode, suffix):
    upload.create_mode(mode, suffix)
    print('Upload successful')

@cli.command('create_empty_index')
@click.argument('mode')
@click.argument('suffix')
def create_empty_index(mode, suffix):
    upload.create_empty_index(mode, suffix)
    print('Index created successfully')

@cli.command('import_mode')
@click.argument('mode')
@click.argument('suffix')
def import_mode(mode, suffix):
    upload.create_mode(mode, suffix, with_id=True)
    print('Upload successful')

@cli.command('publish_mode')
@click.argument('group')
@click.argument('suffix')
def publish_mode(group, suffix):
    upload.publish_group(group, suffix)
    print('Upload successful')

@cli.command('reindex_alias')
@click.argument('index')
@click.argument('target_suffix')
def reindex_alias(index, target_suffix):
    # target_suffix = argv[3]
    upload.reindex_alias(index, target_suffix)

@cli.command('getmapping')
@click.argument('alias')
@click.argument('outfile')
def getmapping(alias, outfile):
    gm.getmapping(alias, outfile)

@cli.command('internalize_lexicon')
@click.argument('mode', nargs=1)
@click.argument('to_upload', nargs=-1)
def internalize_lexicon(mode, to_upload):
    """ Add a lexicon to sql from es.
    Can be done at any time, not noticable to the end user.
    """

    upload.internalize_lexicon(mode, to_upload)
    print('Upload successful')

@cli.command('printlatestversion')
@click.argument('lexicon', metavar='<lexicon>')
@click.option(
    '--output',
    '-o',
    default=None,
    metavar='<path>',
    help='File to write to.'
)
def printlatestversion(lexicon, output):
    if output:
        with open(output, 'w') as fp:
            upload.printlatestversion(lexicon, file=fp)
    else:
        upload.printlatestversion(lexicon)

@cli.command('exportlatestversion')
@click.argument('lexicon', metavar='<lexicon>')
@click.option(
    '--output',
    '-o',
    default=None,
    metavar='<path>',
    help='File to write to.'
)
def exportlatestversion(lexicon, output):
    if output:
        with open(output, 'w') as fp:
            upload.printlatestversion(lexicon, debug=False, with_id=True, file=fp)
    else:
        upload.printlatestversion(lexicon, debug=False, with_id=True)

# Commented since dangerous!
# @cli.command('delete_all')
# def delete_all():
#     """ Deletes all modes.
#     You need to confirm this 5 times before proceding.
#     """
#     print('WARNING: This command will delete all modes.')
#     print('You have to confirm this 5 times.')
#     for i in range(1,6):
#         click.confirm(
#             'Are you sure you want to delete ALL modes ({}/5)?'.format(i),
#             abort=True
#         )
#     upload.delete_all()
#     print('Deletion successful')


 # Commented since dangerous!
# @cli.command('delete_mode')
# @click.argument('mode')
# def delete_mode(mode):
#     click.confirm(
#         "Are you sure you want to delete the mode '{}'".format(mode),
#         abort=True
#     )
#     upload.delete_mode(mode)
#     print('Deletion successful')
