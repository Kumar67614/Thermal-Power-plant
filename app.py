
import math
import time
import streamlit as st
import pandas as pd
import pydeck as pdk

st.set_page_config(
    page_title="3D Thermal Power Plant + Boiler Simulator",
    page_icon="🔥",
    layout="wide",
)

# -----------------------------
# Plant component database
# -----------------------------
COMPONENTS = [
    # name, x, y, z, radius, height, color, category, function
    ("Coal Bunker", -34, 7, 5, 3.2, 7, [105, 75, 45], "Fuel", "Stores coal/fuel before controlled feeding to the milling and firing system."),
    ("Coal Mill", -34, 7, -1, 3.0, 7, [90, 95, 105], "Fuel", "Pulverizes coal to the required fineness and mixes it with primary air in pulverized-coal systems."),
    ("Fuel Feeder", -28, 9, 2, 2.0, 5, [145, 105, 55], "Fuel", "Controls and meters the fuel feed to the furnace."),
    ("Boiler Furnace", -20, 13, 0, 6.5, 25, [125, 55, 35], "Boiler", "Combustion chamber where fuel releases heat. Waterwall tubes absorb furnace heat and generate a steam-water mixture."),
    ("Steam Drum", -20, 27, 0, 2.6, 12, [70, 115, 160], "Boiler", "Separates steam from the circulating water-steam mixture and provides boiler water inventory."),
    ("Economizer", -12, 9, -1, 3.0, 9, [95, 130, 140], "Heat Recovery", "Uses outgoing flue-gas heat to raise feedwater temperature before it enters the evaporating circuit."),
    ("Superheater", -12, 20, 0, 3.0, 7, [165, 100, 45], "Boiler", "Raises saturated steam temperature above saturation to produce superheated main steam."),
    ("Reheater", -3, 18, 0, 3.0, 7, [175, 115, 50], "Boiler", "Reheats HP turbine exhaust steam before it enters the IP/LP expansion path."),
    ("Air Preheater", 2, 8, -4, 3.5, 8, [105, 95, 85], "Heat Recovery", "Transfers heat from outgoing flue gas to incoming combustion air."),
    ("ESP", 10, 8, -3, 3.0, 8, [75, 90, 110], "Emission Control", "Electrostatic precipitator that removes fine particulate matter from flue gas."),
    ("ID Fan", 14, 5, 6, 2.3, 5, [60, 125, 95], "Fans", "Draws flue gas through the boiler, heat-recovery equipment and emission-control system while maintaining furnace draft."),
    ("Stack", 18, 17, -3, 2.2, 20, [125, 125, 125], "Flue Gas", "Discharges treated flue gas to the atmosphere."),
    ("FD Fan", 0, 5, 10, 2.2, 5, [55, 130, 100], "Fans", "Supplies combustion air to the boiler."),
    ("PA Fan", -8, 5, 10, 2.0, 5, [55, 145, 110], "Fans", "Supplies primary air for fuel transport/pulverization in pulverized-coal systems."),
    ("HP Turbine", 8, 16, 7, 2.8, 9, [165, 170, 180], "Turbine", "Expands high-pressure superheated steam and converts part of its enthalpy into shaft work."),
    ("IP Turbine", 18, 16, 7, 2.6, 8, [150, 155, 170], "Turbine", "Intermediate-pressure expansion after reheating."),
    ("LP Turbine", 28, 16, 7, 3.5, 10, [135, 145, 165], "Turbine", "Final turbine expansion toward condenser pressure."),
    ("Generator", 36, 15, 7, 3.0, 9, [180, 145, 80], "Electrical", "Converts turbine shaft mechanical power into electrical power."),
    ("Surface Condenser", 30, 7, 0, 6.0, 7, [60, 115, 135], "Condenser", "Condenses LP turbine exhaust steam using cooling water and maintains low turbine back pressure."),
    ("Condensate Pump", 22, 3, 0, 1.5, 4, [55, 125, 155], "Pump", "Transfers condensate from the condenser toward the feedwater system."),
    ("Deaerator", 10, 3, 0, 4.0, 4, [80, 135, 150], "Feedwater", "Removes dissolved oxygen and other non-condensable gases while heating the feedwater."),
    ("Boiler Feed Pump", -1, 3, 0, 1.7, 5, [55, 125, 155], "Pump", "Raises feedwater pressure to the boiler operating pressure."),
    ("Cooling Tower", 34, 3, -13, 4.5, 13, [55, 115, 125], "Cooling", "Rejects condenser heat to the environment through the cooling-water system."),
    ("Ash Handling", -30, 4, -12, 5.0, 5, [80, 70, 55], "Balance of Plant", "Collects, cools and transports bottom/fly ash depending on plant arrangement."),
    ("Blowdown Tank", -24, 5, 10, 2.5, 4, [120, 85, 55], "Water Treatment", "Receives boiler blowdown used to control dissolved-solids concentration."),
]

FUNCTIONS = {x[0]: x[-1] for x in COMPONENTS}
CATEGORIES = {x[0]: x[-2] for x in COMPONENTS}

# Major flow routes. Each route is a list of XYZ points.
ROUTES = {
    "Water / Steam": [
        [22, 7, 0], [22, 4, 0], [14, 3, 0], [6, 3, 0],
        [-1, 3, 0], [-8, 8, 0], [-16, 25, 0], [-12, 22, 0],
        [-7, 22, 0], [5, 16, 7], [14, 16, 7], [24, 16, 7],
        [30, 10, 0],
    ],
    "Flue Gas": [
        [-20, 20, -6], [-12, 12, -4], [-1, 9, -4],
        [5, 9, -4], [10, 9, -3], [17, 16, -3],
    ],
    "Combustion Air": [
        [2, 7, 10], [-2, 8, 8], [-10, 9, 5],
        [-20, 13, 5],
    ],
    "Primary Air / Fuel": [
        [-8, 7, 10], [-14, 10, 7], [-20, 13, 5],
        [-28, 9, 2], [-34, 8, -1],
    ],
    "Cooling Water": [
        [30, 5, 0], [28, 5, -8], [34, 5, -13],
        [38, 7, -13], [30, 7, 0],
    ],
}

FLOW_COLORS = {
    "Water / Steam": [40, 170, 255],
    "Flue Gas": [255, 105, 35],
    "Combustion Air": [75, 220, 125],
    "Primary Air / Fuel": [255, 190, 60],
    "Cooling Water": [35, 220, 220],
}

# -----------------------------
# Controls
# -----------------------------
with st.sidebar:
    st.header("3D Simulation Controls")

    flow_speed = st.slider("Animation speed", 0.0, 5.0, 1.5, 0.1)

    selected_flow = st.multiselect(
        "Show flow paths",
        list(ROUTES.keys()),
        default=list(ROUTES.keys()),
    )

    selected_category = st.multiselect(
        "Show equipment categories",
        sorted(set(CATEGORIES.values())),
        default=sorted(set(CATEGORIES.values())),
    )

    st.markdown("---")
    st.subheader("Plant operating inputs")

    steam_flow = st.slider("Main steam flow (kg/s)", 10.0, 500.0, 100.0, 5.0)
    main_pressure = st.slider("Main steam pressure (bar)", 20.0, 180.0, 80.0, 1.0)
    main_temp = st.slider("Main steam temperature (°C)", 350.0, 650.0, 540.0, 5.0)
    condenser_pressure = st.slider("Condenser pressure (bar abs)", 0.03, 0.20, 0.08, 0.005)

    st.markdown("---")
    st.write("🖱️ Drag = rotate")
    st.write("🔍 Wheel = zoom")
    st.write("🖱️ Right drag = pan")
    st.write("👆 Click a component = inspect")

# -----------------------------
# Derived educational values
# -----------------------------
boiler_eff = 0.88
turbine_eff = 0.86
generator_eff = 0.98

# Very simplified educational estimates; not steam-table calculations.
fuel_heat_mw = steam_flow * 3000 / boiler_eff / 1000
gross_power_mw = steam_flow * 1000 * 0.95 * turbine_eff * generator_eff / 1000
heat_rate = (fuel_heat_mw * 1000) / max(gross_power_mw, 0.1)

# -----------------------------
# Build 3D layers
# -----------------------------
visible_components = [x for x in COMPONENTS if x[-2] in selected_category]

columns = pd.DataFrame(
    [
        {
            "name": x[0],
            "x": x[1],
            "y": x[3],
            "z": x[2],
            "radius": x[4],
            "height": x[5],
            "color": x[6],
            "category": x[7],
            "function": x[8],
        }
        for x in visible_components
    ]
)

# NOTE: pydeck's coordinate convention is longitude/latitude/altitude.
# We intentionally use a local schematic coordinate system for training visualization.
column_layer = pdk.Layer(
    "ColumnLayer",
    data=columns,
    get_position="[x, y, z]",
    get_elevation="height",
    radius="radius",
    elevation_scale=1,
    get_fill_color="color",
    pickable=True,
    auto_highlight=True,
    coverage=0.85,
)

path_rows = []
for name in selected_flow:
    pts = ROUTES[name]
    path_rows.append({"name": name, "path": pts, "color": FLOW_COLORS[name]})

path_layer = pdk.Layer(
    "PathLayer",
    data=pd.DataFrame(path_rows),
    get_path="path",
    get_color="color",
    width_min_pixels=5,
    width_scale=1,
    pickable=True,
)

# Animated particles: generated from each selected route.
particle_rows = []
phase = time.time() * flow_speed * 0.12
for route_name in selected_flow:
    pts = ROUTES[route_name]
    # 12 particles per route
    for j in range(12):
        t = (phase + j / 12.0) % 1.0
        u = t * (len(pts) - 1)
        i = min(int(u), len(pts) - 2)
        f = u - i
        a = pts[i]
        b = pts[i + 1]
        pos = [
            a[0] + f * (b[0] - a[0]),
            a[1] + f * (b[1] - a[1]),
            a[2] + f * (b[2] - a[2]) + 0.5,
        ]
        particle_rows.append(
            {
                "x": pos[0],
                "y": pos[1],
                "z": pos[2],
                "color": FLOW_COLORS[route_name],
                "route": route_name,
            }
        )

particle_layer = pdk.Layer(
    "ScatterplotLayer",
    data=pd.DataFrame(particle_rows),
    get_position="[x, y, z]",
    get_radius=0.45,
    radius_min_pixels=3,
    radius_max_pixels=10,
    get_fill_color="color",
    pickable=True,
)

# Ground labels using TextLayer
labels = pd.DataFrame(
    [
        {"text": x[0], "x": x[1], "y": x[3], "z": x[2] + x[5] + 1.5}
        for x in visible_components
    ]
)

text_layer = pdk.Layer(
    "TextLayer",
    data=labels,
    get_position="[x, y, z]",
    get_text="text",
    get_size=13,
    get_color=[245, 245, 245],
    get_angle=0,
    billboard=True,
    pickable=False,
)

view = pdk.ViewState(
    longitude=0,
    latitude=2,
    zoom=-1.2,
    pitch=55,
    bearing=-25,
)

tooltip = {
    "html": "<b>{name}</b><br/>Category: {category}<br/>{function}",
    "style": {"backgroundColor": "#111827", "color": "white"},
}

deck = pdk.Deck(
    layers=[column_layer, path_layer, particle_layer, text_layer],
    initial_view_state=view,
    tooltip=tooltip,
    map_provider=None,
)

# -----------------------------
# UI
# -----------------------------
tabs = st.tabs([
    "3D Plant",
    "Boiler Walkthrough",
    "Water / Steam Cycle",
    "Combustion & Flue Gas",
    "Turbine & Generator",
    "Condenser & Cooling",
    "Results",
    "Learning Guide",
])

with tabs[0]:
    st.subheader("Interactive 3D Thermal Power Plant")
    st.pydeck_chart(deck, use_container_width=True, height=720)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Main steam", f"{steam_flow:.0f} kg/s")
    c2.metric("Main pressure", f"{main_pressure:.0f} bar")
    c3.metric("Main temperature", f"{main_temp:.0f} °C")
    c4.metric("Condenser", f"{condenser_pressure:.3f} bar")

with tabs[1]:
    st.header("Boiler: Water → Steam")
    st.markdown("""
**1. Feedwater enters the economizer → 2. steam drum → 3. downcomers →  
4. waterwalls/evaporator → 5. steam-water mixture returns to drum →  
6. separated saturated steam → 7. superheater → 8. main steam outlet.**
""")

    stages = [
        ("Economizer", "Feedwater receives sensible heat from flue gas."),
        ("Steam Drum", "Steam and water are separated. The drum also provides inventory and supports circulation."),
        ("Downcomers", "Water flows downward from the drum toward the lower furnace headers."),
        ("Waterwalls / Evaporator", "Heat transfer from furnace gases causes boiling and steam generation."),
        ("Risers", "Steam-water mixture rises toward the drum."),
        ("Steam Separation", "Moisture is removed from the steam before superheating."),
        ("Superheater", "Saturated steam is heated to the specified main-steam temperature."),
    ]
    for i, (name, desc) in enumerate(stages, 1):
        st.markdown(f"### {i}. {name}")
        st.write(desc)

with tabs[2]:
    st.header("Water / Steam Cycle")
    st.markdown("""
**Condenser → Condensate Pump → Deaerator → Boiler Feed Pump → Economizer → Drum → Waterwalls → Superheater → HP Turbine → Reheater → IP/LP Turbine → Condenser**
""")
    st.info("The model is a training visualization. Exact steam properties require a steam-property library and pressure/temperature state calculations.")

with tabs[3]:
    st.header("Combustion & Flue Gas")
    st.markdown("""
**Fuel preparation → Furnace → Superheater/reheater heat surfaces → Economizer → Air Preheater → ESP → ID Fan → Stack**

**FD fan:** combustion air supply.  
**PA fan:** primary air/fuel transport in pulverized-coal firing.  
**ID fan:** pulls flue gas through the plant and helps maintain negative furnace pressure.  
**Air preheater:** transfers exhaust-gas heat to combustion air.  
**ESP:** removes particulate matter.
""")

with tabs[4]:
    st.header("Turbine & Generator")
    st.markdown("""
**Main steam → HP turbine → Reheater → IP turbine → LP turbine → Condenser**

The turbine converts steam enthalpy drop into shaft work. The generator converts shaft work into electrical output.
""")
    st.metric("Educational estimated gross power", f"{gross_power_mw:.1f} MW")

with tabs[5]:
    st.header("Condenser & Cooling System")
    st.markdown("""
The condenser receives LP exhaust steam, transfers its latent heat to cooling water and returns condensate to the cycle.

Cooling water follows approximately:

**Cooling Tower → Condenser → Cooling Tower**

A low condenser pressure improves turbine expansion, but real operation is constrained by cooling-water temperature, condenser cleanliness, air leakage and equipment limits.
""")

with tabs[6]:
    st.header("Simulation Results")
    r1, r2, r3 = st.columns(3)
    r1.metric("Estimated fuel heat input", f"{fuel_heat_mw:.1f} MW")
    r2.metric("Estimated gross power", f"{gross_power_mw:.1f} MW")
    r3.metric("Indicative heat rate", f"{heat_rate:.0f} kJ/kWh")

    st.warning("These result equations are intentionally simplified for learning. They are NOT a validated plant-performance model and should not be used for design or operation.")

with tabs[7]:
    st.header("Thermal Power Plant Learning Guide")
    st.markdown("""
### Boiler subjects to master
- Boiler pressure parts
- Furnace and waterwalls
- Steam drum
- Downcomers and risers
- Natural and forced circulation
- Economizer
- Superheater
- Reheater
- Attemperator/desuperheater
- Boiler feedwater system
- Blowdown
- Safety valves
- Soot blowing
- Draft system

### Combustion and flue gas
- Fuel preparation
- Stoichiometric air
- Excess air
- FD / PA / ID fans
- Furnace draft
- Air preheater
- ESP
- Stack

### Turbine
- HP/IP/LP sections
- Governing valves
- Reheat cycle
- Extraction/bleed steam
- Turbine efficiency
- Condenser vacuum

### TBWES-oriented mechanical preparation
Focus particularly on:
**thermodynamics, heat transfer, fluid mechanics, boiler construction, pressure parts, heat-recovery surfaces, pumps, fans, valves, piping, materials, welding/fabrication, GD&T, drawings and equipment documentation.**
""")

st.caption("Educational 3D schematic. Component geometry is intentionally simplified; real boiler and power-plant layouts vary by design, fuel, pressure, capacity and project requirements.")
