
import math
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="Thermal Power Plant & Boiler Simulator", layout="wide")

# -----------------------------
# Thermodynamic helper functions
# Educational simplified property model.
# -----------------------------
def cp_water(T):
    return 4.18  # kJ/kg-K

def cp_steam(T):
    return 2.08  # kJ/kg-K

def h_water(T):
    # Reference: h=0 at 0 C; simplified compressed/subcooled liquid
    return cp_water(T) * T

def h_sat_liquid(T):
    return 4.18 * T

def h_fg(T):
    # Approximate latent heat over common boiler range, kJ/kg
    return max(1200.0, 2500.9 - 2.35*T)

def h_sat_vapor(T):
    return h_sat_liquid(T) + h_fg(T)

def saturation_temp(P_bar):
    # Approximate inverse saturation curve for educational use.
    # Antoine-like empirical interpolation over 1-220 bar.
    pts = np.array([1, 2, 5, 10, 20, 40, 60, 100, 150, 200, 220], float)
    Ts  = np.array([100,120,152,180,212,250,276,311,342,365,374], float)
    return float(np.interp(P_bar, pts, Ts))

def steam_h(P_bar, T_C):
    Tsat = saturation_temp(P_bar)
    if T_C <= Tsat + 0.5:
        return h_sat_vapor(Tsat)
    return h_sat_vapor(Tsat) + cp_steam(T_C) * (T_C - Tsat)

def steam_simplified(P_bar, T_C):
    # Relative entropy-like educational index, not IAPWS entropy.
    Tk = T_C + 273.15
    return cp_steam(T_C) * math.log(Tk/273.15) - 0.4615*math.log(max(P_bar,0.01))

def turbine_expand(h_in, P_in, T_in, P_out, eta):
    # Use a simple pressure-dependent ideal enthalpy drop proxy.
    ratio = max(P_in/P_out, 1.001)
    # Educational ideal drop correlation; keeps simulator stable.
    dh_ideal = min(900.0, 210.0*math.log(ratio) + 0.55*max(T_in-300,0))
    h_is = max(h_in - dh_ideal, 100.0)
    h_out = h_in - eta*dh_ideal
    T_out = max(100.0, T_in - eta*(dh_ideal/cp_steam(T_in)))
    return h_out, T_out, h_is

def pump_work(P1_bar, P2_bar, eta, rho=0.001):
    # v ~= 0.001 m3/kg; W = v dP / eta -> kJ/kg
    return rho*(P2_bar-P1_bar)*100/eta

def air_density(T_C):
    return 101325/(287.05*(T_C+273.15))

# -----------------------------
# UI
# -----------------------------
st.title("🔥 Thermal Power Plant + Boiler Simulator")
st.caption("Educational Rankine-cycle and boiler simulator — follow water → steam → power → condenser → feedwater.")

with st.sidebar:
    st.header("Plant Inputs")
    steam_flow = st.slider("Main steam flow (kg/s)", 10.0, 500.0, 100.0, 5.0)
    main_pressure = st.slider("Boiler drum / main steam pressure (bar)", 20.0, 180.0, 100.0, 5.0)
    main_temp = st.slider("Main steam temperature (°C)", 350.0, 600.0, 540.0, 5.0)
    reheat_pressure = st.slider("Reheater outlet / IP inlet pressure (bar)", 10.0, 60.0, 30.0, 1.0)
    reheat_temp = st.slider("Reheat temperature (°C)", 350.0, 620.0, 540.0, 5.0)
    condenser_pressure = st.slider("Condenser pressure (bar abs)", 0.03, 0.30, 0.08, 0.01)
    boiler_eff = st.slider("Boiler efficiency (%)", 65.0, 95.0, 88.0, 0.5)
    mech_eff = st.slider("Mechanical efficiency (%)", 90.0, 100.0, 98.0, 0.5)
    gen_eff = st.slider("Generator efficiency (%)", 90.0, 100.0, 98.0, 0.5)
    turbine_eff = st.slider("Turbine isentropic efficiency (%)", 65.0, 95.0, 85.0, 1.0)
    fuel_lhv = st.slider("Fuel LHV (MJ/kg)", 10.0, 45.0, 25.0, 0.5)
    excess_air = st.slider("Excess air (%)", 5.0, 60.0, 20.0, 1.0)
    ambient_T = st.slider("Ambient air temperature (°C)", 0.0, 50.0, 30.0, 1.0)

# -----------------------------
# Process calculations
# -----------------------------
Tsat = saturation_temp(main_pressure)
h_fw = h_water(105)
P_cond = condenser_pressure

# Pumps
w_bfp = pump_work(P_cond, main_pressure, 0.82)
w_cep = pump_work(P_cond, 5.0, 0.80)
h_bfp_out = h_fw + w_bfp

# Economizer and drum
economizer_out_T = max(180.0, min(Tsat-20.0, 0.92*Tsat))
h_econ_out = h_water(economizer_out_T)
h_drum_vapor = h_sat_vapor(Tsat)
boiler_heat_per_kg = max(1.0, h_drum_vapor - h_bfp_out)

# Superheater
h_main = steam_h(main_pressure, main_temp)
superheat_duty = max(0, h_main - h_drum_vapor)

# Turbine stages
eta_t = turbine_eff/100
h_hp_out, T_hp_out, _ = turbine_expand(h_main, main_pressure, main_temp, reheat_pressure, eta_t)
hp_work = max(0, h_main-h_hp_out)

h_reheat_in = h_hp_out
h_reheat_out = steam_h(reheat_pressure, reheat_temp)
reheat_duty = max(0, h_reheat_out-h_reheat_in)

h_ip_out, T_ip_out, _ = turbine_expand(h_reheat_out, reheat_pressure, reheat_temp, 3.0, eta_t)
ip_work = max(0, h_reheat_out-h_ip_out)

h_lp_out, T_lp_out, _ = turbine_expand(h_ip_out, 3.0, T_ip_out, P_cond, eta_t)
lp_work = max(0, h_ip_out-h_lp_out)

turbine_specific_work = hp_work + ip_work + lp_work
gross_turbine_power_MW = steam_flow*turbine_specific_work/1000
shaft_power_MW = gross_turbine_power_MW*(mech_eff/100)
gross_electric_MW = shaft_power_MW*(gen_eff/100)

pump_power_MW = steam_flow*(w_bfp+w_cep)/1000
net_electric_MW = max(0, gross_electric_MW-pump_power_MW)

# Boiler heat and fuel
boiler_duty_MW = steam_flow*boiler_heat_per_kg/1000
fuel_thermal_MW = boiler_duty_MW/(boiler_eff/100)
fuel_flow_kg_s = fuel_thermal_MW*1000/(fuel_lhv*1000)

# Combustion air: simple stoichiometric proxy
air_fuel_ratio = 12.0*(1+excess_air/100)
air_flow = fuel_flow_kg_s*air_fuel_ratio
flue_gas_flow = air_flow + fuel_flow_kg_s

# Cooling water proxy
condensate_heat = steam_flow*max(0, h_ip_out-h_lp_out)/1000
cw_rise = 8.0
cooling_water_flow = condensate_heat/(cp_water(35)*cw_rise)*1000 if condensate_heat > 0 else 0

# Heat losses
loss_boiler = fuel_thermal_MW-boiler_duty_MW
cycle_heat_in_MW = boiler_duty_MW + reheat_duty*steam_flow/1000
cycle_eff = net_electric_MW/max(fuel_thermal_MW, 1e-6)*100

# -----------------------------
# Tabs
# -----------------------------
tabs = st.tabs([
    "1. Plant Overview", "2. Boiler Walkthrough", "3. Water/Steam Cycle",
    "4. Combustion & Flue Gas", "5. Turbine & Generator",
    "6. Condenser & Cooling", "7. Results", "8. Learning Guide"
])

with tabs[0]:
    st.subheader("Overall thermal power plant flow")
    st.markdown("""
**Fuel + Air → Furnace/Boiler → Superheater → HP Turbine → Reheater → IP Turbine → LP Turbine → Condenser → Condensate Pump → Feedwater System → Boiler Feed Pump → Economizer → Drum → Waterwalls → Superheater**

Parallel support systems: **FD/PA/ID fans, air preheater, ESP, ash handling, cooling tower, water treatment, blowdown, drains/vents and electrical generator.**
""")
    st.code("""
FUEL → MILL/FEED SYSTEM → FURNACE
                         ↑ AIR
                         │
Flue gas → SH → ECO → APH → ESP → ID FAN → STACK
               │
Feedwater → ECO → DRUM → WATERWALL → DRUM → SH → HP TURBINE
                                             ↓
                                          REHEATER
                                             ↓
                                        IP → LP TURBINE
                                             ↓
                                         CONDENSER
                                             ↓
                                      CONDENSATE PUMP
                                             ↓
                                    DEAERATOR / HEATERS
                                             ↓
                                      BOILER FEED PUMP
                                             ↓
                                          ECONOMIZER
""", language="text")

with tabs[1]:
    st.subheader("Boiler: component-by-component simulation")
    components = [
        ("1. Fuel system", "Stores, meters and delivers coal/oil/gas to the furnace.", "Fuel flow", f"{fuel_flow_kg_s:.2f} kg/s"),
        ("2. Air system", "FD fan supplies combustion air; PA fan can transport/pulverize coal; ID fan maintains furnace draft.", "Air flow", f"{air_flow:.1f} kg/s"),
        ("3. Furnace", "Fuel burns with air. Chemical energy becomes high-temperature flue gas and radiant heat.", "Thermal input", f"{fuel_thermal_MW:.2f} MW"),
        ("4. Waterwalls / evaporator", "Boiler water circulates through wall tubes and absorbs furnace heat; part of the water becomes steam.", "Evaporation duty", f"{steam_flow*boiler_heat_per_kg/1000:.2f} MW"),
        ("5. Steam drum", "Separates steam from water, provides inventory, receives downcomer flow and supports blowdown.", "Saturation T", f"{Tsat:.1f} °C"),
        ("6. Economizer", "Uses outgoing flue-gas heat to raise feedwater temperature before the drum.", "Outlet T", f"{economizer_out_T:.1f} °C"),
        ("7. Superheater", "Raises saturated steam above saturation temperature to reduce turbine moisture and increase work.", "Superheat duty", f"{superheat_duty*steam_flow/1000:.2f} MW"),
        ("8. Attemperator", "Sprays controlled water into steam to regulate superheat/reheat temperature.", "Target main T", f"{main_temp:.0f} °C"),
        ("9. Reheater", "Receives HP turbine exhaust and reheats it before IP turbine expansion.", "Reheat duty", f"{reheat_duty*steam_flow/1000:.2f} MW"),
        ("10. Air preheater", "Transfers heat from flue gas to incoming combustion air, reducing fuel demand.", "Concept", "Gas → Air"),
        ("11. ESP / dust collector", "Removes particulate matter from flue gas before the stack.", "Concept", "Particle removal"),
        ("12. Stack / chimney", "Discharges treated flue gas at adequate elevation.", "Flue gas", f"{flue_gas_flow:.1f} kg/s"),
        ("13. Blowdown", "Removes concentrated dissolved solids from boiler water to protect heat-transfer surfaces.", "Concept", "Controlled purge"),
    ]
    for name, fn, label, value in components:
        with st.expander(name):
            st.write(fn)
            st.metric(label, value)

    st.info("Important: This simulator uses simplified property correlations. It is intended to learn process logic, energy flow and component functions—not for boiler design, safety, code compliance or plant operation.")

with tabs[2]:
    st.subheader("Water → Steam → Water")
    stages = [
        ("Condenser outlet", P_cond, max(30, Tsat*0.35), h_water(35)),
        ("Feedwater system", 5.0, 105, h_fw),
        ("Boiler feed pump outlet", main_pressure, 105+w_bfp/cp_water(105), h_bfp_out),
        ("Economizer outlet", main_pressure, economizer_out_T, h_econ_out),
        ("Drum saturated liquid", main_pressure, Tsat, h_sat_liquid(Tsat)),
        ("Drum saturated vapor", main_pressure, Tsat, h_drum_vapor),
        ("Main superheated steam", main_pressure, main_temp, h_main),
        ("HP turbine exhaust", reheat_pressure, T_hp_out, h_hp_out),
        ("Reheater outlet", reheat_pressure, reheat_temp, h_reheat_out),
        ("IP turbine exhaust", 3.0, T_ip_out, h_ip_out),
        ("LP turbine exhaust", P_cond, T_lp_out, h_lp_out),
    ]
    st.dataframe(
        [{"Point":s, "Pressure (bar)":round(p,3), "Temperature (°C)":round(t,1), "Enthalpy (kJ/kg)":round(h,1)}
         for s,p,t,h in stages],
        use_container_width=True, hide_index=True
    )

    st.markdown("### What changes at each stage?")
    st.markdown("""
- **Pump:** pressure increases; liquid remains approximately liquid.
- **Economizer:** feedwater temperature rises using flue-gas heat.
- **Evaporator/waterwall:** latent heat converts water to steam.
- **Superheater:** steam temperature rises while remaining single-phase.
- **Turbine:** steam expands and produces shaft work.
- **Condenser:** exhaust steam rejects heat and returns toward liquid.
- **Feedwater heaters/deaerator:** recover heat and remove dissolved gases.
""")

with tabs[3]:
    st.subheader("Combustion and flue-gas path")
    c1, c2, c3 = st.columns(3)
    c1.metric("Fuel flow", f"{fuel_flow_kg_s:.2f} kg/s")
    c2.metric("Combustion air", f"{air_flow:.1f} kg/s")
    c3.metric("Flue gas proxy", f"{flue_gas_flow:.1f} kg/s")

    fg_temp = np.array([1100, 950, 780, 650, 500, 380, 150])
    fg_labels = ["Furnace", "Superheater", "Reheater", "Economizer", "Air Preheater", "ESP inlet", "Stack"]
    fig, ax = plt.subplots(figsize=(9,4))
    ax.plot(fg_labels, fg_temp, marker="o")
    ax.set_ylabel("Illustrative flue-gas temperature (°C)")
    ax.set_title("Typical qualitative flue-gas cooling path")
    ax.tick_params(axis="x", rotation=30)
    ax.grid(True, alpha=0.25)
    st.pyplot(fig)

    st.markdown("""
**FD fan → furnace:** supplies combustion air.  
**Furnace → superheater/reheater:** hot gas transfers heat to steam surfaces.  
**Economizer:** recovers sensible heat to feedwater.  
**Air preheater:** recovers heat to incoming air.  
**ESP/bag filter:** particulate control.  
**ID fan:** pulls gas through the boiler and maintains negative furnace pressure.  
**Stack:** final discharge.
""")

with tabs[4]:
    st.subheader("Turbine → shaft → generator")
    cols = st.columns(4)
    cols[0].metric("HP work", f"{hp_work:.1f} kJ/kg")
    cols[1].metric("IP work", f"{ip_work:.1f} kJ/kg")
    cols[2].metric("LP work", f"{lp_work:.1f} kJ/kg")
    cols[3].metric("Gross electric", f"{gross_electric_MW:.2f} MW")

    st.markdown("""
**HP turbine:** first expansion from boiler pressure.  
**Reheater:** raises HP exhaust temperature.  
**IP turbine:** second expansion.  
**LP turbine:** final expansion toward condenser pressure.  
**Shaft:** combines turbine stage torque.  
**Generator:** converts mechanical power into electrical power.
""")

    turbine_chart = {
        "HP turbine": hp_work,
        "IP turbine": ip_work,
        "LP turbine": lp_work
    }
    fig, ax = plt.subplots(figsize=(8,4))
    ax.bar(turbine_chart.keys(), turbine_chart.values())
    ax.set_ylabel("Specific work (kJ/kg)")
    ax.set_title("Calculated turbine-stage work")
    st.pyplot(fig)

with tabs[5]:
    st.subheader("Condenser and cooling-water system")
    st.metric("Approx. cooling-water flow", f"{cooling_water_flow:.1f} kg/s")
    st.markdown("""
The condenser has three main jobs:
1. Condense turbine exhaust steam into water.
2. Maintain low back pressure so the turbine can produce more work.
3. Transfer rejected heat to cooling water.

Typical cooling loop:

**Condenser → hot cooling water → cooling tower → cooled water → condenser**

The condensate then travels through the condensate/feedwater system and ultimately returns to the boiler.
""")
    T_cw = np.linspace(30, 38, 20)
    q = cooling_water_flow * 4.18 * (T_cw-T_cw[0])/1000
    fig, ax = plt.subplots(figsize=(8,4))
    ax.plot(T_cw, q)
    ax.set_xlabel("Cooling-water temperature (°C)")
    ax.set_ylabel("Heat pickup (MW, simplified)")
    ax.set_title("Illustrative condenser cooling-water heat pickup")
    ax.grid(True, alpha=0.25)
    st.pyplot(fig)

with tabs[6]:
    st.subheader("Plant performance summary")
    m = st.columns(6)
    m[0].metric("Boiler duty", f"{boiler_duty_MW:.1f} MW")
    m[1].metric("Fuel thermal input", f"{fuel_thermal_MW:.1f} MW")
    m[2].metric("Gross electric", f"{gross_electric_MW:.1f} MW")
    m[3].metric("Pump auxiliary", f"{pump_power_MW:.2f} MW")
    m[4].metric("Net electric", f"{net_electric_MW:.1f} MW")
    m[5].metric("Net/fuel efficiency", f"{cycle_eff:.1f}%")

    losses = {
        "Boiler loss proxy": max(loss_boiler,0),
        "Turbine/conversion losses": max(gross_turbine_power_MW-gross_electric_MW,0),
        "Pump auxiliary": pump_power_MW,
    }
    fig, ax = plt.subplots(figsize=(8,4))
    ax.bar(losses.keys(), losses.values())
    ax.set_ylabel("MW")
    ax.set_title("Major energy-flow loss proxies")
    ax.tick_params(axis="x", rotation=20)
    st.pyplot(fig)

    st.markdown("### Core equations used")
    st.latex(r"\dot Q_{boiler} = \dot m_s (h_{main}-h_{FW,pump})")
    st.latex(r"\dot W_{turbine} = \dot m_s(h_{in}-h_{out})")
    st.latex(r"\dot W_{pump} \approx \dot m\,v\,\Delta P/\eta_p")
    st.latex(r"\eta_{boiler} = \dot Q_{boiler}/(\dot m_f LHV)")
    st.latex(r"\eta_{plant} \approx P_{net}/(\dot m_f LHV)")
    st.latex(r"\dot Q = \dot m c_p \Delta T")

with tabs[7]:
    st.subheader("How to study this simulator for a Mechanical GAT role")
    st.markdown("""
### Level 1 — Trace the process
Start at the **condenser outlet** and trace one kilogram of water all the way to:
**pump → economizer → drum → waterwall → superheater → HP turbine → reheater → IP turbine → LP turbine → condenser**.

### Level 2 — Understand every boiler surface
Learn the purpose and heat-transfer mechanism of:
- Economizer
- Evaporator / waterwall
- Steam drum
- Superheater
- Reheater
- Attemperator
- Air preheater

### Level 3 — Understand circulation
Know the difference between:
- Natural circulation boiler
- Forced circulation
- Once-through boiler

Understand **downcomers, risers, drum level, circulation ratio, boiling, steam separation and blowdown**.

### Level 4 — Learn combustion and draft
Understand:
**Fuel → combustion → excess air → furnace draft → FD/PA/ID fans → flue gas → APH → ESP → stack.**

### Level 5 — Connect thermodynamics
Be able to explain:
- Saturation temperature vs pressure
- Enthalpy
- Latent heat
- Superheat
- Isentropic expansion
- Turbine efficiency
- Pump work
- Boiler efficiency
- Heat rate
- Rankine cycle efficiency

### Level 6 — Industrial boiler thinking
Then study:
- Drum level control
- Three-element feedwater control
- Furnace pressure control
- Steam temperature control / attemperation
- Combustion control
- Soot blowing
- Blowdown
- Safety valves
- Interlocks and trips
- Startup/shutdown sequence
- Tube failures and common boiler problems
""")
    st.success("Recommended exercise: change only ONE input at a time and explain why every downstream parameter changes.")

st.divider()
st.caption("Educational model. Simplified steam properties and turbine/combustion correlations are used. Do not use this application for real plant design, control, safety calculations, equipment sizing, or operating decisions.")
