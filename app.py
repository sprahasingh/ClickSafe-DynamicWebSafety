from flask import Flask, request, jsonify
import pandas as pd
from joblib import load
from flask_cors import CORS
from feature_extract import extract_features
import logging
import os
import shutil
import threading
import numpy as np
import shap

# Clean up __pycache__
shutil.rmtree('__pycache__', ignore_errors=True)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "chrome-extension://ecpganmhndnnnnogcpnlafcdnekoickd"}})

# Path for saving data
DATA_PATH = 'new_data.csv'
columns = [
    'url', 'status', 'actual', 'google_index', 'nb_hyperlinks', 'web_traffic', 'nb_www',
    'ratio_extHyperlinks', 'domain_age', 'phish_hints', 'safe_anchor',
    'ratio_digits_url', 'length_url', 'avg_word_path', 'length_hostname',
    'ratio_extRedirection', 'longest_words_raw', 'length_words_raw',
    'nb_dots', 'links_in_tags', 'domain_registration_length', 'nb_slash',
    'domain_in_title', 'avg_words_raw', 'shortest_word_path', 'ip',
    'nb_hyphens', 'avg_word_host', 'ratio_digits_host', 'ratio_intMedia',
    'nb_qm', 'domain_with_copyright', 'ratio_extMedia', 'nb_extCSS',
    'nb_subdomains', 'domain_in_brand', 'nb_and', 'nb_special_characters',
    'https_in_url', 'https_in_domain', 'has_prefix_suffix', 'depth_of_url',
    'count_parameters', 'uncommon_tld', 'is_numeric_domain',
    'domain_misspelling', 'qty_double_slash_path', 'non_standard_port',
    'abnormal_url', 'url_shortened', 'tld_count_in_url',
    'tld_count_in_domain', 'tilde_count', 'asterisk_count', 'dollar_count',
    'file_length', 'repeated_letters', 'repeated_vowels', 'vowel_repetition_ratio'
]

# Ensure the CSV file exists with correct columns
if not os.path.exists(DATA_PATH):
    pd.DataFrame(columns=columns).to_csv(DATA_PATH, index=False)
    print("New file created")

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load models
logging.info("Loading models...")
models = {
    # 'randomforestclassifier': load("randomforestclassifier.pkl"),
    'xgbclassifier': load("xgbclassifier.pkl"),
    'gradientboostingclassifier': load("gradientboostingclassifier.pkl"),
    # 'extratreesclassifier': load("extratreesclassifier.pkl"),
}
logging.info("Models loaded successfully.")

# Load scaler
logging.info("Loading scaler...")
scaler = load('minmax_scaler.pkl')
logging.info("Scaler loaded successfully.")

# def get_shap_explanations(model, features):
#     """
#     Calculate SHAP values for the given model and features.
#     Returns the top 15 feature contributions.
#     """
#     explainer = shap.TreeExplainer(model)
#     shap_values = explainer.shap_values(features)
#     shap_contributions = pd.DataFrame({
#         'feature': features.columns,
#         'shap_value': shap_values[1][0]  # Assuming class 1 corresponds to unsafe
#     })
#     shap_contributions['direction'] = shap_contributions['shap_value'].apply(
#         lambda x: 'safe' if x < 0 else 'unsafe'
#     )
#     shap_contributions = shap_contributions.sort_values(
#         by='shap_value', key=abs, ascending=False
#     ).head(15)
#     return shap_contributions.to_dict(orient='records')

def get_shap_explanations(model, features):
    """
    Calculate SHAP values for the given model and features.
    Returns the top 10 contributors for both safe and unsafe classes.
    """
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(features)

    # Debug log for SHAP values shape
    logging.info(f"SHAP values shape: {np.array(shap_values).shape}")

    # Extract SHAP values for the "unsafe" class (class 1)
    shap_values_class = shap_values[0][:, 1]  # Access last dimension for class 1

    # Debug log for full SHAP values
    logging.info(f"Full SHAP values for class 1: {shap_values_class}")

    contributions = pd.DataFrame({
        'feature': features.columns,
        'shap_value': shap_values_class,
    })

    # Separate positive and negative contributions
    contributions['direction'] = contributions['shap_value'].apply(
        lambda x: 'safe' if x < 0 else 'unsafe'
    )

    # Sort by absolute SHAP value and select the top 10 for each category
    contributions = contributions.sort_values(by='shap_value', key=abs, ascending=False)
    top_safe = contributions[contributions['direction'] == 'safe'].head(10)
    top_unsafe = contributions[contributions['direction'] == 'unsafe'].head(10)

    # Debug log for top contributors
    logging.info(f"Top 10 safe contributors: {top_safe}")
    logging.info(f"Top 10 unsafe contributors: {top_unsafe}")

    return {
        'top_safe': top_safe.to_dict(orient='records'),
        'top_unsafe': top_unsafe.to_dict(orient='records')
    }



@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    originalUrl = data.get("url")
    if not originalUrl:
        return jsonify({'error': 'URL is required'}), 400

    logging.info(f"Received URL: {originalUrl}")

    # Extract features
    logging.info("Extracting features...")
    try:
        df_features = extract_features(originalUrl)
        logging.info("Feature extraction successful.")
    except Exception as e:
        logging.error(f"Feature extraction failed for URL '{originalUrl}': {str(e)}")
        return jsonify({'error': 'Feature extraction failed', 'details': str(e)}), 500

    # Select and scale features
    feature_columns = columns[3:]  # Skip 'url', 'status', and 'actual'
    if not set(feature_columns).issubset(df_features.columns):
        logging.error("Feature extraction produced incorrect columns.")
        return jsonify({'error': 'Feature extraction produced incorrect columns'}), 400

    logging.info("Scaling features...")
    df_features_scaled = pd.DataFrame(scaler.transform(df_features[feature_columns]), columns=feature_columns)

    # Get probabilities from models
    logging.info("Calculating probabilities from models...")
    model_probabilities = {}
    for model_name, model in models.items():
        try:
            probability = model.predict_proba(df_features_scaled)[0][1]  # Probability of phishing
            model_probabilities[model_name] = float(probability)  # Convert to float
            logging.info(f"{model_name} probability: {probability:.4f}")
        except Exception as e:
            model_probabilities[model_name] = None
            logging.error(f"Error with model {model_name}: {str(e)}")

    # Calculate mean probability
    valid_probabilities = [prob for prob in model_probabilities.values() if prob is not None]
    final_probability = float(np.mean(valid_probabilities)) if valid_probabilities else None
    logging.info(f"Mean probability of phishing: {final_probability:.4f}" if final_probability is not None else "Failed to compute mean probability.")
    # logging.info(f"Features: {df_features.iloc[0].to_dict()}")

    # Generate SHAP explanations
    try:
        shap_explanations = get_shap_explanations(models['randomforestclassifier'], df_features_scaled)
    except Exception as e:
        logging.error(f"SHAP explanation generation failed: {str(e)}")
        shap_explanations = []
    
    # Send final probability back to the extension
    response = jsonify({
        'final_probability': final_probability,
        'shap_explanations': shap_explanations
    })

    # Display prediction result to user via extension
    logging.info("Displaying prediction result to extension.")
    
    # Start thread to prompt for actual prediction input and save data
    threading.Thread(target=prompt_and_save_data, args=(originalUrl, df_features, final_probability)).start()

    return response

def prompt_and_save_data(url, df_features, final_probability):
    # Prompt user for actual prediction (0 or 1)
    actual_prediction = input(f"Please enter the actual prediction for URL '{url}' (0 for safe, 1 for phishing, -1 for other): ")
    while actual_prediction not in ['0', '1', '-1']:
        actual_prediction = input("Invalid input. Please enter 0 for safe, 1 for phishing or -1 for other: ")

    # Convert actual prediction to integer and save to DataFrame
    df_features['actual'] = int(actual_prediction)
    logging.info(f"User entered actual prediction: {actual_prediction}")

    # Save data if new
    save_data_if_new(url, df_features, final_probability)

def save_data_if_new(url, df_features, final_probability):
    try:
        # Load existing data
        existing_data = pd.read_csv(DATA_PATH)

        # Check if the URL is already present
        if url in existing_data['url'].values:
            logging.info(f"{url} is already present in the dataset.\n")
        else:
            # Prepare and append new data row with the specified column order
            row_data = {col: df_features.iloc[0].get(col, None) for col in columns[3:]}
            row_data.update({"url": url, "status": final_probability, "actual": df_features['actual'].values[0]})
            pd.DataFrame([row_data], columns=columns).to_csv(DATA_PATH, mode='a', header=False, index=False)
            logging.info(f"{url} has been added to the dataset.\n")
    except Exception as e:
        logging.error(f"Failed to save data for {url}. Reason: {str(e)}\n")

if __name__ == '__main__':
    logging.info("Starting Flask app...")
    app.run(debug=False)
