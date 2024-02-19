# Surplas Unit Allocation
This problem can be formulated as a classic newsvendor problem with a few additional rules such as surplus capacity and some products can be substituted for one another. If you produce more than you need, you incur extra cost, but if you order less than you need, you lose profit. 

## Required Packages
argparse, numpy, scipy.stats, pandas, gurobi

## Instructon to Run the Stochastic Model

cd path/to/surplus/Allacotion/Folder

Three input need to run the model;

	Number of scenario for random demand generation, default is 1000.
	Macro target percentage parameter from 0.1 to 0.5 recommended.
	Run an existing LP file, due to github file size limit, LP file is not shared in Output folder.
	
python src/main.py --num_scenario=1000 --macro_target_percentage=0.1 --rerun_existing_model=False


## Solution Files
Once model is successfully completed, an excel file for solution will be genrated containing two sheets.

	Sheet: "Production Amount" reports regular production amount for each product.
	Sheet: "Production Amount Transition" reports surplus production amount from each product to another product.



