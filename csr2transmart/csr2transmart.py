import click
from csr2transmart.transmart_transformation import transform


@click.command()
@click.argument('input_dir')
@click.argument('output_dir')
@click.argument('config_dir')
@click.version_option()
def csr2transmart(input_dir, output_dir, config_dir):
    transform(
        input_dir,
        output_dir,
        config_dir,
        'CSR',
        '\\Central Subject Registry\\',
    )


def main():
    csr2transmart()


if __name__ == '__main__':
    main()
