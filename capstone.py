# import relevant libraries
import numpy as np
import matplotlib.pyplot as plt
import os.path
import pandas as pd
from astroquery.splatalogue import Splatalogue  # We must acknowledge authors for use of this library
from astropy import units as u


# Load in the data if it exists
if os.path.isfile('./Data/all_molecules.csv'):
    print("\n --- Loading in data ---\n")
    all_molecules = pd.read_csv('./Data/all_molecules.csv', header = 0, index_col = 0).to_dict(orient = "index")
else:
    # read in the data
    print("\n --- Reading in data ---\n")
    filenames = ["./Data/Win0.clean1.contsub_Jy.rest.scom.c.txt",
                 "./Data/Win1.clean1.contsub_Jy.rest.scom.c.txt",
                 "./Data/Win2.clean1.contsub_Jy.rest.scom.c.txt",
                 "./Data/Win3.clean1.contsub_Jy.rest.scom.c.txt"]
    # 'data' will be a 4 element list, with each element representing the data from 1 text file
    data = [np.loadtxt(f) for f in filenames]

    show_plot = False

    def create_plot():
        """ Recreate the plot from Cordiner et. al. 2015, Figure 1 """
        # Defining the figure might need more finess if there are more than 4 datasets
        # We need to consult a domain expert to learn if ALMA data always comes back with 4 datasets
        fig, axs = plt.subplots(2, 2, figsize = (10, 6))
        for index, ax in enumerate(axs.flat):
            # Plot each data set
            ax.plot(data[index][:,0],
                    data[index][:,1],
                    linewidth = 0.25)
            ax.set(ylabel = "Flux (Jy)")
            ax.set(xlabel = "Frequency (GHz)")
            # Clean up the xticks
            ax.set_xticks(np.arange(round(data[index][0,0], 1), round(data[index][-1,0], 1), step = 0.5))
            # Remove the space from the borders of the plot along the X axis
            ax.autoscale(enable = True, axis = 'x', tight = True)
        # Add some space between the plots
        plt.subplots_adjust(hspace = .3, wspace = .3)
        return fig, axs

    # Add lines to the plot where molecules were found
    def add_lines(id, molecules):
        """This function will add dashed lines to the plot where molecules were detected"""
        for freq in molecules.keys():
            axs[id].axvline(x = float(freq),
                            ymin = 0,
                            ymax = 1,
                            dashes = [18, 6],
                            linewidth = 0.25,
                            color = "gray",
                            alpha = 0.5)

    # Find the frequencies at which molecule flux is significant
    def find_molecules():
        """ Classify the molecules from their frequency for each dataset """
        for id, dataset in enumerate(data):
            # Locate the indices where the flux is greater than 3 standard deviations
            # There are 4 datasets.  Column 0 is the frequency, column 1 is the flux
            # Splatalogue appears to be accurate up to 5 decimal places
            molecules = {}  # An empty dictionary to store the results of each detected molecule and rest frequency
            delta = 0.00005 # +/- when searching frequencies
            frequencies = np.round(dataset[np.where( dataset[:, 1] >= 3 * np.std(dataset[:, 1])), 0], 5)[0]
            for freq in frequencies:
                results = Splatalogue.query_lines( (freq - delta)*u.GHz, (freq + delta)*u.GHz,
                                                    show_molecule_tag = True,
                                                    top20 = 'planet')
                # Append the chemical names corresponding to the searched frequency.
                if len(results) > 0:
                    molecules[freq] = {"Chemical Name": results["Chemical Name"].tolist(),
                                       "Molecule Tag": results["Molecule<br>Tag"].tolist()}
                else:
                    molecules[freq] = {"Chemical Name": "Unknown",
                                       "Molecule Tag": None}

                # Append the chemical name and frequency to the dictionary of all molecules found
                if len(results) > 0:
                    for i, molecule in enumerate(results["Chemical Name"].tolist()):
                        if molecule in all_molecules.keys():
                            all_molecules[molecule]["Occurances"].append(freq)
                        else:
                            all_molecules[molecule] = {"Occurances": [freq],
                                                       "Molecule Tag": results["Molecule<br>Tag"][i],
                                                       "Linelist": results["Linelist"][i]}
                else:
                    if "Unknown" in all_molecules.keys():
                        all_molecules["Unknown"]["Occurances"].append(freq)
                    else:
                        all_molecules["Unknown"] = {"Occurances": [freq],
                                                    "Molecule Tag": None,
                                                    "Linelist": None}
            add_lines(id, molecules)

    # Run it all
    fig, axs = create_plot()
    axs = axs.flat
    all_molecules = {}  # This will store the molecule name and every frequency it is found at
    find_molecules()
    # Save the all_molecules dictionary for faster run time
    pd.DataFrame.from_dict(all_molecules,
                           columns = ["Occurances",
                                      "Molecule Tag",
                                      "Linelist"],
                           orient = "index").to_csv("./Data/all_molecules.csv")

# Test that everything worked
for molecule in all_molecules.keys():
    print(molecule, ": ", all_molecules[molecule])
plt.show()
