#Active Calibration
Once a model has been created with X free parameters it is time to perform an active calibration.

An active calibration consists of the following steps
1. Transfer PT calibration sequence to the PT
1. Start the CSV recorder
1. Execute the calibration script on the PT. 
1. At this point there is a CSV file containing data of the actual PT behaviour.
And the data is stored for future usage.
And the data is tagged in the traceability database.
1. Run the model calibration in order to obtain the values of the parameters.
1. Tag these parameter values in the traceability database.

All of these actions are stubbed in active_calibration.py

Expected parameters that can be derrived from the results are:

- G_box: Energy transferred from the room to the box. (Unit: JK^-1)
- G_heater: Energy transferred from the heatbed to the air. (Unit: JK^-1)
- C_air: Heat capacity of air inside the box * mass of air inside the box. (Unit: JK^-1)
- C_heater: Heat capacity of the heater * volume of the heater. (Unit: JK^-1)