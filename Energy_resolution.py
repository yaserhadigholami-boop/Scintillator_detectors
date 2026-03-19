# filename: pet_sim_app.py
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="PET Detector Simulation", layout="wide")

# ==============================
# CONSTANTS
# ==============================
N_CHANNELS = 256
PHOTOPEAKS = {'F-18': 511, 'Ga-68': 511, 'Zr-89': 511}
COMPTON_EDGES = {'F-18': 340, 'Ga-68': 340, 'Zr-89': 340}
BACKSCATTER_PEAKS = {'F-18': 170, 'Ga-68': 170, 'Zr-89': 170}
POSITRON_RANGES = {'F-18': 0.6, 'Ga-68': 2.9, 'Zr-89': 1.3}  # mm
BASE_RESOLUTION = {'F-18': 0.03, 'Ga-68': 0.03, 'Zr-89': 0.03}

# ==============================
# SESSION STATE INITIALIZATION
# ==============================
if "spectrum" not in st.session_state:
    st.session_state.spectrum = np.zeros(N_CHANNELS)
if "accepted_spectrum" not in st.session_state:
    st.session_state.accepted_spectrum = np.zeros(N_CHANNELS)
if "photopeak_energies" not in st.session_state:
    st.session_state.photopeak_energies = []

# ==============================
# SIDEBAR CONTROLS
# ==============================
st.sidebar.title("Controls")
current_isotope = st.sidebar.radio("Select Isotope", ('F-18', 'Ga-68', 'Zr-89'))
voltage = st.sidebar.slider("Voltage (V)", 400, 1200, 800)
sca_low = st.sidebar.slider("SCA Low (keV)", 0, 800, 400)
sca_high = st.sidebar.slider("SCA High (keV)", 0, 800, 600)
events_per_frame = st.sidebar.slider("Events per frame", 10, 1000, 200)

if st.sidebar.button("Reset"):
    st.session_state.spectrum = np.zeros(N_CHANNELS)
    st.session_state.accepted_spectrum = np.zeros(N_CHANNELS)
    st.session_state.photopeak_energies = []

# ==============================
# SIMULATION FUNCTION
# ==============================
def simulate_event(voltage, isotope):
    if isotope == 'F-18':
        p_photo, p_compton, p_back = 0.45, 0.50, 0.05
    elif isotope == 'Ga-68':
        p_photo, p_compton, p_back = 0.35, 0.60, 0.05
    else:
        p_photo, p_compton, p_back = 0.30, 0.55, 0.05

    r = np.random.rand()
    sigma = BASE_RESOLUTION[isotope]*PHOTOPEAKS[isotope]*(1000/voltage)

    if r < p_photo:
        sigma_total = sigma + 0.05*POSITRON_RANGES[isotope]*PHOTOPEAKS[isotope]/10
        E_dep = np.random.normal(PHOTOPEAKS[isotope], sigma_total)
    elif r < p_photo + p_compton:
        E_dep = np.random.uniform(50, COMPTON_EDGES[isotope])
    else:
        E_dep = np.random.normal(BACKSCATTER_PEAKS[isotope], 10)

    if isotope == 'Zr-89' and np.random.rand() < 0.1:
        E_dep = np.random.normal(909, 5)

    E_dep = np.clip(E_dep, 0, 1000)
    return E_dep

# ==============================
# RUN SIMULATION
# ==============================
accepted_count = 0
for _ in range(events_per_frame):
    E_dep = simulate_event(voltage, current_isotope)
    ch = int(E_dep/1000*N_CHANNELS)
    if 0 <= ch < N_CHANNELS:
        st.session_state.spectrum[ch] += 1
        if sca_low < E_dep < sca_high:
            st.session_state.accepted_spectrum[ch] += 1
            accepted_count += 1
    if abs(E_dep-PHOTOPEAKS[current_isotope])<30:
        st.session_state.photopeak_energies.append(E_dep)

# Calculate running average resolution
if len(st.session_state.photopeak_energies) > 1:
    sigma = np.std(st.session_state.photopeak_energies)
    resolution_avg = 100*2.355*sigma/PHOTOPEAKS[current_isotope]
else:
    resolution_avg = 0

# ==============================
# PLOTS
# ==============================
fig, ax = plt.subplots(1,2,figsize=(12,5))
x_axis = np.linspace(0,1000,N_CHANNELS)
ax[0].plot(x_axis, st.session_state.spectrum, label="All events")
ax[0].plot(x_axis, st.session_state.accepted_spectrum, label="SCA accepted")
ax[0].set_xlabel("Energy (keV)")
ax[0].set_ylabel("Counts")
ax[0].set_title("Energy Spectrum")
ax[0].legend()

# Positron range cloud
r_max = POSITRON_RANGES[current_isotope]
radii = np.abs(np.random.normal(0, r_max/2, 200))
angles = np.random.uniform(0,2*np.pi,200)
x = radii*np.cos(angles)
y = radii*np.sin(angles)
ax[1].scatter(x,y,s=5,alpha=0.3)
ax[1].set_xlim(-5,5)
ax[1].set_ylim(-5,5)
ax[1].set_aspect('equal')
ax[1].set_title(f"{current_isotope} Positron Range Cloud ~{r_max} mm")

st.pyplot(fig)
st.write(f"Accepted events this frame: {accepted_count}")
st.write(f"Running average resolution: {resolution_avg:.2f}%")
