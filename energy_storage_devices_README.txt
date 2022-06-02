type: type of energy storage
max_charge: maximum charge as a proportion of device capacity, between 0 and 1
min_charge: minimum charge as a proportion of device capacity, between 0 and 1
max_discharge: maximum discharge rate per second as a proportion of device capacity, between 0 and 1 or UNDEF
min_charge: minimum charge as a proportion of device capacity, between 0 and 1 or UNDEF
eff_charge: charging efficiency, between 0 and 1 (equal to sqrt(roundtrip efficiency))
eff_discharge: discharging efficiency, between 0 and 1 (equal to sqrt(roundtrip effiency))
self_discharge: loss rate of charge when standing by as a proportion of current charge, a function of x
capital_cost: initial cost of device per kWh
marginal_cost: cost of device per kWh charged or discharged
ramp_speed: maximum rate of change of power (per second) as a proportion of device capacity, between 0 and 1
resp_time: time between dispatch command and realization of energy from device
usable_start: the start of the time window the device can be used, an int between 0 and 23 representing hour (applicable to V2G)
usable_end: the end of the time window the device can be used, an int between 0 and 23 representing hour (applicable to V2G)

**Should add normal lifetime quality deterioriation as part of marginal cost, cost per second, (or maybe separate field)