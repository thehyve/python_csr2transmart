from os import path

import click
from csr2transmart.transmart_transformation import transform


@click.command()
@click.argument('input_path')
@click.argument('output_dir')
@click.argument('config_dir')
@click.version_option()
def csr2transmart(input_path, output_dir, config_dir):
    transform(
        path.join(input_path, 'csr_transformation_data.tsv'),
        path.join(input_path, 'study_registry.tsv'),
        output_dir,
        config_dir,
        'CSR',
        '\\Central Subject Registry\\',
    )


def main():
    csr2transmart()


if __name__ == '__main__':
    main()
