type: type of energy storage
max_charge: maximum charge as a proportion of device capacity, between 0 and 1
min_charge: minimum charge as a proportion of device capacity, between 0 and 1
max_discharge: maximum discharge rate per second as a proportion of device capacity, between 0 and 1 or UNDEF
min_charge: minimum charge as a proportion of device capacity, between 0 and 1 or UNDEF
eff_charge: charging efficiency, between 0 and 1 (equal to sqrt(roundtrip efficiency))
eff_discharge: discharging efficiency, between 0 and 1 (equal to sqrt(roundtrip effiency))
self_discharge: loss rate of charge when standing by as a proportion of current charge, between 0 and 1
capital_cost: initial cost of device per kWh
marginal_cost: cost of device per kWh charged or discharged
ramp_speed: maximum rate of change of power (per second) as a proportion of device capacity, between 0 and 1
resp_time: time between dispatch command and realization of energy from device