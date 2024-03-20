"""
Authors:
----------
Vishnu Balakrishnan - Consultant, MSC Software
Ben Thornton - Consultant, MSC Software

Usage:
---------
1. Open Adams View
2. Go to File>Import...
3. Change File Type to 'Adams View Python File (*.py)"
4. Select res_to_csv.py
"""

import os
import csv
from collections import OrderedDict
import Adams  # type: ignore
import PyQt4.QtGui  # type: ignore

TIME_STRING = 'TIME'


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
    selected_analysis_name = os.path.split(results_filename)[-1].replace('.res', '')

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
            filt_res_names = [res_name for res_name in ans.results if 'XFORM' not in res_name and TIME_STRING not in res_name]

            for res_name in filt_res_names:
                # For each result set, get the result set handle
                res = ans.results.get(res_name)
                for comp_name in res.keys():
                    # for each result component in the result set, get the result component handle
                    comp = res.get(comp_name)

                    if TIME_STRING in comp_name and not time_found:
                        # If this is the first time component encountered, add TIME to the data dictionary
                        data[TIME_STRING] = comp.values
                        time_found = True

                    elif TIME_STRING not in comp_name:
                        # If this is not a TIME component, add item to the data dictionary
                        # Key = (result set name), (result component name)
                        # Value = list of numeric data
                        data['{}.{}'.format(res_name, comp_name)] = comp.values

    if TIME_STRING in data:
        # If the data dictionary has a time key, move it to the front
        data.move_to_end(TIME_STRING, last=False)

    if output_filename is None:
        # If the output file is not given, set equal to the results file
        output_filename = results_filename.replace('.res', '.csv')

    # Write the data dictionary to a csv
    try:
        with open(output_filename, "w", newline='') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(data.keys())
            writer.writerows(zip(*data.values()))
    except PermissionError:
        message_box = PyQt4.QtGui.QMessageBox()
        message_box.setTitle('Permission Denied!')
        message_box.setText(f'Permission to access {output_filename} was denied!  Please close any programs that are using it and rerun this script.')
        message_box.setIcon(PyQt4.QtGui.QMessageBox.Warning)
        message_box.setStandardButtons(PyQt4.QtGui.QMessageBox.Ok)
        message_box.exec_()


def _get_filename_from_dialog(file_type):
    """Opens a dialog for user to select a file

    Arguments:
        file_type {str} -- Type of file ('res' or 'csv')

    Returns:
        str -- Filename of file selected by user.
    """

    if file_type == 'res':
        caption = 'Select a results file.'
        filter = 'Adams Results Files (*.res)'
        # Bring up a dialog for the user to select a results file
        filename = PyQt4.QtGui.QFileDialog.getOpenFileName(caption=caption, filter=filter)

    elif file_type == 'csv':
        caption = 'Select location to save the csv results file.'
        filter = 'CSV Files (*.csv)'
        # Bring up a dialog for the user to select a results file
        filename = PyQt4.QtGui.QFileDialog.getSaveFileName(caption=caption, filter=filter)

    return filename


if __name__ in ['aview_main', '__main__']:
    res_to_csv()
