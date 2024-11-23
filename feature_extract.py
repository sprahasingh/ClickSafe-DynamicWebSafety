import re
import requests
from urllib.parse import urlparse, urljoin
import socket
import whois
from bs4 import BeautifulSoup
import pandas as pd
import time
import logging
import random
import os

TIME_LIMIT = 3  # Define your time limit in seconds for external requests

def get_google_index(url):
    parsed_url = urlparse(url)
    USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0.2 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 11; Pixel 5 Build/RQ1A.211205.012) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.1 Mobile/15E148 Safari/604.1",
  ]
    # Avoid using HTTP in the query to prevent issues with the protocol
    if parsed_url.scheme not in ['http', 'https']:
        return -1  # Invalid URL scheme
    try:
        # Use a random user-agent for the request
        headers = {'User-Agent': random.choice(USER_AGENTS)}
        response = requests.get(f"https://www.google.com/search?q=site:{parsed_url.netloc}", headers=headers, timeout=TIME_LIMIT)
        # Check for success
        if response.status_code == 200:
            # Check if the page contains the URL (this might be a rough indicator of indexing)
            if url in response.text:
                return 1  # URL is indexed
            else:
                return 0  # URL is not indexed
        else:
            # Handle other HTTP errors gracefully
            return -1
    except requests.exceptions.RequestException as e:
        return -1

def get_web_traffic(url):
    try:
        # Replace with the actual SimilarWeb page for the desired website
        response = requests.get(f'https://www.similarweb.com/website/{url}/')
        response.raise_for_status()  # Check for request errors
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        # Locate the traffic data (modify according to the actual HTML structure)
        traffic_data = soup.find('span', class_='totalVisits')  # Example class
        # Extract the traffic number (modify according to actual HTML structure)
        if traffic_data:
            traffic = traffic_data.get_text(strip=True)
            return int(traffic.replace(',', ''))  # Convert to integer
        else:
            return 0  # Default to 0 if no data is found
    except Exception as e:
        return 0  # Default to 0 if an exception occurs

def get_domain_age(url):
    try:
        domain = urlparse(url).netloc
        # Handle localhost specifically
        if domain == "localhost":
            return 0  # Or return 0 depending on your requirements
        domain_info = whois.whois(domain)
        # Check for valid creation and expiration dates
        if domain_info.creation_date and domain_info.expiration_date:
            creation_date = domain_info.creation_date if not isinstance(domain_info.creation_date, list) else domain_info.creation_date[0]
            expiration_date = domain_info.expiration_date if not isinstance(domain_info.expiration_date, list) else domain_info.expiration_date[0]
            return (expiration_date - creation_date).days
        return 365  # Unable to determine age, return None
    except Exception as e:
        return -1  # Return None if an error occurs

def extract_longest_words_raw(url):
    # Find all words consisting only of alphabetic characters
    words = re.findall(r'\w+', url)
    # Return length of the longest word or 0 if no valid words found
    return len(max(words, key=len)) if words else 0
    return 0  # Return 0 if no words found

def extract_length_words_raw(url):
    # Define a set of terms to exclude
    exclude_terms = {"http", "https", "ftp", "www", "com", "co", "uk", "org", "net", "gov", "edu", "info", "localhost"}
    # Find all words
    words = re.findall(r'\w+', url)
    # Filter out excluded terms and sum the lengths of valid words
    valid_words = [word for word in words if word.lower() not in exclude_terms]
    return sum(len(word) for word in valid_words)


def extract_links_in_tags(url, timeout=10):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()  # Raise an error for bad responses
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a')
        return len(links)
    except requests.ConnectionError:
        return -1
    except requests.Timeout:
        return -1
    except requests.RequestException as e:
        return -1

def extract_domain_registration_length(url):
    try:
        domain_info = whois.whois(urlparse(url).netloc)
        if domain_info.creation_date and domain_info.expiration_date:
            creation_date = domain_info.creation_date if not isinstance(domain_info.creation_date, list) else domain_info.creation_date[0]
            expiration_date = domain_info.expiration_date if not isinstance(domain_info.expiration_date, list) else domain_info.expiration_date[0]
            return (expiration_date - creation_date).days
        return 365  # Default median registration length in days
    except whois.parser.PywhoisError as e:
        return 0  # Return None or 0 to indicate failure
    except Exception as e:
        return 0  # Return None or 0 to indicate failure

def extract_ratio_intMedia(url):
    try:
        # Fetch HTML content with a custom User-Agent
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=TIME_LIMIT)
        response.raise_for_status()  # Raise exception for bad status
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        # Find all media tags
        all_media = soup.find_all(['img', 'video', 'audio'])
        # Calculate the base domain for comparison
        base_domain = urlparse(url).netloc
        # Filter internal media by checking domain of 'src' attribute, handling relative URLs
        internal_media = [
            tag for tag in all_media
            if urlparse(urljoin(url, tag.get('src', ''))).netloc == base_domain
        ]
        # Return ratio of internal media to total media
        return len(internal_media) / len(all_media) if all_media else 0
    except requests.RequestException:
        return -1  # Return -1 for any error

def extract_ratio_extMedia(url):
    try:
        # Fetch HTML content with a custom User-Agent
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=TIME_LIMIT)
        response.raise_for_status()  # Raise exception for bad status
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        # Find all media tags
        all_media = soup.find_all(['img', 'video', 'audio'])
        # Calculate the base domain for comparison
        base_domain = urlparse(url).netloc
        # Filter external media by checking domain of 'src' attribute, handling relative URLs
        external_media = [
            tag for tag in all_media
            if tag.get('src') and urlparse(urljoin(url, tag.get('src', ''))).netloc != base_domain
        ]
        # Return ratio of external media to total media
        return len(external_media) / len(all_media) if all_media else 0
    except requests.RequestException:
        return -1  # Return -1 for any error

def extract_ip_feature(url):
    features = {}
    parsed_url = urlparse(url)
    hostname = parsed_url.netloc
    # Regular expression to match IPv4 addresses
    ip_pattern = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")
    # Check if the hostname is an IP address
    if ip_pattern.match(hostname):
        return 1  # URL contains IP address
    else:
        try:
            # Resolve the hostname to an IP address
            socket.gethostbyname(hostname)
            return 0  # URL does not contain IP address
        except socket.gaierror:
            return -1  # Invalid domain or cannot resolve

def extract_hyperlink_count(url):
    try:
        response = requests.get(url, timeout=TIME_LIMIT)
        # Improved regex to match href attributes in different contexts
        hyperlinks = re.findall(r'<a\s+[^>]*href=["\']([^"\']+)["\']', response.text)
        return len(hyperlinks)
    except Exception as e:
        return -1  # Return -1 if there's an error

def count_special_characters(url):
    try:
        special_chars = re.findall(r'[@!$%^&*(),?":{}|<>]', url)
        return len(special_chars)
    except Exception:
        return -1

def https_in_url(url):
    try:
        return 1 if urlparse(url).scheme == 'https' else 0
    except Exception:
        return -1

def https_in_domain(url):
    try:
        domain = urlparse(url).netloc
        return 1 if 'https' in domain else 0
    except Exception:
        return -1

def has_prefix_suffix(url):
    try:
        domain = urlparse(url).netloc
        return 1 if '-' in domain else 0
    except Exception:
        return -1

def depth_of_url(url):
    try:
        path = urlparse(url).path
        parts = [p for p in path.split('/') if p]  # Remove empty parts caused by extra slashes
        # Check if the last part is a file (has an extension)
        if parts and os.path.splitext(parts[-1])[1]:  # If last part has an extension, exclude it from depth count
            return len(parts) - 1
        return len(parts)
    except Exception:
        return -1

def count_parameters(url):
    try:
        query = urlparse(url).query
        return len(query.split('&')) if query else 0
    except Exception:
        return -1

def uncommon_tld(url):
    # Basic set of the most common TLDs
    common_tlds = [
    '.com',    # Most common for commercial businesses
    '.org',    # Commonly used by non-profit organizations
    '.net',    # Often used by internet service providers and tech companies
    '.gov',    # Official government websites
    '.edu',    # Educational institutions (universities, colleges)
    '.mil',    # Military institutions
    '.info',   # Information-related websites, often legitimate
    '.co',     # Increasingly used by companies
    '.us',     # United States-specific domains
    '.io',     # Tech startups and organizations
    '.biz',    # Business-related websites
    '.me',     # Personal websites
    '.dev',    # Development-related sites
    '.store',  # E-commerce websites
    '.health', # Health-related organizations
    '.name',   # Personal branding sites
    '.pro',    # Professional services
    '.jobs',   # Employment and job postings
    ]
    try:
        # Parse the TLD from the URL
        domain_parts = urlparse(url).netloc.split('.')
        if len(domain_parts) < 2:
            return -1  # Invalid TLD or domain
        # Extract the TLD
        tld = '.' + domain_parts[-1].lower()  # Convert to lowercase to handle cases like .COM
        # Mark as 0 for common TLDs, 1 for uncommon
        return 0 if tld in common_tlds else 1
    except Exception:
        return -1  # Return -1 if an exception occurs

def is_numeric_domain(url):
    try:
        # Parse the domain from the URL
        domain = urlparse(url).netloc
        # Split the domain into subdomains and the main domain part
        domain_parts = domain.split('.')
        # Check the main part of the domain for numeric-only characters
        if domain_parts[-2].isdigit():
            return 1  # Indicates a numeric domain
        else:
            return 0  # Indicates a non-numeric domain
    except Exception:
        return -1  # Return -1 in case of an error

def domain_misspelling(url, common_words=["google", "facebook", "fb", "amazon", "instagram", "insta", "twitter", "youtube", "yt", "shopify", "paypal", "linkedin", "microsoft", "apple"]):
    try:
        domain = urlparse(url).netloc.split('.')[0]
        # Regular expression to identify typical phishing patterns around brand names
        pattern = re.compile(r'\b(?:{})\b'.format('|'.join(common_words)), re.IGNORECASE)
        # Check if a brand name exists within the domain but isn't an exact match
        if pattern.search(domain):
            for word in common_words:
                # Match if domain contains the brand but is not exactly the brand
                if word in domain and domain != word:
                    # Check for likely phishing additions such as "my", "login", "secure", etc.
                    if any(prefix in domain for prefix in ["my", "login", "secure", "service", "page", "account", "help", "buy", "shop", "friends", "support", "team"]):
                        return 1
                    # Allow exact brand domains
                    elif domain == word:
                        return 0
            return 0  # No suspicious pattern found
        return 1  # Suspicious if unrelated to any known brand
    except Exception:
        return -1  # Error case

def qty_double_slash_path(url):
    try:
        path = urlparse(url).path
        count = path.count('//')
        return count
    except Exception:
        return -1

def extract_phishing_hints(url):
    # Initialize hints counter
    hints = 0
    # Convert URL to lowercase for consistent checks
    url_lower = url.lower()
    # List of common phishing hints
    phishing_indicators = [
        'login',       # Login page
        'secure',      # Secure pages often misused
        'verify',      # Verification processes
        'account',     # References to accounts
        'update',      # Requests for updates
        'confirm',     # Confirmation pages
        'alert',       # Alerts or warnings
        'suspend',     # Account suspension warnings
        'password',    # Password input requests
        'credentials',  # Credential requests
        'bank',        # Financial institutions
        'free',        # Often used in scams
        'offers',      # Special offers or deals
        'click',       # Clickbait
        'urgent',      # Urgent messages
        'porn',
        'x',
        'torrent'
    ]
    # Check for phishing indicators in the URL
    for indicator in phishing_indicators:
        if indicator in url_lower:
            hints += 1
    # Return the total count of phishing hints
    return hints

def calculate_ratio_extHyperlinks(url):
    # Parse base domain of the URL
    base_domain = urlparse(url).netloc.lower()
    try:
        # Fetch HTML content of the URL
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an error if the request failed
        html_content = response.text
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        # Find all anchor tags in the HTML
        all_links = soup.find_all('a', href=True)
        # Count external links by checking each anchor tag's href attribute
        ext_links = sum(1 for link in all_links if base_domain not in link['href'] and link['href'].startswith('http'))
        # Total links for ratio calculation
        total_links = len(all_links) or 1  # Avoid division by zero
        # Calculate ratio of external links to total links
        ratio_extHyperlinks = ext_links / total_links
        return ratio_extHyperlinks
    except requests.RequestException as e:
        return -1

def calculate_ratio_digits_url(url):
    # Check for empty URL to prevent division by zero
    if not url:
        return 0
    # Calculate the number of digits in the URL
    num_digits = sum(char.isdigit() for char in url)
    # Calculate the ratio of digits to the total length of the URL
    ratio_digits = num_digits / len(url) if len(url) > 0 else 0
    return ratio_digits

def count_dots(url):
    parsed_url = urlparse(url)
    return parsed_url.netloc.count('.')

def extract_length_hostname(url):
    # Parse the URL to extract the hostname
    parsed_url = urlparse(url)
    return len(parsed_url.hostname) if parsed_url.hostname else 0

def extract_safe_anchor(url):
    # Initialize the safe anchor score
    safe_anchor_score = 1  # Assume it's safe initially
    # Check if the URL starts with 'https'
    is_https = url.lower().startswith('https://')
    if not is_https:
        safe_anchor_score = 0  # Not secure if it doesn't start with https
    # List of known unsafe or suspicious domains
    unsafe_domains = [
    'example.com',        # Placeholder example
    'test.com',           # Placeholder example
    'phishingsite.com',   # Generic phishing site
    'malicious.com',      # Generic malicious site
    'suspicious.com',     # Generic suspicious site
    'fakebank.com',       # Known phishing site
    'secure-login.com',   # Common phishing keyword
    'login-page.com',     # Common phishing keyword
    'verify-account.com',  # Common phishing keyword
    'bank-update.com',    # Common phishing keyword
    'update-your-account.com',  # Common phishing keyword
    'account-login.com',  # Common phishing keyword
    'login-confirm.com',  # Common phishing keyword
    'payment-verification.com',  # Common phishing keyword
    'confirm-your-account.com',  # Common phishing keyword
    'secure-accounts.com', # Common phishing keyword
    'account-recovery.com', # Common phishing keyword
    'get-your-password.com', # Common phishing keyword
    'login-secure.com',    # Common phishing keyword
    'account-access.com',  # Common phishing keyword
    'phishingsite.net',    # Variants of phishing sites
    'malicious.net',       # Variants of malicious sites
    'suspicious.net',      # Variants of suspicious sites
    'unknown-website.com', # Hypothetical domain
    'untrusted-site.com',  # Hypothetical domain
    'fraudulent-activity.com', # Hypothetical domain
    'scam-website.com',    # Hypothetical domain
    'dangerous-link.com',  # Hypothetical domain
    'fraud.com',           # Generic fraud site
    'impersonate.com',     # Generic impersonation site
    'malware-distribution.com', # Sites known for malware
    'phishing-attack.com', # Generic phishing site
    'hacked-login.com',    # Impersonating login pages
    'spoofed-site.com',    # Generic spoofed site
    'secure-your-identity.com', # Common phishing keyword
    'identity-theft.com',  # Generic identity theft site
    'login-verification.com', # Common phishing keyword
    'verify-your-identity.com', # Common phishing keyword
    # Add more domains as needed
]
    # Check if the domain of the URL is in the unsafe domains list
    domain = urlparse(url).netloc
    is_safe_domain = not any(unsafe in domain for unsafe in unsafe_domains)
    if not is_safe_domain:
        safe_anchor_score = 0  # Not safe if the domain is unsafe
    # Check for common domain extensions
    common_safe_extensions = ['com', 'org', 'net', 'gov', 'edu', 'info']
    domain_extension = domain.split('.')[-1] if '.' in domain else ''
    is_common_extension = domain_extension in common_safe_extensions
    if not is_common_extension:
        safe_anchor_score = 0  # Not safe if the domain extension is uncommon
    # Check for excessive length of URL
    max_length = 2048  # Common maximum URL length
    is_length_safe = len(url) <= max_length
    if not is_length_safe:
        safe_anchor_score = 0  # Not safe if the URL is too long
    return safe_anchor_score

def check_domain_in_title(url):
    # Create headers to simulate a Chrome browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.134 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive'
    }
    parsed_url = urlparse(url)
    try:
        response = requests.get(url, headers=headers, timeout=TIME_LIMIT)
        response.raise_for_status()  # Raises an error for bad responses
        # Extract title from the HTML using BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string if soup.title else ''  # Ensure title is a string
        # Check if title is None and handle it
        if title is None:
            title = ''  # Default to empty string if title is None
        # Get domain parts and convert them to lowercase
        domain_parts = parsed_url.netloc.split('.')
        domain_words = [part.lower() for part in domain_parts]
        # Check if any domain word is in the title (case-insensitive)
        domain_in_title = any(word in title.lower() for word in domain_words)
        # Return 1 if any word from domain is found in title, else return 0
        result = 1 if domain_in_title else 0
        return result  # Return the result
    except requests.Timeout:
        return -1  # Indicate error with -1
    except requests.HTTPError as http_err:
        return -1  # Handle HTTP errors
    except requests.RequestException as e:
        return -1  # Handle other requests exceptions

def extract_nb_subdomains(url):
    # Parse the URL
    parsed_url = urlparse(url)
    netloc = parsed_url.netloc
    two_part_tlds = {
    "co.uk", "com.au", "net.au", "org.au", "gov.uk", "ac.uk",
    "gov.au", "com.sg", "co.jp", "co.in", "co.kr", "com.cn"
}
    # Remove port number if present
    if ':' in netloc:
        netloc = netloc.split(':')[0]
    # Split the network location by dots
    parts = netloc.split('.')
    # Ensure there are at least two parts (domain and TLD)
    if len(parts) < 2:
        return 0  # No valid domain structure found
    # Form the TLD (either two-part or single-part)
    tld = '.'.join(parts[-2:]) if len(parts) > 2 else parts[-1]
    # Determine if TLD is two-part or single-part
    if tld in two_part_tlds:
        # Exclude the last three parts (two-part TLD + main domain)
        subdomain_count = max(0, len(parts) - 3)
    else:
        # Exclude the last two parts (single-part TLD + main domain)
        subdomain_count = max(0, len(parts) - 2)
    return subdomain_count

def calculate_avg_word_path(url):
    parsed_url = urlparse(url)
    # Split the path into segments and filter out empty segments
    path_segments = [segment for segment in parsed_url.path.strip('/').split('/') if segment]
    # Calculate average word length in the path segments
    if path_segments:
        total_length = sum(len(word) for word in path_segments)
        return total_length / len(path_segments)
    else:
        return 0  # Return 0 if there are no path segments

def calculate_avg_words_raw(url):
    try:
        # Send a GET request to the URL
        response = requests.get(url, timeout=TIME_LIMIT)
        response.raise_for_status()  # Raises an error for bad responses
        # Split the response text into words
        words = response.text.split()
        # Parse the URL to get the path
        parsed_url = urlparse(url)
        path_segments = parsed_url.path.split('/')  # Split the path into segments
        # Calculate the average number of words per path segment
        avg_words_raw = len(words) / len(path_segments) if path_segments else 0
        return avg_words_raw
    except requests.Timeout:
        return -1  # Indicate error with -1
    except requests.HTTPError as http_err:
        return -1
    except requests.RequestException as e:
        return -1  # Indicate error with -1

def extract_nb_qm(url):
    return url.count('?')

def extract_domain_in_brand(url):
    try:
        response = requests.get(url, timeout=TIME_LIMIT)
        response.raise_for_status()  # Raises an error for bad responses
        # Use BeautifulSoup to parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        # Extract text from the soup and check for 'brand'
        page_text = soup.get_text().lower()  # Get the text and convert to lowercase
        return 1 if 'brand' in page_text else 0  # Case insensitive check
    except requests.Timeout:
        return -1  # Indicate error with -1
    except requests.HTTPError as http_err:
        return -1
    except requests.RequestException as e:
        return -1  # Indicate error with -1

def shortest_word_path(url):
    # Parse the URL to extract the path
    parsed_url = urlparse(url)
    # Split the path into segments and filter out any empty segments
    path_segments = [segment for segment in parsed_url.path.split('/') if segment]
    # Calculate the length of the shortest word in the path segments
    if path_segments:  # Check if there are any path segments
        return min(len(word) for word in path_segments)
    else:
        return 0  # Return 0 if there are no path segments

def extract_nb_and(url):
    # Count the number of occurrences of '&' in the URL
    return url.count('&')

def extract_nb_extCSS(url):
    ext_css_count = 0
    try:
        # Send a GET request to the URL
        response = requests.get(url, timeout=TIME_LIMIT)
        # response.raise_for_status()  # Raise an error for bad responses
        # Parse the HTML content with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        # Find all <link> tags that have an href attribute ending with .css
        css_links = soup.find_all('link', href=re.compile(r'\.css$'))
        # Count the number of external CSS files found
        ext_css_count = len(css_links)
        return ext_css_count
    except requests.exceptions.RequestException as e:
        return -1

def extract_nb_hyphens(url):
    parsed_url = urlparse(url)
    return parsed_url.netloc.count('-')

def extract_nb_slash(url):
    parsed_url = urlparse(url)
    # Count slashes in the path and query components
    # `url.count('/')` - 2 to exclude the first two slashes
    return parsed_url.path.count('/') + parsed_url.query.count('/')  # Include only path and query parts


def extract_domain_with_copyright(url):
    try:
        # Send a GET request to the URL
        response = requests.get(url, timeout=TIME_LIMIT)
        response.raise_for_status()  # Raise an error for bad responses
        # Parse the HTML content with Beautiful Soup
        soup = BeautifulSoup(response.text, 'html.parser')
        # Check for copyright symbol in the parsed content
        if '©' in soup.get_text():
            return 1  # Copyright symbol found in the content
        else:
            return 0  # Copyright symbol not found in content
    except requests.exceptions.RequestException as e:
        return -1  # Error occurred

def extract_length(url):
  return len(url)

def extract_avg_word_host(url):
    parsed_url = urlparse(url)
    host_segments = parsed_url.netloc.split('.')
    # Calculate the average word length in the host
    return (sum(len(word) for word in host_segments) / len(host_segments)
                                  if host_segments else 0)

def extract_ratio_digits_host(url):
    parsed_url = urlparse(url)
    # Get the netloc (host) part of the URL
    host = parsed_url.netloc
    # Count the number of digits in the netloc (host)
    digit_count = sum(char.isdigit() for char in host)
    # Calculate the total length of the netloc (host)
    total_length = len(host)
    # Ensure we don't divide by zero
    if total_length > 0:
        ratio = digit_count / total_length
    else:
        ratio = 0.0  # Avoid division by zero
    return ratio

def count_special_characters(url):
    try:
        special_chars = re.findall(r'[@!$%^&*(),?":{}|<>]', url)
        return len(special_chars)
    except Exception:
        return -1

def https_in_url(url):
    try:
        return 1 if urlparse(url).scheme == 'https' else 0
    except Exception:
        return -1

def https_in_domain(url):
    try:
        domain = urlparse(url).netloc
        return 1 if 'https' in domain else 0
    except Exception:
        return -1

def has_prefix_suffix(url):
    try:
        domain = urlparse(url).netloc
        return 1 if '-' in domain else 0
    except Exception:
        return -1

def depth_of_url(url):
    try:
        path = urlparse(url).path
        parts = [p for p in path.split('/') if p]  # Remove empty parts caused by extra slashes
        # Check if the last part is a file (has an extension)
        if parts and os.path.splitext(parts[-1])[1]:  # If last part has an extension, exclude it from depth count
            return len(parts) - 1
        return len(parts)
    except Exception:
        return -1

def count_parameters(url):
    try:
        query = urlparse(url).query
        return len(query.split('&')) if query else 0
    except Exception:
        return -1

def uncommon_tld(url):
    # Basic set of the most common TLDs
    common_tlds = [
    '.com',    # Most common for commercial businesses
    '.org',    # Commonly used by non-profit organizations
    '.net',    # Often used by internet service providers and tech companies
    '.gov',    # Official government websites
    '.edu',    # Educational institutions (universities, colleges)
    '.mil',    # Military institutions
    '.info',   # Information-related websites, often legitimate
    '.co',     # Increasingly used by companies
    '.us',     # United States-specific domains
    '.io',     # Tech startups and organizations
    '.biz',    # Business-related websites
    '.me',     # Personal websites
    '.dev',    # Development-related sites
    '.store',  # E-commerce websites
    '.health', # Health-related organizations
    '.name',   # Personal branding sites
    '.pro',    # Professional services
    '.jobs',   # Employment and job postings
    ]
    try:
        # Parse the TLD from the URL
        domain_parts = urlparse(url).netloc.split('.')
        if len(domain_parts) < 2:
            return -1  # Invalid TLD or domain
        # Extract the TLD
        tld = '.' + domain_parts[-1].lower()  # Convert to lowercase to handle cases like .COM
        # Mark as 0 for common TLDs, 1 for uncommon
        return 0 if tld in common_tlds else 1
    except Exception:
        return -1  # Return -1 if an exception occurs

def is_numeric_domain(url):
    try:
        # Parse the domain from the URL
        domain = urlparse(url).netloc
        # Split the domain into subdomains and the main domain part
        domain_parts = domain.split('.')
        # Check the main part of the domain for numeric-only characters
        if domain_parts[-2].isdigit():
            return 1  # Indicates a numeric domain
        else:
            return 0  # Indicates a non-numeric domain
    except Exception:
        return -1  # Return -1 in case of an error

def domain_misspelling(url, common_words=["google", "facebook", "fb", "amazon", "instagram", "insta", "twitter", "youtube", "yt", "shopify", "paypal", "linkedin", "microsoft", "apple"]):
    try:
        domain = urlparse(url).netloc.split('.')[0]
        # Regular expression to identify typical phishing patterns around brand names
        pattern = re.compile(r'\b(?:{})\b'.format('|'.join(common_words)), re.IGNORECASE)
        # Check if a brand name exists within the domain but isn't an exact match
        if pattern.search(domain):
            for word in common_words:
                # Match if domain contains the brand but is not exactly the brand
                if word in domain and domain != word:
                    # Check for likely phishing additions such as "my", "login", "secure", etc.
                    if any(prefix in domain for prefix in ["my", "login", "secure", "service", "page", "account", "help", "buy", "shop", "friends", "support", "team"]):
                        return 1
                    # Allow exact brand domains
                    elif domain == word:
                        return 0
            return 0  # No suspicious pattern found
        return 1  # Suspicious if unrelated to any known brand
    except Exception:
        return -1  # Error case

def is_url_shortened(url):
    try:
        shortened_domains = {
            'bit.ly', 'goo.gl', 'tinyurl.com', 'ow.ly', 't.co', 'buff.ly', 'adf.ly', 'bit.do',
            'cutt.ly', 'is.gd', 'soo.gd', 's2r.co', 'shorte.st', 'lnkd.in', 't.ly', 'bl.ink',
            'mcaf.ee', 'x.co', 'tiny.cc', 'rebrand.ly', 'trib.al', 'clck.ru', 'm.me', 'po.st',
            'smarturl.it', 'qr.ae', 'v.gd', '0rz.tw', 'ln.is'
        }
        parsed_url = urlparse(url)
        return 1 if parsed_url.netloc in shortened_domains else 0
    except Exception:
        return -1

valid_tlds = {
        "com", "org", "net", "edu", "gov", "co", "io", "uk", "au", "in", "store", "info",
        "biz", "me", "tv", "name", "xyz", "online", "app", "shop", "website", "mobi",
        "pro", "cc", "asia", "global", "travel", "site", "tech", "health", "money",
        "media", "law", "design", "photo", "fun", "tips", "life", "work", "family",
        "today", "place", "space", "win", "group", "club"
        }
def count_tld_in_url(url):
    if not isinstance(url, str):
        # logging.error(f"Invalid input type: {type(url)}. Expected string.")
        return -1  # Invalid input type
    try:
        # Improved pattern to match only valid TLDs at the end of the domain name
        tld_pattern = r'\b(?:[a-zA-Z0-9-]+\.)+([a-zA-Z]{2,})\b'  # Match domain names with valid TLDs
        tld_matches = re.findall(tld_pattern, url)  # Find all TLD matches
        # Count unique valid TLDs
        tld_count = sum(1 for tld in tld_matches if tld in valid_tlds)
        return tld_count
    except Exception as e:
        return -1  # General error

def count_tld_in_domain(url):
    try:
        domain = urlparse(url).netloc
        # Use a more precise regex to capture the TLD correctly
        tld_pattern = r'\.([a-z]{2,})$'
        match = re.search(tld_pattern, domain)
        # If a TLD match is found, return 1; otherwise, return 0
        return 1 if match else 0
    except Exception as e:
        # Return -1 in case of an error
        return -1

def count_tilde_in_url(url):
    if not isinstance(url, str):
        return -1  # Invalid input type
    try:
        return url.count('~')
    except Exception as e:
        return -1  # General error

def count_asterisk_in_url(url):
    if not isinstance(url, str):
        return -1  # Invalid input type
    try:
        return url.count('*')  # Count asterisk characters in the URL
    except Exception as e:
        return -1  # General error handling

def count_dollar_in_url(url):
    if not isinstance(url, str):
        return -1  # Invalid input type
    try:
        return url.count('$')  # Count dollar characters in the URL
    except Exception as e:
        return -1  # General error handling

def get_file_length(url):
    if not isinstance(url, str):
        return -1  # Invalid input type
    try:
        # Parse the URL and extract the path
        path = urlparse(url).path
        # If the path ends with a slash, it's likely a directory, return 0
        if path.endswith('/'):
            return 0
        # Split the path into components
        path_parts = path.split('/')
        # Get the last part of the path, which should be the file name
        file_name = path_parts[-1]
        # Check if the file name is empty
        if not file_name:
            return 0
        # Return the length of the file name
        return len(file_name)
    except Exception as e:
        return -1  # General error

from urllib.parse import urlparse

def extract_domain(url):
    match = re.search(r'://(www\.)?([a-zA-Z0-9.-]+)', url)
    return match.group(2) if match else url  # Return the domain if found, otherwise return the input URL

def count_repeated_letters(url):
    # Extract the domain part of the URL
    domain = extract_domain(url)

    # Use the original logic on the domain
    repeated_letters = re.findall(r'(.)\1+', domain)
    return len(repeated_letters)

def count_repeated_vowels(url):
    # Extract the domain part of the URL
    domain = extract_domain(url)

    # Use the original logic on the domain
    repeated_vowels = re.findall(r'([aeiouAEIOU])\1+', domain)
    return len(repeated_vowels)

def calculate_vowel_repetition_ratio(url):
    # Extract the domain part of the URL
    domain = extract_domain(url)

    # Find repeated vowels in the domain
    repeated_vowels = re.findall(r'([aeiouAEIOU])\1+', domain)
    
    # Calculate the domain length
    domain_length = len(domain)
    
    # Calculate the ratio of repeated vowels to the domain length
    return round(len(repeated_vowels) / domain_length, 3) if domain_length > 0 else 0


def has_non_standard_port(url):
    try:
        parsed_url = urlparse(url)
        if parsed_url.port:
            return 0 if parsed_url.port in [80, 443] else 1
        return -1  # Return -1 if no port is specified
    except Exception as e:
        return -1  # Return -1 in case of an error

def is_abnormal_url(url):
    try:
        # Check length of the entire URL
        if len(url) > 75:
            return 1
        # Check for forbidden characters
        if re.search(r'[<>{}|\\^~\[\]`]', url):
            return 1
        # Check if the URL contains an IP address instead of a domain name
        if re.search(r'^(?:http://|https://)?(?:\d{1,3}\.){3}\d{1,3}', url):
            return 1
        # Check for localhost and reserved IP addresses (with or without subdomains)
        if re.search(r'^(?:http://|https://)?(?:localhost|127\.0\.0\.1|::1|(\w+\.)?localhost)', url):
            return 1
        # Check for uncommon TLDs (Top-Level Domains)
        uncommon_tlds = [
            '.xyz', '.top', '.club', '.online', '.site',
            '.win', '.work', '.info', '.biz', '.pw',
            '.icu', '.ga', '.cf', '.ml', '.party',
            '.loan', '.trade', '.gq', '.space',
            '.mobi', '.buzz', '.link', '.bizz'  # Added '.bizz'
        ]
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        # Check if domain ends with any uncommon TLDs
        if any(domain.endswith(tld) for tld in uncommon_tlds):
            return 1
        # Check for excessive subdomains
        subdomains = domain.split('.')
        if len(subdomains) > 3:  # More than 2 subdomains
            return 1
        return 0
    except Exception as e:
        return -1

def qty_double_slash_path(url):
    try:
        path = urlparse(url).path
        count = path.count('//')
        return count
    except Exception:
        return -1

def check_protocol(url):
    parsed_url = urlparse(url)
    return 1 if parsed_url.scheme in ['http', 'https'] else 0

def extract_features(url):
    """Extract features from the given URL."""
    features = {}
    parsed_url = urlparse(url)

    # Timing the overall feature extraction
    start_time = time.time()

    try:
        # Feature 1: Google Index
        features['google_index'] = get_google_index(url)

        # Feature 3: Number of hyperlinks
        features['nb_hyperlinks'] = extract_hyperlink_count(url)

        # Feature 4: Web Traffic
        features['web_traffic'] = get_web_traffic(url)

        # Feature 5: Number of "www" in hostname
        features['nb_www'] = parsed_url.netloc.count('www')

        # Feature 6: Ratio of external hyperlinks
        features['ratio_extHyperlinks'] = calculate_ratio_extHyperlinks(url)

        # Feature 7: Domain Age
        features['domain_age'] = get_domain_age(url)

        # Feature 8: Phishing hints
        features['phish_hints'] = extract_phishing_hints(url)

        # Feature 9: Safe anchor
        features['safe_anchor'] = extract_safe_anchor(url)

        # Feature 10: Ratio of digits in URL
        features['ratio_digits_url'] = calculate_ratio_digits_url(url)

        # Feature 11: Length of URL
        features['length_url'] = extract_length(url)

        # Feature 12: Average word length in path
        features['avg_word_path'] = calculate_avg_word_path(url)

        # Feature 13: Length of hostname
        features['length_hostname'] = extract_length_hostname(url)

        # Feature 14: ratio_extRedirection
        features['ratio_extRedirection'] = calculate_ratio_extHyperlinks(url)

        # Feature 15: longest_words_raw
        features['longest_words_raw'] = extract_longest_words_raw(url)

        # Feature 16: length_words_raw
        features['length_words_raw'] = extract_length_words_raw(url)

        # Feature 17: Number of dots in hostname
        features['nb_dots'] = count_dots(url)

        # Feature 18: links_in_tags
        features['links_in_tags'] = extract_links_in_tags(url)

        # Feature 19: domain_registration_length
        features['domain_registration_length'] = extract_domain_registration_length(url)

        # Feature 20: Number of slashes in URL
        features['nb_slash'] = extract_nb_slash(url)

        # Feature 21: Domain in title
        features['domain_in_title'] = check_domain_in_title(url)

        # Feature 22: Average words in raw text
        features['avg_words_raw'] = calculate_avg_words_raw(url)

        # Feature 23: Shortest word in path
        features['shortest_word_path'] = shortest_word_path(url)

        # Feature 24: Presence of IP in the URL
        features['ip'] = extract_ip_feature(url)

        # Feature 25: Number of hyphens in hostname
        features['nb_hyphens'] = extract_nb_hyphens(url)

        # Feature 26: Average word length in hostname
        features['avg_word_host'] = extract_avg_word_host(url)

        # Feature 27: Ratio of digits in hostname
        features['ratio_digits_host'] = extract_ratio_digits_host(url)

        # Feature 28: ratio_intMedia
        features['ratio_intMedia'] = extract_ratio_intMedia(url)

        # Feature 29: Number of query parameters in URL
        features['nb_qm'] = extract_nb_qm(url)

        # Feature 30: Domain with copyright
        features['domain_with_copyright'] = extract_domain_with_copyright(url)

        # Feature 31: ratio_extMedia
        features['ratio_extMedia'] = extract_ratio_extMedia(url)

        # Feature 32: Number of external CSS
        features['nb_extCSS'] = extract_nb_extCSS(url)

        # Feature 33: Number of subdomains
        features['nb_subdomains'] = extract_nb_subdomains(url)

        # Feature 34: Domain in brand
        features['domain_in_brand'] = extract_domain_in_brand(url)

        # Feature 35: Number of occurrences of 'and' in URL
        features['nb_and'] = extract_nb_and(url)

        # Feature 36: count special characters in URL
        features['nb_special_characters'] = count_special_characters(url)

        # Feature 37: check if URL uses HTTPS
        features['https_in_url'] = https_in_url(url)

        # Feature 38: check if domain uses HTTPS
        features['https_in_domain'] = https_in_domain(url)

        # Feature 39: check for prefix-suffix in domain (indicated by '-')
        features['has_prefix_suffix'] = has_prefix_suffix(url)

        # Feature 40: calculate URL depth (count of '/' in path)
        features['depth_of_url'] = depth_of_url(url)

        # Feature 41: count parameters in URL
        features['count_parameters'] = count_parameters(url)

        # Feature 42: check for uncommon TLD
        features['uncommon_tld'] = uncommon_tld(url)

        # Feature 43: check if the main part of the domain is numeric
        features['is_numeric_domain'] = is_numeric_domain(url)

        # Feature 44: check domain misspelling using common patterns and brand detection
        features['domain_misspelling'] = domain_misspelling(url)

        # Feature 45: count occurrences of double slashes '//' in URL path
        features['qty_double_slash_path'] = qty_double_slash_path(url)

        # Feature 46: Check for non-standard ports
        features['non_standard_port'] = has_non_standard_port(url)

        # Feature 47: Check for abnormal URL patterns
        features['abnormal_url'] = is_abnormal_url(url)

        # Feature 48: Check if the URL is shortened
        features['url_shortened'] = is_url_shortened(url)

        # Feature 49: Count the number of TLDs (Top-Level Domains) in the URL
        features['tld_count_in_url'] = count_tld_in_url(url)

        # Feature 50: Count the number of TLDs in the domain part of the URL
        features['tld_count_in_domain'] = count_tld_in_domain(url)

        # Feature 51: Count the number of tilde characters in the URL
        features['tilde_count'] = count_tilde_in_url(url)

        # Feature 52: Count the number of asterisk characters in the URL
        features['asterisk_count'] = count_asterisk_in_url(url)

        # Feature 53: Count the number of dollar characters in the URL
        features['dollar_count'] = count_dollar_in_url(url)

        # Feature 54: Get the length of the file part of the URL
        features['file_length'] = get_file_length(url)

        # Feature 55: Count the groups of consecutive repeated letters in the domain of the URL
        features['repeated_letters'] = count_repeated_letters(url)

        # Feature 56: Count the groups of consecutive repeated vowels in the domain of the URL
        features['repeated_vowels'] = count_repeated_vowels(url)

        # Feature 57: Calculate the ratio of repeated vowels to the total length of the domain
        features['vowel_repetition_ratio'] = calculate_vowel_repetition_ratio(url)



        features_df = pd.DataFrame([features])
        # features_df = [features]
        return features_df
    except Exception as e:
        # If an exception occurs, create a DataFrame with all-zero values
        feature_names = [
            'google_index', 'nb_hyperlinks', 'web_traffic', 'nb_www', 'ratio_extHyperlinks',
            'domain_age', 'phish_hints', 'safe_anchor', 'ratio_digits_url', 'length_url', 'avg_word_path',
            'length_hostname', 'ratio_extRedirection', 'longest_words_raw', 'length_words_raw', 'nb_dots',
            'links_in_tags', 'domain_registration_length', 'nb_slash', 'domain_in_title', 'avg_words_raw',
            'shortest_word_path', 'ip', 'nb_hyphens', 'avg_word_host', 'ratio_digits_host', 'ratio_intMedia',
            'nb_qm', 'domain_with_copyright', 'ratio_extMedia', 'nb_extCSS', 'nb_subdomains', 'domain_in_brand',
            'nb_and', 'nb_special_characters', 'https_in_url', 'https_in_domain', 'has_prefix_suffix',
            'depth_of_url', 'count_parameters', 'uncommon_tld', 'is_numeric_domain', 'domain_misspelling', 'qty_double_slash_path',
            'non_standard_port', 'abnormal_url', 'url_shortened', 'tld_count_in_url', 'tld_count_in_domain',
            'tilde_count', 'asterisk_count', 'dollar_count', 'file_length', 'repeated_letters', 'repeated_vowels', 'vowel_repetition_ratio'
        ]
        features_df = pd.DataFrame([{feature: -1 for feature in feature_names}])
        # features_df = [{feature: -1 for feature in feature_names}]
        return features_df

