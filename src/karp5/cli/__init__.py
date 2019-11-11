from __future__ import unicode_literals
import logging
import logging.handlers
import os

import click

import karp5
from karp5.cli import create_metadata as metadata
from karp5.cli import upload_offline as upload
from karp5.cli import getmapping as gm


_logger = logging.getLogger("karp5")


def setup_cli(config=karp5.Config):
    print("Setting up logging")
    karp5.conf_mgr.app_config = config
    logger = logging.getLogger("karp5")
    logger.setLevel(config.LOG_LEVEL)
    formatter = logging.Formatter(fmt=config.LOG_FMT, datefmt=config.LOG_DATEFMT)

    if config.TESTING or config.DEBUG or config.LOG_TO_STDERR:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(config.LOG_LEVEL)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
    else:
        log_dir = config.LOG_DIR
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)

        file_handler = logging.handlers.TimedRotatingFileHandler(
            os.path.join(log_dir, "karp5-admin.log"),
            when="d",
            interval=1,
            backupCount=0,
        )
        file_handler.setLevel(config.LOG_LEVEL)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.WARNING)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)


@click.group()
@click.version_option(karp5.get_version(), prog_name="karp5")
def cli():
    if not karp5.conf_mgr.app_config:
        setup_cli()


@cli.command("create_metadata", short_help="Generate fieldmappings.")
def create_metadata():
    """
    Generate 'config/fieldmappings.json'.

    Generate from the 'config/mappings/fieldmappings_*.json' files.
    NOTE: Not needed since version 5.9.0
    """
    outpath = "config/fieldmappings.json"
    metadata.print_all(outpath)


@cli.command("create_mode")
@click.argument("mode")
@click.argument("suffix")
def create_mode(mode, suffix):
    upload.create_mode(mode, suffix)
    print("Upload successful")


@cli.command("create_empty_index")
@click.argument("mode")
@click.argument("suffix")
def create_empty_index(mode, suffix):
    upload.create_empty_index(mode, suffix)
    print("Index created successfully")


@cli.command("import_mode")
@click.argument("mode")
@click.argument("suffix")
def import_mode(mode, suffix):
    upload.create_mode(mode, suffix, with_id=True)
    print("Upload successful")


@cli.command("publish_mode")
@click.argument("mode")
@click.argument("suffix")
def publish_mode(mode, suffix):
    """Publish MODE to all modes that contain MODE."""
    upload.publish_mode(mode, suffix)
    print(
        "Published '{mode}_{suffix}' successfully to '{mode}'".format(
            mode=mode, suffix=suffix
        )
    )


@cli.command("reindex_alias")
@click.argument("index")
@click.argument("target_suffix")
def reindex_alias(index, target_suffix):
    ret = upload.reindex_alias(index, target_suffix)
    if not ret:
        raise click.ClickException("Something went wrong")


@cli.command("getmapping")
@click.argument("alias")
@click.argument("outfile")
def getmapping(alias, outfile):
    gm.getmapping(alias, outfile)


@cli.command("internalize_lexicon")
@click.argument("mode", nargs=1)
@click.argument("to_upload", nargs=-1)
def internalize_lexicon(mode, to_upload):
    """ Add a lexicon to sql from es.
    Can be done at any time, not noticable to the end user.
    """

    upload.internalize_lexicon(mode, to_upload)
    print("Upload successful")


@cli.command("printlatestversion")
@click.argument("lexicon", metavar="<lexicon>")
@click.option(
    "--output", "-o", default=None, metavar="<path>", help="File to write to."
)
def printlatestversion(lexicon, output):
    if output:
        with open(output, "w") as fp:
            upload.printlatestversion(lexicon, file=fp)
    else:
        upload.printlatestversion(lexicon)


@cli.command("exportlatestversion")
@click.argument("lexicon", metavar="<lexicon>")
@click.option(
    "--output", "-o", default=None, metavar="<path>", help="File to write to."
)
def exportlatestversion(lexicon, output):
    if output:
        with open(output, "w") as fp:
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
