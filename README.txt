Run from this folder:

python -m pip install -r requirements.txt
python -m streamlit run app.py

This version uses Streamlit's native PyDeck/Deck.gl 3D renderer instead of the previous Three.js iframe loader, which avoids the blank 3D viewport caused by the old OrbitControls path.
