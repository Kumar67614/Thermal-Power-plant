# Thermal Power Plant + Boiler Simulator

This is an educational Streamlit simulator for understanding a conventional Rankine-cycle thermal power plant with a detailed boiler-side walkthrough.

## Included systems

### Boiler island
- Fuel system
- Furnace/combustion
- FD/PA/ID fan concepts
- Waterwalls / evaporator
- Steam drum
- Downcomer/riser concept
- Economizer
- Superheater
- Attemperator
- Reheater
- Air preheater
- ESP / particulate removal
- Stack
- Blowdown

### Steam-water cycle
- Condenser
- Condensate/feedwater system
- Boiler feed pump
- Economizer
- Drum
- Superheater
- HP turbine
- Reheater
- IP turbine
- LP turbine

### Cooling
- Condenser
- Cooling-water loop
- Cooling tower concept

### Outputs
- Boiler duty
- Fuel thermal input
- Fuel flow
- Air flow
- Flue-gas flow proxy
- Turbine stage work
- Gross electrical power
- Pump auxiliary power
- Net electrical power
- Simplified net efficiency

## Run

1. Install Python 3.10+.
2. Open a terminal in this folder.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run:

```bash
streamlit run app.py
```

5. Open the local address shown by Streamlit.

## Important engineering note

The simulator is designed for learning process relationships, not for engineering design or real plant operation. Steam properties, turbine expansion, combustion air, flue-gas and cooling-water calculations are intentionally simplified. For design-grade work, use validated IAPWS-IF97/REFPROP or equivalent property data, manufacturer curves, detailed heat balances and applicable codes/standards.
