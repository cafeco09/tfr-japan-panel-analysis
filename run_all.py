"""Run the full pipeline in order."""
import subprocess, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = ["_01_core_models.py", "_02_imports_no_yearFE.py",
           "_03_eating_out_2024_25.py", "_04_period_panel_interactions.py",
           "_05_plots.py", "_06_export_tables.py"]
for s in SCRIPTS:
    print("\n" + "="*72)
    print(f"RUNNING {s}")
    print("="*72, flush=True)
    r = subprocess.run([sys.executable, os.path.join(HERE, "scripts", s)])
    if r.returncode != 0:
        print(f"FAILED: {s}"); sys.exit(r.returncode)
print("\nAll scripts completed. See output/tables and output/figures.")
