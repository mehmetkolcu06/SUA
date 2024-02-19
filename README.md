# Surplas Unit Allocation

This problem can be formulated as a classic newsvendor problem with a few additional rules such as surplus capacity and some products can be substituted for one another. If you produce more than you need, you incur extra cost, but if you order less than you need, you lose profit. 

## Required Packages

argparse, numpy, scipy.stats, pandas, gurobi

## Instructon to Run the Stochastic Model

Three input need to run the model;

	Number of scenario for random demand generation, default is 1000.
	Macro target percentage parameter from 0.1 to 0.5 recommended.
	Run an existing LP file, due to github file size limit, LP file is not shared in Output folder.

cd "path/to/surplus/Allacotion/Folder"
	
python src/main.py --num_scenario=1000 --macro_target_percentage=0.1 --rerun_existing_model=False


## Solution Files

Once model is successfully completed, an excel file for solution will be genrated containing two sheets.

	Sheet: "Production Amount" reports regular production amount for each product.
	Sheet: "Production Amount Transition" reports surplus production amount from each product to another product.

Two sample solution files are provided for two extreme macro_target_percentage value which are 0.1 and 0.5 using 1000 randomly enerated demand for each product.

## Problem Formulation

Pdf file named ProblemFormulation-SUA in "Surplus_Allocation/Docs" folder shows the problem formulation.


## Observations

If Macro target percentage parameter increases, model become more flexabile and products with low costs substituted more for another product in the same group.
This model allows to decide regular production amount for each product, and due to nature of Burr 12 distribution, Demand has high variation, that is why substituon amount is low for each product.
If we set regular production amount for each product as predicted demand, and optimize surplus amount, mstly model becomes infeasible. since demand has high variation, and limited surplus capacity, these two constraint conflict and model become infeasible.

## Assumptions

This model does not consider any penalty model when a product substituted for another. However, a logic can be implemeted in the cost function by adding a penalty option.




