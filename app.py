from flask import Flask, request, jsonify, render_template
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit.visualization import plot_histogram, circuit_drawer
import matplotlib
matplotlib.use('Agg')  # Required for Flask rendering
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

# -----------------------------
# Build Bell State Circuit
# -----------------------------
def build_bell_circuit(state):
    qc = QuantumCircuit(2, 2)
    if state == "phi_plus":
        qc.h(0)
        qc.cx(0, 1)
    elif state == "phi_minus":
        qc.h(0)
        qc.cx(0, 1)
        qc.z(0)
    elif state == "psi_plus":
        qc.x(1)
        qc.h(0)
        qc.cx(0, 1)
    elif state == "psi_minus":
        qc.x(1)
        qc.h(0)
        qc.cx(0, 1)
        qc.z(0)
    qc.measure([0, 1], [0, 1])
    return qc

# -----------------------------
# Routes
# -----------------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/simulate', methods=['POST'])
def simulate():
    try:
        data = request.get_json(force=True)
        state = data.get('state', 'phi_plus')
        shots = int(data.get('shots', 1024))

        # --- Quantum Simulation ---
        qc = build_bell_circuit(state)
        simulator = AerSimulator()
        compiled = transpile(qc, simulator)
        job = simulator.run(compiled, shots=shots)
        result = job.result()
        counts = result.get_counts()

        # --- Correlation calculation ---
        n00, n01, n10, n11 = counts.get('00',0), counts.get('01',0), counts.get('10',0), counts.get('11',0)
        total = n00 + n01 + n10 + n11
        correlation = (n00 + n11 - n01 - n10) / total if total > 0 else 0

        # --- Circuit Image ---
        fig1 = circuit_drawer(qc, output='mpl', style={'backgroundcolor': '#0f172a', 'textcolor': '#ffffff'})
        buf1 = io.BytesIO()
        fig1.savefig(buf1, format='png', bbox_inches='tight', facecolor='#0f172a')
        buf1.seek(0)
        circuit_img = base64.b64encode(buf1.read()).decode()
        plt.close(fig1)

        # --- Histogram Image ---
        plt.style.use('dark_background')
        fig2 = plot_histogram(counts, color='#22d3ee')
        buf2 = io.BytesIO()
        fig2.savefig(buf2, format='png', bbox_inches='tight', facecolor='#0f172a')
        buf2.seek(0)
        hist_img = base64.b64encode(buf2.read()).decode()
        plt.close(fig2)

        return jsonify({
            "counts": counts,
            "correlation": f"{round(correlation, 2):+}",
            "circuit_img": f"data:image/png;base64,{circuit_img}",
            "hist_img": f"data:image/png;base64,{hist_img}"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -----------------------------
if __name__ == '__main__':
    app.run(debug=True, port=5000)
