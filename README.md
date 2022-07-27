# Storage.py

Module contains all logic for simulating custom microgrid-scale energy devices
Customizityion can be done by modifying the data.csv files

## Usage
### Initialzitation
The module requires the path of the storage device data file to function
All storage devices will be objects of the Storage class and stored in the StorageSuite.storage_suite dict
```Python
from Storage import StorageSuite
#### Add your path here
path = r''
####
storage_suite = StorageSuite(filename = path, load = 1E6)
```
### Charge function
This is one of the main ways to interact with the storage devices
The charge function returns the ammount of energy that was actually stored as a float
#### Example of charging all storage devices
```Python
for device in StorageSuite.storage_dict:
  StorageSuite.charge(stor_type = device, energy_sent = 1E3)
```
### Discharge function
This is one of the main ways to interact with the storage devices
The charge function returns the ammount of energy that was actually expended as a float
#### Example of discharging all storage devices
```Python
for device in StorageSuite.storage_dict:
  StorageSuite.discharge(stor_type = device, energy_requested = 1E3)
```
## License
MIT
