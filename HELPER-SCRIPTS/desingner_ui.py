import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import math
import json
import os
from datetime import datetime

from current_design_v2 import  CurrentMeasurementDesign ,DesignSweep
from ui_utils import get_n_channels_spec ,get_overlap_spec ,get_pin1_spec,get_r_spec,get_rmes_spec,get_vos_spec ,SweepPlotter


class ModernCurrentMeasurementUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Current Measurement System Designer")
        self.root.geometry("1600x1000")
        
        self.design_sweep :DesignSweep = DesignSweep()
        self.current_design = None
        self.sweep_results = {}
        
        self.fig_design = plt.Figure(figsize=(12, 8))
        self.fig_sweep = plt.Figure(figsize=(12, 8))
        self.fig_analysis = plt.Figure(figsize=(12, 8))
        
        self.init_ui()
        
        # Create data directory
        self.data_dir = "current_design_data"
        self.plotter = SweepPlotter()
        os.makedirs(self.data_dir, exist_ok=True)
    
    def init_ui(self):

        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)
    
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=3)
        
        self.create_input_panel(left_frame)
        self.create_results_panel(right_frame)
        
        main_paned.sashpos(0, 450)
    
    def create_input_panel(self, parent):
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # System Parameters
        sys_group = ttk.LabelFrame(scrollable_frame, text="System Parameters", padding="10")
        sys_group.pack(fill=tk.X, padx=5, pady=5)
        
        self.inputs = {}
        params = [
            ('vos', 'Offset Voltage (μV)', 50.0),
            ('pin1', 'Input Precision Ch1', 0.2),
            ('rmes', 'Shunt Resistance (Ω)', 0.1),
            ('delta_ic1', 'Base Range (mA)', 2.5),
            ('kp', 'ADC Resolution (V/step)', 0.0048828),
            ('von_min', 'Min Output Voltage (V)', 0.024414),
            ('k', 'Overlap Factor', 0.8),
            ('r', 'Range Ratio', 10.0),
            ('n_channels', 'Number of Channels', 4)
        ]
        
        for i, (key, label, default) in enumerate(params):
            frame = ttk.Frame(sys_group)
            frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(frame, text=label, width=20).pack(side=tk.LEFT)
            
            if key == 'n_channels':
                var = tk.IntVar(value=default)
                spinbox = ttk.Spinbox(frame, from_=2, to=20, textvariable=var, width=15)
            else:
                var = tk.DoubleVar(value=default)
                spinbox = ttk.Spinbox(frame, from_=0.001, to=1000, textvariable=var, width=15, format="%.6f")
            
            spinbox.pack(side=tk.LEFT, padx=5)
            self.inputs[key] = var
        
        # Control Buttons
        btn_frame = ttk.Frame(scrollable_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="Calculate Design", 
                  command=self.calculate_design).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Save Design", 
                  command=self.save_design).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Load Design", 
                  command=self.load_design).pack(side=tk.LEFT, padx=2)
        
        # Sweep Parameters
        self.create_sweep_panel(scrollable_frame)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_sweep_panel(self, parent):
        sweep_group = ttk.LabelFrame(parent, text="Parameter Sweep", padding="10")
        sweep_group.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(sweep_group, text="Sweep Parameter:").pack(anchor=tk.W)
        self.sweep_var = tk.StringVar(value="rmes")
        sweep_combo = ttk.Combobox(sweep_group, textvariable=self.sweep_var,
                                  values=["rmes", "k", "r", "pin1", "vos", "n_channels"])
        sweep_combo.pack(fill=tk.X, pady=2)
        
        sweep_frame = ttk.Frame(sweep_group)
        sweep_frame.pack(fill=tk.X, pady=5)
        
        self.sweep_inputs = {}
        sweep_params = [
            ('sweep_min', 'Min Value', 0.01),
            ('sweep_max', 'Max Value', 1.0),
            ('sweep_steps', 'Steps', 20)
        ]
        
        for key, label, default in sweep_params:
            frame = ttk.Frame(sweep_frame)
            frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(frame, text=label, width=15).pack(side=tk.LEFT)
            
            if key == 'sweep_steps':
                var = tk.IntVar(value=default)
                spinbox = ttk.Spinbox(frame, from_=5, to=100, textvariable=var, width=10)
            else:
                var = tk.DoubleVar(value=default)
                spinbox = ttk.Spinbox(frame, from_=0.001, to=1000, textvariable=var, width=10)
            
            spinbox.pack(side=tk.LEFT, padx=5)
            self.sweep_inputs[key] = var
        
        ttk.Button(sweep_group, text="Run Sweep", 
                  command=self.run_sweep).pack(pady=5)
    
    def create_results_panel(self, parent):
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        self.create_results_table_tab(notebook)
        
        self.create_summary_tab(notebook)
        
        self.create_design_plots_tab(notebook)
        
        self.create_sweep_plots_tab(notebook)
        
        self.create_analysis_tab(notebook)
    
    def create_results_table_tab(self, notebook):
        table_frame = ttk.Frame(notebook)
        notebook.add(table_frame, text="Channel Results")
        
        columns = ('Channel', 'I_min (μA)', 'I_max (μA)', 'K_c (μA/step)', 
                  'V_min (V)', 'V_max (V)', 'ΔV_on (V)', 'A_d·R_mes', 'P_in', 'Gain Ratio')
        self.results_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)
        
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=90, anchor=tk.CENTER)
        
        tree_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_summary_tab(self, notebook):
        summary_frame = ttk.Frame(notebook)
        notebook.add(summary_frame, text="Design Summary")
        
        self.summary_text = scrolledtext.ScrolledText(summary_frame, width=80, height=25)
        self.summary_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def create_design_plots_tab(self, notebook):
        plot_frame = ttk.Frame(notebook)
        notebook.add(plot_frame, text="Design Plots")
        
        self.canvas_design = FigureCanvasTkAgg(self.fig_design, master=plot_frame)
        self.canvas_design.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        control_frame = ttk.Frame(plot_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(control_frame, text="Refresh Plots", 
                  command=self.plot_design).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Save Plot", 
                  command=lambda: self.save_plot(self.fig_design)).pack(side=tk.LEFT, padx=5)
    
    def create_sweep_plots_tab(self, notebook):
        plot_frame = ttk.Frame(notebook)
        notebook.add(plot_frame, text="Sweep Analysis")
        
        self.canvas_sweep = FigureCanvasTkAgg(self.fig_sweep, master=plot_frame)
        self.canvas_sweep.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def create_analysis_tab(self, notebook):
        plot_frame = ttk.Frame(notebook)
        notebook.add(plot_frame, text="Advanced Analysis")
        
        self.canvas_analysis = FigureCanvasTkAgg(self.fig_analysis, master=plot_frame)
        self.canvas_analysis.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def save_design(self):
        if not self.current_design:
            messagebox.showwarning("Warning", "No design to save. Please calculate a design first.")
            return
        
        try:
            
            save_data = {
                'timestamp': datetime.now().isoformat(),
                'parameters': self.get_input_parameters(),
                'design_results': {},
                'sweep_results': self.sweep_results
            }
        
            for n, ch in self.current_design.channels.items():
                save_data['design_results'][f'channel_{n}'] = {
                    k: (float(v) if isinstance(v, (int, float)) else v) 
                    for k, v in ch.items()
                }
            

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"design_{timestamp}.json"
            filepath = os.path.join(self.data_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(save_data, f, indent=2)
            
            messagebox.showinfo("Success", f"Design saved to:\n{filepath}")
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save design: {str(e)}")
    
    def load_design(self):
        try:
            filepath = filedialog.askopenfilename(
                initialdir=self.data_dir,
                title="Select Design File",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if not filepath:
                return
            
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            params = data['parameters']
            for key, value in params.items():
                if key in self.inputs:
                    if key == 'n_channels':
                        self.inputs[key].set(int(value))
                    else:
                        self.inputs[key].set(float(value))
            
            self.calculate_design()
            

            if 'sweep_results' in data:
                
                self.sweep_results = data['sweep_results']
                self.plot_sweep_analysis()
            
            messagebox.showinfo("Success", f"Design loaded from:\n{filepath}")
            
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load design: {str(e)}")
    
    def save_plot(self, fig):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if filepath:
            fig.savefig(filepath, dpi=300, bbox_inches='tight')
            messagebox.showinfo("Success", f"Plot saved to:\n{filepath}")
    
    def run_sweep(self):
        try:
          
            base_params = self.get_input_parameters()
            sweep_param = self.sweep_var.get()
            
            min_val = self.sweep_inputs['sweep_min'].get()
            max_val = self.sweep_inputs['sweep_max'].get()
            steps = self.sweep_inputs['sweep_steps'].get()
            
            if sweep_param in ['k', 'r', 'pin1']:
                values = np.logspace(np.log10(min_val), np.log10(max_val), steps)
            else:
                values = np.linspace(min_val, max_val, steps)
            
            if sweep_param == 'n_channels':
                values = [int(v) for v in values]
            
            results = getattr(self.design_sweep, f'sweep_{sweep_param}')(base_params, values)
            self.sweep_results[sweep_param] = results
            self.plot_sweep_analysis()
            
        except Exception as e:
            messagebox.showerror("Sweep Error", str(e))
    
    def plot_design(self):
        if not self.current_design:
            return
        
        design = self.current_design
        self.fig_design.clear()
        
        channels = list(range(1, design.n_channels + 1))
        
        axes = self.fig_design.subplots(2, 3)
        
        # Plot 1: Current ranges (log scale)
        min_currents = [design.channels[n]['ic_min']*1e6 for n in channels]
        max_currents = [design.channels[n]['ic_max']*1e6 for n in channels]
        axes[0,0].semilogy(channels, min_currents, 'bo-', label='I_min', markersize=6)
        axes[0,0].semilogy(channels, max_currents, 'ro-', label='I_max', markersize=6)
        axes[0,0].set_xlabel('Channel Number')
        axes[0,0].set_ylabel('Current (μA)')
        axes[0,0].set_title('Current Ranges per Channel')
        axes[0,0].legend()
        axes[0,0].grid(True, alpha=0.3)
        
        # Plot 2: Voltage requirements
        von_max = [design.channels[n]['von_max'] for n in channels]
        delta_von = [design.channels[n]['delta_von'] for n in channels]
        axes[0,1].plot(channels, von_max, 'g^-', label='V_max', markersize=6)
        axes[0,1].plot(channels, delta_von, 'mv-', label='ΔV_on', markersize=6)
        axes[0,1].set_xlabel('Channel Number')
        axes[0,1].set_ylabel('Voltage (V)')
        axes[0,1].set_title('Output Voltage Requirements')
        axes[0,1].legend()
        axes[0,1].grid(True, alpha=0.3)
        
        # Plot 3: Amplifier gains (log scale)
        gains = [design.channels[n]['ad_rmes']/design.rmes for n in channels]
        axes[0,2].semilogy(channels, gains, 's-', color='purple', markersize=6)
        axes[0,2].set_xlabel('Channel Number')
        axes[0,2].set_ylabel('Amplifier Gain')
        axes[0,2].set_title('Required Amplifier Gains')
        axes[0,2].grid(True, alpha=0.3)
        
        # Plot 4: Input precision (log scale)
        pin_values = [design.channels[n]['pin'] for n in channels]
        axes[1,0].semilogy(channels, pin_values, 'd-', color='orange', markersize=6)
        axes[1,0].set_xlabel('Channel Number')
        axes[1,0].set_ylabel('Input Precision')
        axes[1,0].set_title('Input Precision per Channel')
        axes[1,0].grid(True, alpha=0.3)
        
        # Plot 5: Current sensitivity
        kc_values = [design.channels[n]['kc']*1e6 for n in channels]
        axes[1,1].semilogy(channels, kc_values, '*-', color='brown', markersize=6)
        axes[1,1].set_xlabel('Channel Number')
        axes[1,1].set_ylabel('Sensitivity (μA/step)')
        axes[1,1].set_title('Current Sensitivity per Channel')
        axes[1,1].grid(True, alpha=0.3)
        
        # Plot 6: Gain ratios
        gain_ratios = [design.gain_ratios.get(n, float('nan')) for n in channels[1:]]
        if any(not math.isnan(r) for r in gain_ratios):
            axes[1,2].plot(channels[1:], gain_ratios, 'o-', color='teal', markersize=6)
            axes[1,2].axhline(y=design.r, color='r', linestyle='--', label=f'Ideal (r={design.r})')
            axes[1,2].set_xlabel('Channel Transition')
            axes[1,2].set_ylabel('Gain Ratio A_dn/A_d(n+1)')
            axes[1,2].set_title('Gain Ratio Progression')
            axes[1,2].legend()
            axes[1,2].grid(True, alpha=0.3)
        else:
            axes[1,2].text(0.5, 0.5, 'No gain ratio data', ha='center', va='center', 
                          transform=axes[1,2].transAxes)
        
        self.fig_design.tight_layout()
        self.canvas_design.draw()


    def get_input_parameters(self):
        """Extract parameters from UI inputs."""
        return {
            'vos': self.inputs['vos'].get() * 1e-6,  # Convert μV to V
            'pin1': self.inputs['pin1'].get(),
            'rmes': self.inputs['rmes'].get(),
            'delta_ic1': self.inputs['delta_ic1'].get() * 1e-3,  # Convert mA to A
            'kp': self.inputs['kp'].get(),
            'von_min': self.inputs['von_min'].get(),
            'k': self.inputs['k'].get(),
            'r': self.inputs['r'].get(),
            'n_channels': self.inputs['n_channels'].get()
        }

    def calculate_design(self):
        """Calculate the current design based on input parameters."""
        try:
            params = self.get_input_parameters()
            self.current_design = CurrentMeasurementDesign(**params)
            self.current_design.design()
            self.update_results_table()
            self.update_summary()
            self.plot_design()
            
            messagebox.showinfo("Success", "Design calculated successfully!")
            
        except Exception as e:
            messagebox.showerror("Calculation Error", f"Failed to calculate design:\n{str(e)}")

    def update_results_table(self):
        """Update the results table with current design data."""
        if not self.current_design:
            return
        
        # Clear existing items
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        design = self.current_design
        channels = design.channels
        
        for n in range(1, design.n_channels + 1):
            ch = channels[n]
            gain_ratio = design.gain_ratios.get(n, float('nan'))
            
            values = (
                str(n),
                f"{ch['ic_min']*1e6:.2f}",
                f"{ch['ic_max']*1e6:.2f}",
                f"{ch['kc']*1e6:.4f}",
                f"{ch['von_min']:.3f}",
                f"{ch['von_max']:.3f}",
                f"{ch['delta_von']:.3f}",
                f"{ch['ad_rmes']:.1f}",
                f"{ch['pin']:.3f}",
                f"{gain_ratio:.3f}" if not math.isnan(gain_ratio) else "N/A"
            )
            
            self.results_tree.insert("", tk.END, values=values)

    def update_summary(self):
        """Update the design summary text."""
        if not self.current_design:
            return
        
        design = self.current_design
        min_current, max_current = design.get_total_range()
        
        # Calculate additional metrics
        max_voltage = max(ch['von_max'] for ch in design.channels.values())
        min_voltage = min(ch['von_min'] for ch in design.channels.values())
        gain_range = design.channels[1]['ad_rmes'] / design.channels[design.n_channels]['ad_rmes']
        
        summary = f"""CURRENT MEASUREMENT SYSTEM DESIGN SUMMARY
            {'='*60}

            SYSTEM PARAMETERS:
            • Offset Voltage (V_os): {design.vos*1e6:.2f} μV
            • Input Precision Ch1 (P_in1): {design.pin1:.3f}
            • Shunt Resistance (R_mes): {design.rmes} Ω
            • Base Current Range (ΔI_c1): {design.delta_ic1*1e3:.2f} mA
            • ADC Resolution (K_p): {design.kp:.6f} V/step
            • Min Output Voltage (V_on_min): {design.von_min:.3f} V
            • Overlap Factor (k): {design.k:.2f}
            • Range Ratio (r): {design.r:.2f}
            • Number of Channels: {design.n_channels}

            PERFORMANCE SUMMARY:
            • Total Current Range: {min_current*1e6:.2f} μA to {max_current*1e3:.2f} mA
            • Dynamic Range: {max_current/min_current:.0f}:1 ({20*math.log10(max_current/min_current):.1f} dB)
            • Output Precision: {design.precision:.4%}
            • Output Accuracy: {design.accuracy:.4%}
            • Channel 1 Gain (A_d1): {design.channels[1]['ad_rmes']/design.rmes:.1f}
            • Overall Gain Range: {gain_range:.1f}:1
            • Voltage Range: {min_voltage:.3f} V to {max_voltage:.3f} V

            CHANNEL TRANSITIONS:
            """
        
        for n in range(2, design.n_channels + 1):
            gain_ratio = design.gain_ratios.get(n-1, float('nan'))
            if not math.isnan(gain_ratio):
                ideal_ratio = design.r
                deviation = abs(gain_ratio - ideal_ratio) / ideal_ratio * 100
                summary += f"• Ch{n-1}→Ch{n}: Gain ratio = {gain_ratio:.3f} (ideal: {ideal_ratio}, deviation: {deviation:.1f}%)\n"
        
        
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(1.0, summary)


    def plot_sweep_analysis(self):
        """Plot comprehensive sweep analysis results."""
        if not self.sweep_results:
            return
        
        self.fig_sweep.clear()
        
        n_sweeps = len(self.sweep_results.keys())
        if n_sweeps == 0:
            return
        

        if n_sweeps == 1:
            axes = self.fig_sweep.subplots(2, 2)
            axes = axes.flatten()
        else:
            axes = self.fig_sweep.subplots(3, 2)
            axes = axes.flatten()
        
        plot_idx = 0
        
        for sweep_param, results in self.sweep_results.items():
            if plot_idx >= len(axes):
                break
                
            if sweep_param == 'rmes':
                self._plot_rmes_sweep(axes[plot_idx], results)
                plot_idx += 1
            elif sweep_param == 'k':
                self._plot_overlap_sweep(axes[plot_idx], results)
                plot_idx += 1
            elif sweep_param == 'r':
                self._plot_r_sweep(axes[plot_idx], results)
                plot_idx += 1
            elif sweep_param == 'pin1':
                self._plot_pin1_sweep(axes[plot_idx], results)
                plot_idx += 1
            elif sweep_param == 'vos':
                self._plot_vos_sweep(axes[plot_idx], results)
                plot_idx += 1
            elif sweep_param == 'n_channels':
                self._plot_n_channels_sweep(axes[plot_idx], results)
                plot_idx += 1
      

        for i in range(plot_idx, len(axes)):
            axes[i].set_visible(False)
        
        self.fig_sweep.tight_layout()
        self.canvas_sweep.draw()

    def _plot_rmes_sweep(self, ax, results):
        self.plotter.plot(ax, results, get_rmes_spec())


    def _plot_overlap_sweep(self, ax, results):
        self.plotter.plot(ax, results, get_overlap_spec())


    def _plot_r_sweep(self, ax, results):
        self.plotter.plot(ax, results, get_r_spec())


    def _plot_pin1_sweep(self, ax, results):
        self.plotter.plot(ax, results, get_pin1_spec())


    def _plot_vos_sweep(self, ax, results):
        self.plotter.plot(ax, results, get_vos_spec())


    def _plot_n_channels_sweep(self, ax, results):
        self.plotter.plot(ax, results, get_n_channels_spec())



if __name__ == "__main__":
    root = tk.Tk()
    app = ModernCurrentMeasurementUI(root)
    root.mainloop()