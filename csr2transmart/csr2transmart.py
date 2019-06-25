from os import path, listdir

import click
from csr2transmart.transmart_transformation import transform

from csr2transmart.csr_transformations import csr_transformation


@click.command()
@click.argument('input_path')
@click.argument('output_dir')
@click.argument('config_dir')
def csr2transmart(input_path, output_dir, config_dir):
    csr_transformation(
        input_path,
        output_dir,
        config_dir,
        'data_model.json',
        'column_priority.json',
        'file_headers.json',
        'columns_to_csr.json',
        'csr_transformation_data.tsv',
        'study_registry.tsv',
    )
    transform(
        path.join(output_dir, 'csr_transformation_data.tsv'),
        path.join(output_dir, 'study_registry.tsv'),
        output_dir,
        config_dir,
        'blueprint.json',
        'modifiers.txt',
        'CSR',
        '\\Public Studies\\CSR\\',
        False,
        None
    )


def main():
    csr2transmart()


if __name__ == '__main__':
    main()
