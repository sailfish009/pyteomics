import os
from urllib import urlretrieve
# In python 3, use 'from urllib.request import urlretrieve' instead

import matplotlib.pyplot as plt
import numpy as np
from pyteomics import fasta, parser, mass, achrom, electrochem, auxiliary

import shelve

if not os.path.isfile('./yeast.fasta'):
    print 'Download the FASTA file for Saccharomyces cerevisiae...'
    schema_file = urlretrieve(
        'http://www.uniprot.org/uniprot/?query=organism%3a559292+keyword%3a1185&format=fasta',
        './yeast.fasta')
    print 'Done!'

print 'Cleave the proteins with Lys-C...'
unique_peptides = set()
for description, sequence in fasta.read_fasta('./yeast.fasta'):
    new_peptides = parser.cleave(sequence, parser.expasy_rules['trypsin'])
    unique_peptides = set.union(unique_peptides, new_peptides)
peptides = [{'sequence': i} for i in unique_peptides if len(i) <= 100]

print 'Done, {0} sequences obtained!'.format(len(peptides))

print 'Parse peptide sequences...'
for peptide in peptides:
    peptide['parsed_sequence'] = parser.parse_sequence(
        peptide['sequence'],
        show_unmodified_termini=True)
    peptide['length'] = len(peptide['parsed_sequence']) - 2 
print 'Done!'

peptides = [peptide for peptide in peptides if peptide['length'] <= 200]

print 'Calculate the mass, charge and m/z...'
for peptide in peptides:
    peptide['mass'] = mass.calculate_mass(peptide['parsed_sequence'])
    peptide['charge'] = int(round(electrochem.charge(peptide['parsed_sequence'], 2.0)))
    peptide['m/z'] = mass.calculate_mass(peptide['parsed_sequence'], 
        charge=peptide['charge'])
print 'Done!'

print 'Calculate the retention time...'
for peptide in peptides:
    peptide['RT_RP'] = achrom.calculate_RT(
        peptide['parsed_sequence'],
        achrom.RCs_zubarev)
    peptide['RT_normal'] = achrom.calculate_RT(
        peptide['parsed_sequence'],
        achrom.RCs_yoshida_lc)
print 'Done!'

plt.figure()
plt.hist([peptide['m/z'] for peptide in peptides],
plt.xlabel('m/z, Th')
plt.ylabel('# of peptides within 2 Th bin')
plt.show()

plt.figure()
plt.hist([peptide['charge'] for peptide in peptides],
    bins = 40,
    range=(0,20))
plt.xlabel('charge, e')
plt.ylabel('# of peptides')
plt.show()

x = [peptide['RT_RP'] for peptide in peptides]
y = [peptide['RT_normal'] for peptide in peptides]
a, b, r, stderr = auxiliary.linear_regression(x,y)
heatmap, xbins, ybins = np.histogram2d(x, y, bins=100)

plt.figure()
plt.imshow(
    heatmap, 
    extent=(xbins[0], xbins[-1], ybins[0], ybins[-1]),
    interpolation='none')
plt.xlabel('RT on RP, min')
plt.ylabel('RT on normal phase, min')
plt.title('All tryptic peptides, RT correlation = {0}'.format(r))
plt.show()

close_mass_peptides = [peptide for peptide in peptides 
                       if 700.0 <= peptide['m/z'] <= 701.0]
x = [peptide['RT_RP'] for peptide in close_mass_peptides]
y = [peptide['RT_normal'] for peptide in close_mass_peptides]
a, b, r, stderr = auxiliary.linear_regression(x,y)

plt.figure()
plt.scatter(x, y)
plt.xlabel('RT on RP, min')
plt.ylabel('RT on normal phase, min')
plt.title('Tryptic peptides with m/z=700-701 Th\nRT correlation = {0}'.format(r))
plt.show()
