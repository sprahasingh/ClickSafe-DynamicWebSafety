document.getElementById("check-button").addEventListener("click", function () {
  // Hide result boxes and analytics section when a button is pressed
  document.getElementById("result").style.display = "none";
  document.getElementById("tab-result").style.display = "none";
  document.getElementById("analytics-section").style.display = "none";
  document.getElementById("analytics-section-tab").style.display = "none";

  let url = document.getElementById("website-input").value.trim(); // Trim spaces from input
  let originalUrl = url; // Store the original URL

  // Clear results and loading indicators for both buttons
  document.getElementById("result").innerText = "";
  document.getElementById("tab-result").innerText = "";
  document.getElementById("loading").style.display = "none";
  document.getElementById("loading-tab").style.display = "none";

  // Reset border color to original
  resetContainerBorder();

  // Check if URL input is empty
  if (!url) {
    document.getElementById("result").innerText = "Please enter a URL.";
    document.getElementById("result").style.display = "block";
    document.getElementById("result").style.color = "red";
    return;
  }

  // Prepend 'http://' if the URL does not start with 'http://' or 'https://'
  if (!url.startsWith("http://") && !url.startsWith("https://")) {
    url = "http://" + url; // Modify the URL for prediction
  }

  // Handle search engine URLs
  const trimmedUrl = handleSearchEngineUrls(url);
  if (trimmedUrl) {
    // Use the trimmed URL for prediction
    url = trimmedUrl.baseUrl;
  }

  // Validate the URL
  if (!isValidURL(url)) {
    document.getElementById("result").innerText = "Please enter a valid URL.";
    document.getElementById("result").style.display = "block";
    document.getElementById("result").style.color = "red";
    return;
  }

  // Show loading message for the URL check
  document.getElementById("loading").style.display = "block";

  // Make prediction by sending the URL to the backend
  makePrediction(url).then((data) => {
    // Hide loading message
    document.getElementById("loading").style.display = "none";

    // Get final probability and final prediction
    const finalProbability = data.final_probability.toFixed(2);
    const shapExplanations = data.shap_explanations;

    // Define message based on probability
    let message;
    let color;

    if (finalProbability < 0.2) {
      message = `${originalUrl} is assessed as <b>safe</b> to access.<br> **Enjoy browsing!**`;
      color = "#1E8449"; // Safe - Green
    } else if (finalProbability >= 0.2 && finalProbability < 0.3) {
      message = `${originalUrl} is assessed as <b>very low risk</b>.<br> **Likely safe to access.**`;
      color = "#2E7D32"; // Very Low Risk - Dark Green
    } else if (finalProbability >= 0.3 && finalProbability < 0.5) {
      message = `<b>Caution:</b> ${originalUrl} has a <b>moderate risk</b> with a risk probability of ${Math.round(
        finalProbability * 100
      )}%.<br> **Verify the source before proceeding.**`;
      color =
        finalProbability < 0.3
          ? "#558B2F"
          : finalProbability < 0.4
          ? "#9E9D24"
          : "#F9A825"; // Gradient from Greenish Yellow to Yellow
    } else if (finalProbability >= 0.5 && finalProbability < 0.8) {
      message = `<b>Warning:</b> ${originalUrl} is assessed as <b>unsafe</b> with a risk probability of ${Math.round(
        finalProbability * 100
      )}%.<br> **Avoid sharing sensitive information.**`;
      color =
        finalProbability < 0.6
          ? "#F57F17"
          : finalProbability < 0.7
          ? "#EF6C00"
          : "#D84315"; // Gradient from Orange to Dark Orange
    } else {
      message = `<b>Danger:</b> ${originalUrl} is identified as <b>unsafe</b> with a very high risk.<br> **Avoid accessing this link or sharing any information.**`;
      color = finalProbability < 0.9 ? "#C62828" : "#B71C1C"; // High Risk - Red
    }

    // Update the result element with HTML content
    document.getElementById("result").innerHTML = message;
    document.getElementById("result").style.display = "block";
    document.getElementById("result").style.color = color;
    document.querySelector(".container").style.borderColor = color;
    // Show the analytics button after the result
    document.getElementById("analytics-section").style.display = "inline-block";
    // Save SHAP explanations for analytics
    saveAnalytics(shapExplanations);
  });
});

// Event listener for the Check Analytics button (Check Website)
document
  .getElementById("analytics-button")
  .addEventListener("click", function () {
    displayAnalytics("analytics-section");
  });

function saveAnalytics(shapExplanations) {
  console.log("SHAP Explanations Data:", shapExplanations); // Debug log
  window.analyticsData = shapExplanations;
}

function displayAnalytics() {
  if (
    !window.analyticsData ||
    (!window.analyticsData.top_safe.length &&
      !window.analyticsData.top_unsafe.length)
  ) {
    alert("No analytics data available.");
    return;
  }

  // Open a new popup window for analytics
  const popup = window.open(
    "analytics.html?data=" +
      encodeURIComponent(JSON.stringify(window.analyticsData)),
    "Analytics",
    "width=900,height=600,scrollbars=yes"
  );

  if (!popup) {
    alert("Please allow popups to view the analytics.");
  }
}

// Event listener for checking the active tab
document
  .getElementById("check-tab-button")
  .addEventListener("click", function () {
    // Hide result boxes when a button is pressed
    document.getElementById("result").style.display = "none";
    document.getElementById("tab-result").style.display = "none";

    // Clear the analytics button
    document.getElementById("analytics-section").style.display = "none";
    document.getElementById("analytics-section-tab").style.display = "none";

    // Clear results and loading indicators for both buttons
    document.getElementById("result").innerText = "";
    document.getElementById("tab-result").innerText = "";
    document.getElementById("loading").style.display = "none";
    document.getElementById("loading-tab").style.display = "none";

    // Reset border color to original
    resetContainerBorder();

    // Clear the URL input box
    document.getElementById("website-input").value = "";

    chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
      let activeTab = tabs[0];
      let activeTabURL = activeTab.url;

      // Check if the active tab URL is empty or a Chrome internal URL
      if (
        !activeTabURL ||
        activeTabURL.startsWith("chrome://") ||
        activeTabURL === "about:blank"
      ) {
        document.getElementById("tab-result").innerText =
          "This is a Chrome internal URL.";
        document.getElementById("tab-result").style.display = "block";
        document.getElementById("tab-result").style.color = "red";
        return;
      }

      // Handle search engine URLs for active tab
      const trimmedTabUrl = handleSearchEngineUrls(activeTabURL);
      const urlToCheck = trimmedTabUrl ? trimmedTabUrl.baseUrl : activeTabURL; // Use the trimmed URL or the original one

      // Check if the active tab URL is valid but not empty
      // if (!isValidURL(urlToCheck)) {
      //   document.getElementById("tab-result").innerText =
      //     "Please enter a valid URL for the active tab.";
      //   document.getElementById("tab-result").style.display = "block";
      //   document.getElementById("tab-result").style.color = "red";
      //   return;
      // }

      // Show loading message for the tab check
      document.getElementById("loading-tab").style.display = "block";

      // Make prediction by sending the active tab URL to the backend
      makePrediction(urlToCheck).then((data) => {
        // Hide loading message
        document.getElementById("loading-tab").style.display = "none";

        // Get final probability and final prediction
        const finalProbability = data.final_probability.toFixed(2);
        const shapExplanations = data.shap_explanations;

        // Define message based on probability
        let message;
        let color;

        if (finalProbability < 0.2) {
          message = `${activeTabURL} is assessed as <b>safe</b> to access.<br> **Enjoy browsing!**`;
          color = "#1E8449"; // Safe - Green
        } else if (finalProbability >= 0.2 && finalProbability < 0.3) {
          message = `${activeTabURL} is assessed as <b>very low risk</b>.<br> **Likely safe to access.**`;
          color = "#2E7D32"; // Very Low Risk - Dark Green
        } else if (finalProbability >= 0.3 && finalProbability < 0.5) {
          message = `<b>Caution:</b> ${activeTabURL} has a <b>moderate risk</b> with a risk probability of ${Math.round(
            finalProbability * 100
          )}%.<br> **Verify the source before proceeding.**`;
          color =
            finalProbability < 0.3
              ? "#558B2F"
              : finalProbability < 0.4
              ? "#9E9D24"
              : "#F9A825"; // Gradient from Greenish Yellow to Yellow
        } else if (finalProbability >= 0.5 && finalProbability < 0.8) {
          message = `<b>Warning:</b> ${activeTabURL} is assessed as <b>unsafe</b> with a risk probability of ${Math.round(
            finalProbability * 100
          )}%.<br> **Avoid sharing sensitive information.**`;
          color =
            finalProbability < 0.6
              ? "#F57F17"
              : finalProbability < 0.7
              ? "#EF6C00"
              : "#D84315"; // Gradient from Orange to Dark Orange
        } else {
          message = `<b>Danger:</b> ${activeTabURL} is identified as <b>unsafe</b> with a very high risk.<br> **Avoid accessing this link or sharing any information.**`;
          color = finalProbability < 0.9 ? "#C62828" : "#B71C1C"; // High Risk - Red
        }

        // Update the result element with HTML content
        document.getElementById("tab-result").innerHTML = message;
        document.getElementById("tab-result").style.display = "block";
        document.getElementById("tab-result").style.color = color;
        document.querySelector(".container").style.borderColor = color;
        // Show the analytics button after the result
        // Show the analytics button after the result
        document.getElementById("analytics-section-tab").style.display =
          "inline-block";
        // Save SHAP explanations for analytics
        saveAnalytics(shapExplanations);
      });
    });
  });

// Event listener for the Check Analytics button (Check Tab)
document
  .getElementById("analytics-button-tab")
  .addEventListener("click", function () {
    displayAnalytics("analytics-section-tab");
  });

// Function to reset the container border color
function resetContainerBorder() {
  document.querySelector(".container").style.borderColor = "#ddd"; // Default border color
  document.getElementById("result").style.color = "#333"; // Default text color
}

function isValidURL(url) {
  const urlPattern = new RegExp(
    "^(https?:\\/\\/)" + // protocol
      "((([a-zA-Z\\d]([a-zA-Z\\d-]*[a-zA-Z\\d])*)\\.)+[a-zA-Z]{2,}|" + // domain name
      "((\\d{1,3}\\.){3}\\d{1,3}))" + // OR IP (v4) address
      "(\\:\\d+)?(\\/[-a-zA-Z\\d%@_.~+&:]*)*" + // port and path
      "(\\?[;&a-zA-Z\\d%@_.,~+&:=|!-]*)?" + // query string
      "(\\#[-a-zA-Z\\d%@_.,~+&:=|!]*)?$", // fragment locator
    "i"
  );

  // Check for spaces in the URL (not allowed)
  return urlPattern.test(url) && !/\s/.test(url);
}

// Function to make prediction by sending the URL to the backend
async function makePrediction(url) {
  const response = await fetch("http://127.0.0.1:5000/predict", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ url: url }), // Send the URL in the request body
  });

  const data = await response.json();
  return data; // Return the entire data object containing final prediction and probability
}

function handleSearchEngineUrls(url) {
  const searchEngines = [
    "google.com",
    "bing.com",
    "yahoo.com",
    "duckduckgo.com",
    "baidu.com",
    "ask.com",
    "aol.com",
  ];

  try {
    let parsedUrl = new URL(url);
    let baseUrl = parsedUrl.origin + parsedUrl.pathname; // Retain the scheme and pathname

    // Check if the base URL is a search engine
    if (searchEngines.some((engine) => parsedUrl.hostname.includes(engine))) {
      return { baseUrl: baseUrl }; // Return the base URL
    }
  } catch (error) {
    console.error("Invalid URL:", url); // Log error for invalid URL
  }

  return null; // Return null if it's not a search engine URL
}

// Event listener for the Clear button
document.getElementById("clear-button").addEventListener("click", function () {
  // Clear the input field
  document.getElementById("website-input").value = "";

  // Clear the analytics button
  document.getElementById("analytics-section").style.display = "none";
  document.getElementById("analytics-section-tab").style.display = "none";

  // Clear all results and loading messages
  document.getElementById("result").style.display = "none";
  document.getElementById("tab-result").style.display = "none";
  document.getElementById("loading").style.display = "none";
  document.getElementById("loading-tab").style.display = "none";

  // Reset the result text
  document.getElementById("result").innerText = "";
  document.getElementById("tab-result").innerText = "";

  // Reset container border color to default
  resetContainerBorder();
});

// SUCCESS

// Close the popup window when the close button is clicked
document.getElementById("close-button").addEventListener("click", function () {
  window.close();
});
