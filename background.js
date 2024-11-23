chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "checkURL") {
    const features = extractFeaturesFromURL(request.url);

    predictFromBackend(features)
      .then((result) => {
        const rfPrediction = result.random_forest_prediction;

        let message =
          rfPrediction === 1
            ? `The URL ${request.url} is phishing!`
            : `The URL ${request.url} is legitimate.`;

        sendResponse({ result: message });
      })
      .catch((error) => {
        console.error("Error:", error);
        sendResponse({ result: "Error: Could not process the URL." });
      });

    return true; // Keep the message channel open for async response
  }
});

function extractFeaturesFromURL(url) {
  const features = [];

  const ipPattern = /(\d{1,3}\.){3}\d{1,3}/;
  const haveIP = ipPattern.test(url) ? 1 : 0;
  features.push(haveIP);

  const haveAt = url.includes("@") ? 1 : 0;
  features.push(haveAt);

  const urlLength = url.length;
  features.push(urlLength);

  const urlObj = new URL(url);
  const depth = urlObj.pathname
    .split("/")
    .filter((segment) => segment.length > 0).length;
  features.push(depth);

  const domain = urlObj.hostname;
  const prefixSuffix = domain.includes("-") ? 1 : 0;
  features.push(prefixSuffix);

  const webTraffic = 0; // Placeholder
  features.push(webTraffic);

  const iFrame = 0; // Placeholder
  features.push(iFrame);

  const mouseOver = 0; // Placeholder
  features.push(mouseOver);

  const webForwards = 0; // Placeholder
  features.push(webForwards);

  return features;
}

async function predictFromBackend(features) {
  const response = await fetch("http://127.0.0.1:5000/predict", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ features: features }),
  });

  const data = await response.json();
  return data;
}
