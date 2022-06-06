import csv

class StorageSuite:
    def __init__(self, filename):
        self.storage_suite = []
        self.device_data = {}
        with open(filename, newline='', encoding='utf-8-sig') as devices_file:
            reader = csv.DictReader(devices_file)
            for row in reader:
                self.device_data[row['type']] = row
        for device in self.device_data:
            self.storage_suite[device] = Storage(type=device)

class Storage:
    def __init__(self, ss, type, cap, power, s_wind, e_wind):
        self.type = type
        self.cap = cap
        self.power = power
        self.s_wind = s_wind
        self.e_wind = e_wind
        if ss.device_data['cap_power_ind']:
            pass
        else:
            self.capital_cost = ss.device_data['capital_cost'] * self.power
        self.max_soc = ss.device_data['max_charge']
        self.min_soc = ss.device_data['min_charge']
        self.max_charge_rate = ss.device_data['max_charge_rate']
        self.min_charge_rate = ss.device_data['min_charge_rate']
        self.max_cont_discharge = ss.device_data['max_cont_discharge']
        self.max_peak_discharge = ss.device_data['max_peak_discharge']
        self.min_discharge = ss.device_data['min_discharge']
        self.eff_charge = ss.device_data['eff_charge']
        self.self_discharge = ss.device_data['self_discharge']
        self.marginal_cost = ss.device_data['marginal_cost']
        self.ramp_speed = ss.device_data['ramp_speed']
        self.resp_time = ss.device_data['resp_time']
        self.soc = 0
        pass
    

if __name__ == "__main__":
    test_ss = StorageSuite('energy_storage_devices_v2.csv')
    print(test_ss.device_data['flywheel']['capital_cost'])



#do we need to include response time of aggregator?
#maybe we can have aggegator control as a boolean
#or even separate suites for each?