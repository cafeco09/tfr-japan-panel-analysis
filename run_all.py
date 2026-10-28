"""Run the World-food analysis; --legacy runs the original prefectural pipeline."""
import argparse
from pathlib import Path
import subprocess
import sys


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--legacy',action='store_true',help='Run the original six-stage prefectural analysis')
    args=parser.parse_args()
    root=Path(__file__).resolve().parent
    names=(['_01_core_models.py','_02_imports_no_yearFE.py','_03_eating_out_2024_25.py',
            '_04_period_panel_interactions.py','_05_plots.py','_06_export_tables.py'] if args.legacy
           else ['_14_external_food_imports.py','_15_external_food_analysis.py'])
    for name in names:
        print(f"\n{'='*72}\nRUNNING {name}\n{'='*72}",flush=True)
        result=subprocess.run([sys.executable,str(root/'scripts'/name)],cwd=root)
        if result.returncode:
            print(f'FAILED: {name}',flush=True)
            return result.returncode
    destination='output/tables and output/figures' if args.legacy else 'output/external_food_imports'
    print(f'\nAll stages completed. Results: {destination}',flush=True)
    return 0


if __name__=='__main__':
    sys.exit(main())
