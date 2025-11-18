from dataclasses import dataclass
from typing import List, Callable, Optional

@dataclass
class Curve:
    x_key: str
    y_key: str
    scale_y: float = 1.0
    plot_type: str = "plot"       # plot, semilogy, loglog
    color: str = "b"
    label: Optional[str] = None
    linestyle: str = "-"
    secondary_axis: bool = False  # False → primary axis, True → secondary axis

@dataclass
class PlotSpec:
    title: str
    x_label: str
    y1_label: str
    y2_label: Optional[str]
    curves: List[Curve]

class SweepPlotter:
    def plot(self, ax, results, spec: PlotSpec):
        ax.grid(True, alpha=0.3)
        ax.set_title(spec.title)

        # primary axis
        ax.set_xlabel(spec.x_label)
        ax.set_ylabel(spec.y1_label)

        ax2 = None
        if spec.y2_label:
            ax2 = ax.twinx()
            ax2.set_ylabel(spec.y2_label)

        for c in spec.curves:
            x = [r[c.x_key] for r in results]
            y = [r[c.y_key] * c.scale_y for r in results]

            target = ax2 if c.secondary_axis else ax

            if c.plot_type == "plot":
                target.plot(x, y, color=c.color, label=c.label, linestyle=c.linestyle)
            elif c.plot_type == "semilogy":
                target.semilogy(x, y, color=c.color, label=c.label, linestyle=c.linestyle)
            elif c.plot_type == "loglog":
                target.loglog(x, y, color=c.color, label=c.label, linestyle=c.linestyle)

        ax.legend(loc="upper left")
        if ax2:
            ax2.legend(loc="upper right")


def get_r_spec():
    return PlotSpec(
        title="Range Ratio Optimization",
        x_label="Range Ratio r",
        y1_label="Dynamic Range",
        y2_label="Maximum Gain",
        curves=[
            Curve(
                x_key="r",
                y_key="dynamic_range",
                plot_type="semilogy",
                color="g",
                label="Dynamic Range",
            ),
            Curve(
                x_key="r",
                y_key="max_gain",
                plot_type="semilogy",
                color="b",
                label="Max Gain",
                linestyle="--",
                secondary_axis=True,
            ),
        ],
    )

def get_pin1_spec():
    return PlotSpec(
        title="Input Precision Trade-off",
        x_label="Input Precision P_in1",
        y1_label="Minimum Current (μA)",
        y2_label="Amplifier Gain A_d1",
        curves=[
            Curve(
                x_key="pin1",
                y_key="ic_min1",
                scale_y=1e6,
                plot_type="semilogy",
                color="b",
                label="I_c_min1",
            ),
            Curve(
                x_key="pin1",
                y_key="ad1",
                plot_type="semilogy",
                color="r",
                label="A_d1",
                linestyle="--",
                secondary_axis=True,
            ),
        ],
    )

def get_vos_spec():
    return PlotSpec(
        title="Offset Voltage Impact",
        x_label="Offset Voltage V_os (μV)",
        y1_label="Minimum Current (μA)",
        y2_label="Amplifier Gain A_d1",
        curves=[
            Curve(
                x_key="vos",
                y_key="ic_min1",
                scale_y=1e6,
                plot_type="semilogy",
                color="b",
                label="I_c_min1",
            ),
            Curve(
                x_key="vos",
                y_key="ad1",
                plot_type="semilogy",
                color="r",
                label="A_d1",
                linestyle="--",
                secondary_axis=True,
            ),
        ],
    )

def get_n_channels_spec():
    return PlotSpec(
        title="Channel Count Optimization",
        x_label="Number of Channels",
        y1_label="Dynamic Range",
        y2_label="Maximum Voltage (V)",
        curves=[
            Curve(
                x_key="n_channels",
                y_key="dynamic_range",
                plot_type="semilogy",
                color="g",
                label="Dynamic Range",
            ),
            Curve(
                x_key="n_channels",
                y_key="max_voltage",
                plot_type="plot",
                color="purple",
                label="Max Voltage",
                linestyle="--",
                secondary_axis=True,
            ),
        ],
    )


def get_overlap_spec():
    return PlotSpec(
        title="Overlap Factor Impact",
        x_label="Overlap Factor k",
        y1_label="Maximum Voltage (V)",
        y2_label="Gain Range",
        curves=[
            Curve(
                x_key="k",
                y_key="max_voltage",
                plot_type="plot",
                color="purple",
                label="Max Voltage",
            ),
            Curve(
                x_key="k",
                y_key="gain_range",
                plot_type="semilogy",
                color="orange",
                label="Gain Range",
                linestyle="--",
                secondary_axis=True,
            ),
        ],
    )


def get_rmes_spec():
    return PlotSpec(
        title="R_mes Sweep: Min Current & Gain",
        x_label="Shunt Resistance R_mes (Ω)",
        y1_label="Minimum Current (μA)",
        y2_label="Amplifier Gain A_d1",
        curves=[
            Curve("rmes", "ic_min1", scale_y=1e6, plot_type="loglog",
                  color="b", label="I_c_min1"),
            Curve("rmes", "ad1", plot_type="loglog",
                  color="r", label="A_d1", secondary_axis=True)
        ]
    )
