import json
import logging
import os
import string
import sys

class SystemCheck:
    def __init__(self):
        self.options_file = "options.json"
        self.options = {}

    def check_options(self):
        if os.path.exists(self.options_file):
            with open(self.options_file, 'r') as file:
                self.options = json.load(file)
            logging.info("Options loaded successfully.")
        else:
            logging.warning("Options file not found. Requesting options from user.")
            self.build_options()

        # Check command line arguments for --options
        if '--options' in sys.argv:
            logging.info("User requested options rebuild.")
            self.build_options()

    def build_options(self):
        option_builder = OptionBuild()
        option_builder.build_options()
        self.options = option_builder.options

class OptionBuild:
    def __init__(self):
        self.options_path = "options.json"
        self.load_existing_options()

    def load_existing_options(self):
        try:
            with open(self.options_path, 'r') as file:
                self.options = json.load(file)
            logging.info("Existing options loaded for update.")
        except FileNotFoundError:
            logging.info("No existing options file found. Starting fresh.")
            self.options = {}

    def build_options(self):
        logging.info("Starting interactive option builder.")
        example_length = 60  # Set the length of the example PayID
        example_pay_id = (string.ascii_uppercase * (example_length // len(string.ascii_uppercase) + 1))[:example_length]
        questions = [
            ("Allow CPU Mining? (Y/n): ", "CPUMining", "Yes", True),
            ("CPU Alias? (Only if CPU Mining is True): ", "CPUAlias", "CPU", False),
            ("Allow GPU Mining (CUDA ONLY)? (Y/n): ", "GPUMining", "No", True),
            ("GPU Alias? (Only if GPU Mining is True): ", "GPUAlias", "GPU", False),
            ("Start Mining on Application Startup? (Y/n): ", "Autostart", "Yes", True),
            ("Automatically Update File When Available? (Y/n): ", "AutoUpdate", "Yes", True),
            ("Automatically Benchmark CPU Versions? (Y/n): ", "AutoBench", "Yes", True),
            ("Automatically Restart Miners as Needed? (Y/n): ", "AutoRestart", "Yes", True),
            ("Please Enter File Path for Mining Files? (Default is current directory): ", "FilePath", os.getcwd(), False),
            ("Please Enter Payout ID? (Required, no default): ", "PayID", "", False),
            ("How Many CPU Threads? (Default is max logical processors): ", "ThreadCount", os.cpu_count(), False),
            ("Hide Mining Windows? (Y/n): ", "HideWindows", "No", True)
        ]

        for prompt, key, default, is_boolean in questions:
            valid_response = False
            while not valid_response:
                current_value = self.options.get(key, default)
                response = input(f"{prompt} (Current: {current_value}) ")
                logging.debug(f"Processing {key}: '{response}' with length {len(response)}")

                if not response:
                    response = current_value

                if key == "PayID":
                    logging.debug(f"Checking PayID: '{response}' (Expected length {len(example_pay_id)})")
                    if response.isupper() and len(response) == len(example_pay_id):
                        valid_response = True
                    else:
                        logging.error(f"Invalid PayID entered: '{response}'. Length: {len(response)}, Uppercase: {response.isupper()}")
                        print(f"Invalid PayID. It must be all uppercase and {len(example_pay_id)} characters long.")
                        for index, char in enumerate(response):
                            print(f"Index: {index}, Char: '{char}'")

                elif is_boolean:
                    if response.lower() in ['y', 'yes']:
                        response = True
                        valid_response = True
                    elif response.lower() in ['n', 'no']:
                        response = False
                        valid_response = True
                    else:
                        print("Invalid response. Please answer with 'Y' for Yes or 'N' for No.")
                else:
                    valid_response = True

                self.options[key] = response

        self.save_options()

    def save_options(self):
        with open(self.options_path, 'w') as file:
            json.dump(self.options, file, indent=4)
        logging.info("Options saved to file.")

# Setup logging to see debug outputs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
