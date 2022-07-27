{   I modified the files:
    - "Microgird"
    - "MicrogridGenerator"

    The original copies are suffixed as Unmodified
     I modified:
     _generate_disaster_grid_profile
     _generate_weak_grid_profile
     _get_grid
     _create_microgrid

     in the MicrogridGenerator.py file    } 5/19/2022


{    Base algo Script is up, I stated on the microgrid class 
     The comments there should explain everything    } 5/26/2022

Storage Module Functionality:

Stores and checks contraints on the values of microgrid-scale storage devices:
    - Lithium Ion Cell Batteries
    - Vanadium Ion Flow Batteries
    - Flywheel Energy Storage

Due to implimentaton on a second-timscale, the horizon limits within the simulator where changed to account for large data sizes.

This module contains two classes: Storage, and StorageSuite, along with some functions from parsing strings into mathematical functions

Storage:
    This class is used to apply the correct behavior to the appropriate storage types 
    
StorageSuite:
    This class is used to aggregate all storage objects and opperates on them, and to manage data flow to and from the module
    

