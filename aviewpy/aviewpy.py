"""Python tools for working in the adams view python environment.

Authors:
----------
Vishnu Balakrishnan - Consultant, MSC Software
Ben Thornton - Consultant, MSC Software
"""

import Adams
import PyQt4.QtGui
import numpy as np
import os
import csv
from collections import OrderedDict

def res_to_csv(results_filename=None, output_filename=None):
    """Writes data in a results file selected by the user to a csv file.
    
    Arguments:
        results_filename {str} -- Path to an adams results file
    """
    
    if results_filename is None:
        results_filename = _get_filename_from_dialog('res')
        if not results_filename:
            print('You must select a .res file!')
    
    if output_filename is None:
        output_filename = _get_filename_from_dialog('csv')
        if not output_filename:
            print('You must select a .csv file for output!')

    # Run an aview cmd command to load the results file.
    aview_cmd = 'file results read file_name = "{}"'.format(os.path.normpath(results_filename).replace(os.sep, '/'))
    Adams.execute_cmd(aview_cmd)
    
    # Get the name of the analysis loaded by the results file
    selected_analysis_name = os.path.split(results_filename)[-1].replace('.res','')

    # Loop through all analyses in the model    
    data = OrderedDict()
    for mod_name in Adams.Models:
        mod = Adams.Models.get(mod_name)
        for ans_name in mod.Analyses:
            if ans_name not in selected_analysis_name:
                # If this analysis name doesn't match, break
                break
            
            # Initialize a flag indicating that the TIME array has not been set
            time_found = False
                
            # For each analysis in the model, get the analysis handle
            ans = mod.Analyses.get(ans_name)

            # Filtering out XFORM result sets
            filt_res_names = [res_name for res_name in ans.results if 'XFORM' not in res_name and 'TIME' not in res_name]
            
            for res_name in filt_res_names:
                # For each result set, get the result set handle
                res = ans.results.get(res_name)                    
                for comp_name in res.keys():
                    # for each result component in the result set, get the result component handle
                    comp = res.get(comp_name)

                    if 'TIME' in comp_name and not time_found:
                        # If this is the first time component encountered, add TIME to the data dictionary
                        data['TIME'] = comp.values

                    elif 'TIME' not in comp_name:
                        # If this is not a TIME component, add item to the data dictionary
                        # Key = (result set name), (result component name)
                        # Value = list of numeric data
                        data['{}.{}'.format(res_name, comp_name)] = comp.values

    if output_filename is None:
        # If the output file is not given, set equal to the results file
        output_filename = results_filename.replace('.res', '.csv')
    with open(output_filename, "w",newline = '') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(data.keys())
        writer.writerows(zip(*data.values()))

def _get_filename_from_dialog(file_type):
    if file_type is 'res':
        caption = 'Select a results file.'
        filter = 'Adams Results Files (*.res)'
        # Bring up a dialog for the user to select a results file
        filename = PyQt4.QtGui.QFileDialog.getOpenFileName(caption=caption, filter=filter)

    elif file_type is 'csv':
        caption='Select location to save the csv results file.'
        filter='CSV Files (*.csv)'
        # Bring up a dialog for the user to select a results file
        filename = PyQt4.QtGui.QFileDialog.getSaveFileName(caption=caption, filter=filter)       

    return filename

if __name__ == 'aview_main':
    res_to_csv()
