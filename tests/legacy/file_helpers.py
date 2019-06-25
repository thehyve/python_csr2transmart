import csv
import gzip
import shutil


def create_tsv_file(file, table):
    with open(file, 'w') as tsvfile:
        writer = csv.writer(tsvfile, delimiter='\t')
        for row in table:
            writer.writerow(row)


def read_tsv_file(file):
    table = []
    with open(file, 'r') as tsvfile:
        reader = csv.reader(tsvfile, delimiter='\t')
        for row in reader:
            table.append(row)
    return table


def gz_file(file):
    result_file = file + '.gz'
    with open(file, 'rb') as f_in, gzip.open(result_file, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)
