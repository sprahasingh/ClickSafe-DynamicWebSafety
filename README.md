# ClickSafe: Dynamic Web Safety System

**Browse with confidence, click with security.**

ClickSafe is a **Google Chrome extension powered by machine learning** that analyzes websites and predicts their safety level before users interact with potentially unsafe links.

The system extracts **50+ URL, host, and webpage-content features** and uses multiple machine learning models combined through a **weighted ensemble** to detect suspicious and potentially malicious websites. ClickSafe also uses **SHAP explainability** to show the key features influencing each prediction.

---

## Key Features

* **Dynamic Website Analysis**
  Extracts 50+ lexical, URL, host/domain, and webpage-content features.

* **Machine Learning Detection**
  Uses an ensemble of:

  * Random Forest
  * XGBoost
  * Gradient Boosting
  * Extra Trees

* **Weighted Ensemble Prediction**
  Combines predictions from multiple models to improve robustness and generalization.

* **5-Level Risk Categorization**

  * 🟢 **Safe** — <20%
  * 🟢 **Very Low Risk** — 20–30%
  * 🟡 **Moderate Risk** — 30–50%
  * 🟠 **Unsafe** — 50–80%
  * 🔴 **Danger** — ≥80%

* **SHAP-Based Explainability**
  Provides feature-level explanations showing which characteristics contributed to the prediction.

* **Chrome Extension Interface**
  Provides a user-friendly popup for viewing website safety predictions and risk details.

* **Interactive Analytics**
  Displays prediction information and feature-level insights through visualizations.

---

## System Architecture

```text
                    ┌──────────────────────┐
                    │    Chrome Browser    │
                    │   + ClickSafe        │
                    │      Extension       │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │     URL Processing   │
                    └──────────┬───────────┘
                               │
                               ▼
              ┌─────────────────────────────────┐
              │       Feature Extraction        │
              │                                 │
              │  • URL / Lexical Features      │
              │  • Host / Domain Features      │
              │  • Webpage Content Features    │
              │  • 50+ Features                │
              └───────────────┬─────────────────┘
                              │
                              ▼
              ┌─────────────────────────────────┐
              │       ML Model Ensemble         │
              │                                 │
              │  • Random Forest               │
              │  • XGBoost                     │
              │  • Gradient Boosting           │
              │  • Extra Trees                 │
              └───────────────┬─────────────────┘
                              │
                              ▼
                    ┌──────────────────────┐
                    │ Weighted Prediction  │
                    └──────────┬───────────┘
                               │
                    ┌──────────┴───────────┐
                    ▼                      ▼
          ┌──────────────────┐   ┌──────────────────┐
          │ Risk Assessment  │   │ SHAP Explanation │
          └────────┬─────────┘   └────────┬─────────┘
                   │                      │
                   └──────────┬───────────┘
                              ▼
                    ┌──────────────────────┐
                    │ ClickSafe Extension  │
                    │  Risk + Explanation  │
                    └──────────────────────┘
```

---

## Model Performance

The weighted ensemble achieved the following results on the test data:

| Metric        |      Score |
| ------------- | ---------: |
| **Accuracy**  | **91.36%** |
| **Precision** |  **92.4%** |
| **Recall**    |  **89.2%** |
| **F1-Score**  |  **90.7%** |
| **ROC-AUC**   | **0.9744** |

Among the individual tuned models, XGBoost achieved an accuracy of **91.72%**.

---

## Features

ClickSafe uses three major categories of features.

### 1. URL / Lexical Features

Examples include:

* URL length
* Number of dots
* Number of subdomains
* Number of URL parameters
* Digit ratio
* URL depth
* HTTPS usage
* URL shortening
* Suspicious prefixes/suffixes
* Double-slash patterns
* Uncommon TLDs

### 2. Host / Domain Features

Examples include:

* Domain age
* Domain registration length
* IP address usage
* Number of hyphens
* Hostname length
* Number of subdomains
* Numeric domain detection
* Domain misspelling
* Non-standard ports
* TLD-related features

### 3. Webpage Content Features

Examples include:

* Number of hyperlinks
* External hyperlink ratio
* External redirection ratio
* Links inside HTML tags
* Domain presence in webpage title
* Internal/external media ratios
* External CSS count
* Phishing hints
* Safe-anchor indicators
* Domain/brand matching

---

## Machine Learning Pipeline

```text
Dataset
   │
   ▼
Data Cleaning
   │
   ▼
Feature Engineering
   │
   ▼
Missing Value Handling
   │
   ▼
Feature Selection
   │
   ▼
Train / Test Split
   │
   ▼
Model Training
   │
   ├── Random Forest
   ├── XGBoost
   ├── Gradient Boosting
   └── Extra Trees
   │
   ▼
Weighted Ensemble
   │
   ▼
Risk Prediction
   │
   ▼
SHAP Explanation
```

---

## Project Structure

```text
ClickSafe-DynamicWebSafety/
│
├── app.py
├── requirements.txt
│
├── chrome-extension/
│   ├── manifest.json
│   ├── popup.html
│   ├── popup.css
│   ├── popup.js
│   └── ...
│
├── models/
│   └── [trained model files]
│
├── feature_extraction/
│   └── ...
│
├── templates/
│   └── ...
│
└── README.md
```

> **Note:** Some trained `.pkl` model files are too large to be stored directly on GitHub. They are provided separately through Google Drive.

---

## Download Trained Models

Download the required `.pkl` model files from Google Drive:

### [Download Trained Model Files](https://drive.google.com/drive/folders/1Q2MQkctnP1X_57hdfHzMT_n73Hjtw2zG?usp=sharing)

After downloading, place the `.pkl` files in the appropriate model directory before running the backend.

For example:

```text
ClickSafe-DynamicWebSafety/
└── models/
    ├── random_forest.pkl
    ├── xgboost.pkl
    ├── gradient_boosting.pkl
    └── extra_trees.pkl
```

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/sprahasingh/ClickSafe-DynamicWebSafety.git
cd ClickSafe-DynamicWebSafety
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Download the Trained Models

Download the `.pkl` files from the [Google Drive model repository](https://drive.google.com/drive/folders/1Q2MQkctnP1X_57hdfHzMT_n73Hjtw2zG?usp=sharing) and place them in the required model directory.

### 4. Run the Flask Backend

```bash
python app.py
```

The backend will start locally and handle website analysis requests from the Chrome extension.

### 5. Load the Chrome Extension

1. Open Google Chrome.
2. Navigate to:

```text
chrome://extensions/
```

3. Enable **Developer mode**.
4. Click **Load unpacked**.
5. Select the ClickSafe Chrome extension directory.
6. Ensure the Flask backend is running.
7. Open a website and use the ClickSafe extension to view its risk assessment.

---

## How ClickSafe Works

1. The user visits or analyzes a website through the Chrome extension.
2. ClickSafe processes the URL and associated webpage information.
3. More than 50 URL, host, and content-based features are extracted.
4. Multiple machine learning models generate predictions.
5. The weighted ensemble combines the model predictions.
6. The system assigns a risk level to the website.
7. SHAP identifies the features contributing to the prediction.
8. The extension displays the risk level and supporting insights to the user.

---

## Technologies Used

| Technology              | Purpose                    |
| ----------------------- | -------------------------- |
| **Python**              | Backend and ML pipeline    |
| **Flask**               | Backend API                |
| **scikit-learn**        | Machine learning models    |
| **XGBoost**             | Gradient boosting model    |
| **SHAP**                | Model explainability       |
| **HTML/CSS/JavaScript** | Chrome extension interface |
| **Chrome APIs**         | Browser integration        |
| **Joblib / Pickle**     | Model serialization        |
| **Git/GitHub**          | Version control            |

---

## Dataset

The project uses website data collected from multiple sources, including:

* Kaggle
* PhishTank
* Government websites
* Custom crawling

The dataset contains **100,000+ instances** and **50+ features**.

The final dataset is approximately balanced between:

* **Safe:** 51.74%
* **Unsafe:** 48.26%

The machine learning pipeline uses an **80/20 train-test split**, with a validation portion used during model tuning.

---

## Explainability with SHAP

ClickSafe uses **SHAP (SHapley Additive exPlanations)** to make model predictions more interpretable.

Instead of only showing:

```text
Website: UNSAFE
```

ClickSafe can identify characteristics that contributed to the prediction, such as:

* Suspicious URL patterns
* Domain age
* Number of subdomains
* External hyperlinks
* Redirection behavior
* Suspicious keywords
* URL length

This provides users with additional context behind the model's prediction.

---

## Project Results

ClickSafe achieved:

* **91.36% overall accuracy**
* **92.4% precision**
* **89.2% recall**
* **90.7% F1-score**
* **0.9744 ROC-AUC**
* **50+ engineered features**
* **4 ML classifiers combined through a weighted ensemble**
* **5 user-facing website risk levels**
* **SHAP-based prediction explanations**

---

## Future Improvements

Potential future enhancements include:

* Deep learning models for webpage-content analysis
* Real-time threat-intelligence integration
* Behavioral website analysis
* Multimodal detection using text, images, and URL characteristics
* Cloud deployment and scalable APIs
* Continuous learning from user feedback
* Cross-browser support
* Mobile browser support

---

## Disclaimer

ClickSafe is an academic machine-learning project intended to assist with website-risk assessment. Its predictions should not be treated as a guarantee that a website is safe or malicious.

---

## Author

**Spraha Singh**

[GitHub](https://github.com/sprahasingh)
