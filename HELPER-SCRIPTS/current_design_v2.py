import math
import json 
from typing import Dict ,Any

class CurrentMeasurementDesign:
    def __init__(self, vos, pin1, rmes, delta_ic1, kp, von_min, k=0.8, r=10, n_channels=4):
        """
        Initialize the current measurement design parameters with offset voltage constraint.
        
        Parameters:
        vos (float): Operational amplifier offset voltage (V)
        pin1 (float): Input precision for channel 1
        rmes (float): Shunt resistance (Ω)
        delta_ic1 (float): Base current range for channel 1 (A)
        kp (float): ADC voltage resolution (V/step)
        von_min (float): Minimum output voltage (V)
        k (float): Overlap constant (0 < k < 1)
        r (float): Range ratio for geometric scaling
        n_channels (int): Number of channels
        """
        self.vos = vos
        self.pin1 = pin1
        self.rmes = rmes
        self.delta_ic1 = delta_ic1
        self.kp = kp
        self.von_min = von_min
        self.k = k
        self.r = r
        self.n_channels = n_channels
        

        self.ic_min1 = vos / (pin1 * rmes)
      
        self.precision = kp / von_min
        self.accuracy = 1 - self.precision
        

        self.channels = {}
        self.gain_ratios = {}
    
    def design(self):
        """Calculate all channel parameters using the systematic algorithm."""
        
        ic_max1 = self.ic_min1 + self.delta_ic1
        kc1 = self.precision * self.ic_min1
        von_max1 = self.von_min * (ic_max1 / self.ic_min1)
        ad_rmes1 = self.von_min / self.ic_min1
        pin1 = self.vos / (self.ic_min1 * self.rmes)  
        
        self.channels[1] = {
            'ic_min': self.ic_min1,
            'ic_max': ic_max1,
            'delta_ic': self.delta_ic1,
            'kc': kc1,
            'von_min': self.von_min,
            'von_max': von_max1,
            'delta_von': von_max1 - self.von_min,
            'ad_rmes': ad_rmes1,
            'pin': pin1,
            'precision': self.precision,
            'accuracy': self.accuracy
        }
        
        prev_ic_max = ic_max1
        ad_rmes_prev= ad_rmes1
        for n in range(2, self.n_channels + 1):
  
            ic_min_n = self.k * prev_ic_max
            delta_ic_n = self.delta_ic1 * (self.r ** (n - 1))
            ic_max_n = ic_min_n + delta_ic_n
            
            kc_n = self.precision * ic_min_n
            von_max_n = self.von_min * (ic_max_n / ic_min_n)
            ad_rmes_n = self.von_min / ic_min_n
            pin_n = self.vos / (ic_min_n * self.rmes)
            
            self.channels[n] = {
                'ic_min': ic_min_n,
                'ic_max': ic_max_n,
                'delta_ic': delta_ic_n,
                'kc': kc_n,
                'von_min': self.von_min,
                'von_max': von_max_n,
                'delta_von': von_max_n - self.von_min,
                'ad_rmes': ad_rmes_n,
                'pin': pin_n,
                'precision': self.precision,
                'accuracy': self.accuracy
            }
            
     
            if n > 1:
                gain_ratio = ad_rmes_prev / ad_rmes_n 
                self.gain_ratios[n-1] = gain_ratio
            
            ad_rmes_prev = ad_rmes_n
            prev_ic_max = ic_max_n
    
    def verify_calculations(self):
        pass 

    
    def print_summary(self):
        """Print a formatted summary of the design."""
        print("=" * 80)
        print("CURRENT MEASUREMENT SYSTEM DESIGN SUMMARY")
        print("=" * 80)
        print(f"System Parameters:")
        print(f"  Offset voltage (V_os): {self.vos*1e6:.2f} μV")
        print(f"  Input precision Ch1 (P_in1): {self.pin1:.3f}")
        print(f"  Shunt resistance (R_mes): {self.rmes} Ω")
        print(f"  Output precision (P): {self.precision:.6f} ({self.precision*100:.4f}%)")
        print(f"  Accuracy: {self.accuracy*100:.4f}%")
        print(f"  Overlap constant (k): {self.k}")
        print(f"  Range ratio (r): {self.r}")
        print(f"  V_on_min: {self.von_min} V")
        print(f"  K_p: {self.kp} V/step")
        print()
        
        print("Channel Parameters:")
        print("-" * 100)
        print(f"{'Ch':<3} {'I_min (μA)':<12} {'I_max (μA)':<12} {'K_c (μA/step)':<15} {'V_max (V)':<10} {'A_d·R_mes':<12} {'P_in':<10} {'Gain Ratio':<12}")
        print("-" * 100)
        
        for n in range(1, self.n_channels + 1):
            ch = self.channels[n]
            gain_ratio = self.gain_ratios.get(n, "N/A")
            if gain_ratio != "N/A":
                gain_ratio_str = f"{gain_ratio:.3f}"
            else:
                gain_ratio_str = "N/A"
                
            print(f"{n:<3} {ch['ic_min']*1e6:<12.2f} {ch['ic_max']*1e6:<12.2f} "
                  f"{ch['kc']*1e6:<15.4f} {ch['von_max']:<10.3f} {ch['ad_rmes']:<12.1f} "
                  f"{ch['pin']:<10.3f} {gain_ratio_str:<12}")
    
    def get_total_range(self):
        """Get the total current range covered by the system."""
        first_ch = self.channels[1]
        last_ch = self.channels[self.n_channels]
        return first_ch['ic_min'], last_ch['ic_max']
    
    def get_channel_parameters(self, channel):
        """Get parameters for a specific channel."""
        return self.channels.get(channel, None)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the design to a dictionary for JSON serialization."""
        return {
            'metadata': {
                'vos': self.vos,
                'pin1': self.pin1,
                'rmes': self.rmes,
                'delta_ic1': self.delta_ic1,
                'kp': self.kp,
                'von_min': self.von_min,
                'k': self.k,
                'r': self.r,
                'n_channels': self.n_channels,
                'ic_min1': self.ic_min1,
                'precision': self.precision,
                'accuracy': self.accuracy
            },
            'channels': self.channels,
            'gain_ratios': self.gain_ratios
        }

    def default(self) -> str:
        """Serialize the design to JSON string or file."""
        data = self.to_dict()
        return json.dumps(data, indent=2, default=str)
        

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create a design instance from a dictionary."""
        metadata = data['metadata']
        design = cls(
            vos=metadata['vos'],
            pin1=metadata['pin1'],
            rmes=metadata['rmes'],
            delta_ic1=metadata['delta_ic1'],
            kp=metadata['kp'],
            von_min=metadata['von_min'],
            k=metadata['k'],
            r=metadata['r'],
            n_channels=metadata['n_channels']
        )
        
        # Restore calculated properties
        design.ic_min1 = metadata['ic_min1']
        design.precision = metadata['precision']
        design.accuracy = metadata['accuracy']
        design.channels = data['channels']
        design.gain_ratios = data['gain_ratios']
        
        return design

    @classmethod
    def from_json(cls, json_str: str = None, filepath: str = None):
        """Create a design instance from JSON string or file."""
        if filepath:
            with open(filepath, 'r') as f:
                data = json.load(f)
        else:
            data = json.loads(json_str)
        
        return cls.from_dict(data)


class DesignSweep:
    def __init__(self):
        self.designs = []
        self.sweep_results = {}
    
    def sweep_rmes(self, base_params, rmes_values):
        results = []
        for rmes in rmes_values:
            params = base_params.copy()
            params['rmes'] = rmes
            design = CurrentMeasurementDesign(**params)
            design.design()
            results.append({
                'rmes': rmes,
                'design': design.to_dict(),
                'ic_min1': design.ic_min1,
                'ad1': design.channels[1]['ad_rmes'] / rmes,
                'pin1': design.pin1,
                'dynamic_range': design.get_total_range()[1] / design.get_total_range()[0]
            })

        self.sweep_results['rmes_sweep'] = results
        return results
    
    def sweep_k(self, base_params, k_values):
        results = []
        for k in k_values:
            params = base_params.copy()
            params['k'] = k
            design = CurrentMeasurementDesign(**params)
            design.design()
            results.append({
                'k': k,
                'design': design.to_dict(),
                'max_voltage': max(ch['von_max'] for ch in design.channels.values()),
                'gain_range': design.channels[1]['ad_rmes'] / design.channels[design.n_channels]['ad_rmes']
            })
        self.sweep_results['overlap_sweep'] = results
        return results
    
    def sweep_r(self, base_params, r_values):
        results = []
        for r in r_values:
            params = base_params.copy()
            params['r'] = r
            design = CurrentMeasurementDesign(**params)
            design.design()
            min_current, max_current = design.get_total_range()
            results.append({
                'r': r,
                'dynamic_range': max_current / min_current,
                'max_gain': design.channels[1]['ad_rmes'] / params['rmes'],
                'channel_spacing': r
            })
        return results
    
    def sweep_pin1(self, base_params, pin1_values):
        results = []
        for pin1 in pin1_values:
            params = base_params.copy()
            params['pin1'] = pin1
            design = CurrentMeasurementDesign(**params)
            design.design()
            results.append({
                'pin1': pin1,
                'ic_min1': design.ic_min1,
                'ad1': design.channels[1]['ad_rmes'] / params['rmes'],
                'input_precision': pin1
            })
        return results
    
    def sweep_vos(self, base_params, vos_values):
        results = []
        for vos in vos_values:
            params = base_params.copy()
            params['vos'] = vos * 1e-6 
            design = CurrentMeasurementDesign(**params)
            design.design()
            results.append({
                'vos': vos,
                'ic_min1': design.ic_min1,
                'ad1': design.channels[1]['ad_rmes'] / params['rmes'],
                'min_current': design.ic_min1
            })
        return results
    
    def sweep_n_channels(self, base_params, n_values):
        results = []
        for n in n_values:
            params = base_params.copy()
            params['n_channels'] = n
            design = CurrentMeasurementDesign(**params)
            design.design()
            min_current, max_current = design.get_total_range()
            results.append({
                'n_channels': n,
                'dynamic_range': max_current / min_current,
                'max_voltage': max(ch['von_max'] for ch in design.channels.values()),
                'gain_range': design.channels[1]['ad_rmes'] / design.channels[n]['ad_rmes']
            })
        return results

