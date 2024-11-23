# ClickSafe: Dynamic Web Safety System  

**Tagline**: *Browse with confidence, click with security.*  

ClickSafe is a Google Chrome extension that analyzes URLs using machine learning to predict website safety. By evaluating over 50 features, ClickSafe categorizes websites into safety levels, helping users make informed decisions before accessing potentially unsafe links.

## **Key Features**
- **Dynamic Analysis**: Extracts 50+ URL, host, and content-based features.
- **ML-Powered Predictions**: Combines multiple ensemble models for high accuracy.
- **Risk Categorization**:  
  - Safe (<20%): Green  
  - Very Low Risk (20-30%): Dark Green  
  - Moderate Risk (30-50%): Gradient from Yellowish Green to Yellow  
  - Unsafe (50-80%): Gradient from Orange to Dark Orange  
  - Danger (≥80%): Red  
- **Interactive Analytics**: Visual graphs explaining prediction details.
- **User-Friendly Extension**: Chrome popup with detailed insights.

## **Installation**
1. Clone this repository:  
   ```bash
   git clone https://github.com/sprahasingh/ClickSafe-DynamicWebSafety.git
   cd ClickSafe
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
4. Run the backend:
   ```bash
   python app.py
