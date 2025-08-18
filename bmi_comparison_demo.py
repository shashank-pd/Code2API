#!/usr/bin/env python3
"""
Demonstration of BMI calculations for Imperial vs Metric systems
"""
import requests
import json

BASE_URL = "http://localhost:8001"

def demo_bmi_calculations():
    """Demonstrate the difference between Imperial and Metric BMI calculations"""
    
    print("=" * 60)
    print("BMI CALCULATION COMPARISON: IMPERIAL VS METRIC")
    print("=" * 60)
    
    # Same person's measurements in different units
    # Person: 5'10" (70 inches), 150 lbs
    # Converted: 1.778 meters, 68 kg
    
    print("\n📏 SAME PERSON, DIFFERENT UNIT SYSTEMS:")
    print("Imperial: 5'10\" (70 inches), 150 lbs")
    print("Metric: 1.778 meters, 68 kg")
    
    # Test Imperial BMI
    imperial_data = {
        "weight": 150,  # pounds
        "height": 70    # inches
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/calculate-bmi-imperial", 
            json=imperial_data,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code == 200:
            imperial_result = response.json()
            print(f"\n🇺🇸 IMPERIAL CALCULATION:")
            print(f"Formula: (150 / 70²) × 703 = {imperial_result.get('bmi')}")
            print(f"BMI: {imperial_result.get('bmi')}")
            print(f"Category: {imperial_result.get('category')}")
        else:
            print(f"Imperial API Error: {response.status_code}")
            
    except Exception as e:
        print(f"Imperial API Error: {e}")
    
    # Test Metric BMI
    metric_data = {
        "weight": 68.0,   # kg (150 lbs ≈ 68 kg)
        "height": 1.778   # meters (70 inches ≈ 1.778 m)
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/calculate-bmi", 
            json=metric_data,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code == 200:
            metric_result = response.json()
            print(f"\n🌍 METRIC CALCULATION:")
            print(f"Formula: 68 / 1.778² = {metric_result.get('bmi')}")
            print(f"BMI: {metric_result.get('bmi')}")
            print(f"Category: {metric_result.get('category')}")
        else:
            print(f"Metric API Error: {response.status_code}")
            
    except Exception as e:
        print(f"Metric API Error: {e}")
    
    print("\n" + "=" * 60)
    print("SUMMARY OF DIFFERENCES:")
    print("=" * 60)
    print("Imperial:")
    print("  • Input: pounds + inches")
    print("  • Formula: (weight_lbs / height_inches²) × 703")
    print("  • Used in: USA primarily")
    print()
    print("Metric:")
    print("  • Input: kilograms + meters") 
    print("  • Formula: weight_kg / height_m²")
    print("  • Used in: Most of the world")
    print()
    print("Both should give similar BMI values for the same person!")

if __name__ == "__main__":
    demo_bmi_calculations()
