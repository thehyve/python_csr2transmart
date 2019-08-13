import click

from sources2csr.csr_transformations import csr_transformation


@click.command()
@click.argument('input_path')
@click.argument('output_dir')
@click.argument('config_dir')
@click.version_option()
def sources2csr(input_path, output_dir, config_dir):
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


def main():
    sources2csr()


if __name__ == '__main__':
    main()
