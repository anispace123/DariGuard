"""Diagnostic script to trace every step of clicking 'Варфарин + Амиодарон' in Molecular Lab."""
import os
import sys
from streamlit.testing.v1 import AppTest

APP_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app.py"))

def trace_flow():
    print("=== STEP 2 DIAGNOSTIC TRACE START ===")
    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()
    
    print("\n--- A. BEFORE CLICK ---")
    print(f"nav_page: {at.session_state.get('nav_page')}")
    print(f"active_pair: {at.session_state.get('active_pair')}")
    print(f"active_cohort: {at.session_state.get('active_cohort')}")
    print(f"mol_custom_a: {at.session_state.get('mol_custom_a')}")
    print(f"mol_custom_b: {at.session_state.get('mol_custom_b')}")
    print(f"mol_sel_a: {at.session_state.get('mol_sel_a')}")
    print(f"mol_sel_b: {at.session_state.get('mol_sel_b')}")
    print(f"ai_a: {at.session_state.get('ai_a')}")
    print(f"ai_b: {at.session_state.get('ai_b')}")
    
    # Navigate to Molecular Lab
    print("\n--- NAVIGATING TO MOLECULAR LAB ---")
    nav = [r for r in at.radio if r.key == "main_nav_radio"][0]
    nav.set_value(nav.options[1]).run()
    
    print(f"nav_page: {at.session_state.get('nav_page')}")
    print(f"active_pair: {at.session_state.get('active_pair')}")
    print(f"active_cohort: {at.session_state.get('active_cohort')}")
    print(f"mol_active_pair: {at.session_state.get('mol_active_pair')}")
    print(f"mol_custom_a: {at.session_state.get('mol_custom_a')}")
    print(f"mol_custom_b: {at.session_state.get('mol_custom_b')}")
    print(f"mol_sel_a: {at.session_state.get('mol_sel_a')}")
    print(f"mol_sel_b: {at.session_state.get('mol_sel_b')}")
    
    # Check showcase buttons
    btn_keys = [b.key for b in at.button]
    print(f"Visible buttons: {btn_keys}")
    
    amio_btn = [b for b in at.button if b.key == "chip_pair_warfarin_amiodarone"]
    if not amio_btn:
        print("ERROR: chip_pair_warfarin_amiodarone not found!")
        return
        
    print("\n--- B. CLICKING BUTTON 'chip_pair_warfarin_amiodarone' ---")
    amio_btn[0].click().run()
    
    print("\n--- C. AFTER CLICK & RUN ---")
    print(f"nav_page: {at.session_state.get('nav_page')}")
    print(f"active_pair: {at.session_state.get('active_pair')}")
    print(f"active_cohort: {at.session_state.get('active_cohort')}")
    print(f"mol_active_pair: {at.session_state.get('mol_active_pair')}")
    print(f"mol_custom_a: {at.session_state.get('mol_custom_a')}")
    print(f"mol_custom_b: {at.session_state.get('mol_custom_b')}")
    print(f"mol_sel_a: {at.session_state.get('mol_sel_a')}")
    print(f"mol_sel_b: {at.session_state.get('mol_sel_b')}")
    print(f"ai_a: {at.session_state.get('ai_a')}")
    print(f"ai_b: {at.session_state.get('ai_b')}")
    
    # Check rendered elements in at
    tabs = [t for t in at.tabs]
    print(f"Tabs rendered: {[t.label for t in tabs] if tabs else 'No tabs'}")
    
    # Check markdown texts
    markdown_texts = [m.value for m in at.markdown if "Амиодарон" in m.value or "Amiodarone" in m.value or "Кордарон" in m.value or "amiodarone" in m.value]
    print(f"Amiodarone mentions in markdown: {len(markdown_texts)}")
    for m in markdown_texts[:5]:
        print(f"  -> {m[:100]}...")
        
    print("=== STEP 2 DIAGNOSTIC TRACE END ===")

if __name__ == "__main__":
    trace_flow()
