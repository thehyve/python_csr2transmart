import logging
import sys

import click

from csr.logging import setup_logging
from csr.subject_registry_writer import SubjectRegistryWriter

from csr.study_registry_writer import StudyRegistryWriter
from sources2csr.derived_values import add_derived_values
from sources2csr.ngs2csr import add_ngs_data
from sources2csr.sources_reader import SourcesReader


logger = logging.getLogger(__name__)


def sources2csr(input_dir, output_dir, config_dir):
    logger.info('sources2csr')
    try:
        reader = SourcesReader(input_dir=input_dir, config_dir=config_dir)
        subject_registry = reader.read_subject_data()
        add_derived_values(subject_registry)
        add_ngs_data(subject_registry, input_dir)
        subject_registry_writer = SubjectRegistryWriter(output_dir)
        subject_registry_writer.write(subject_registry)

        study_registry = reader.read_study_data()
        study_registry_writer = StudyRegistryWriter(output_dir)
        study_registry_writer.write(study_registry)
    except Exception as e:
        logger.error(e)
        sys.exit(1)


@click.command()
@click.argument('input_dir', type=click.Path(file_okay=False, exists=True, readable=True))
@click.argument('output_dir', type=click.Path(file_okay=False, writable=True))
@click.argument('config_dir', type=click.Path(file_okay=False, exists=True, readable=True))
@click.option('--debug', is_flag=True, help='Print more verbose messages')
@click.version_option()
def run(input_dir, output_dir, config_dir, debug: bool):
    setup_logging(debug)
    sources2csr(input_dir, output_dir, config_dir)


def main():
    run()


if __name__ == '__main__':
    main()
