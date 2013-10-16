import utils.python
from utils.python.cosmic_db import get_cosmic_db
from utils.python.amino_acid import AminoAcid
import plot_data
import pandas as pd
import csv
import logging


def count_mutations(cursor):
    """Count the number of entries"""
    cursor.execute("""SELECT COUNT(COSMICSampleID)
                   FROM `nucleotide`""")
    return cursor.fetchone()[0]  # COUNT query returns a tuple


def count_aa_missense_changes(cursor):
    """Count amino acid changes.

    Args:
        cursor: mysqldb cursor object

    Returns:
        dict. containing counts eg. {('aa1', 'aa2'): 4}
    """
    logger = logging.getLogger(name=__name__)
    logger.info('Starting to count amino acid changes . . .')
    cursor.execute("""SELECT aachange, occurrences
                   FROM `cosmic_aa`""")
    aa_change_counter = {}
    for aachange, occurrences in cursor.fetchall():
        aa = AminoAcid(hgvs=aachange,
                       occurrence=occurrences)
        if aa.is_valid and not aa.is_missing_info:
            aa_change_counter.setdefault((aa.initial, aa.mutated), 0)
            aa_change_counter[(aa.initial, aa.mutated)] += aa.occurrence
    logger.info('Finished counting amino acid changes.')
    return aa_change_counter


def save_aa_missense_counts(aacounter):
    """Saves missense mutation counts to file.

    """
    # save missense mutation counts into a file
    file_path = 'data_analysis/results/aa_change.missense.txt'  # save file
    header = [['initial', 'mutated', 'count']]
    aa_list = sorted([[key[0], key[1], val]
                      for key, val in aacounter.iteritems() if "*" not in key])
    csv.writer(open(file_path, 'wb'),
               delimiter='\t').writerows(header + aa_list)

    # re-slice the mutation data
    new_file_path = 'data_analysis/results/aa_change.properties.txt'
    df = pd.read_csv(file_path, sep='\t')
    # add properties of initial/mutated amino acids
    df['initial_prop'] = df['initial'].apply(lambda x: utils.python.letter_to_prop[x])
    df['mutated_prop'] = df['mutated'].apply(lambda x: utils.python.letter_to_prop[x])
    ptable = pd.pivot_table(df,
                            values='count',
                            rows='initial_prop',
                            cols='mutated_prop',
                            aggfunc=sum)
    ptable.to_csv(new_file_path, sep='\t')


def main():
    conn = get_cosmic_db()
    cursor = conn.cursor()

    # handle missense mutation data
    aa_counter = count_aa_missense_changes(cursor)
    save_aa_missense_counts(aa_counter)
    plot_data.plot_aa_missense_heatmap()
    plot_data.plot_aa_property_heatmap()
    plot_data.plot_aa_property_barplot()

    conn.close()

if __name__=="__main__":
    main()
