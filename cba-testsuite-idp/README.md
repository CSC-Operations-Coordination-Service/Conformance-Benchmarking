

# Conformance SW Test Suite v1.3.0

The Conformance Test Suite software package verifies the compliance of CSC Ground Segment Interface Delivery Points (IDP) with the corresponding ICD specifications. The following interfaces are currently tested:

* LTA: LTA Interface Point
* PRIP: Production Interface Point
* AUXIP: Auxiliary Data Interface Point
* EDRS: EDRS Interface Point
* CADIP: CADU Interface delivery Point

The Conformance Test Suite uses the free [Postman API platform](https://www.postman.com/) for testing the IDP’s APIs, except for the EDRS Interface Point where [Python](https://www.python.org/) is used.

## The Postman Conformance Test Suite
### Postman download and install
Postman is available as a native desktop app for Mac (Intel and Apple), Windows (32-bit/64-bit), and Linux (64-bit) operating systems.
Download and install the latest desktop [Postman app](https://www.postman.com/downloads/) following the instructions from the official webpage.

### Test Suite configuration
In order to execute the Conformance tests against the CSC Ground Segment IDP the following steps are required:

* [**Import the Postman Collection**](#Import-the-Postman-Collection)
* [**Configure the provider's Environment**](#Configure-the-provider's-Environment)
* [**Import the Environment**](#Import-the-Environment)
* [**Disable SSL certificate verification**](#Disable-SSL-certificate-verification)
* [**Configure the external data file**](#Configure-the-external-data-file)
* [**Configure the Collection Runner**](#Configure-the-Collection-Runner)
* [**Run the collection**](#Run-the-collection)

The [**Specific Examples**](#Specific-Examples) section then shows some practical examples of test execution.

#### Import the Postman Collection
 
- Open the Postman desktop app
- Click the "Import" button in the top left section
- Click on "Choose Files" and select the *CBA_Interface_Delivery_Point_Test_Suite.json* collection from the unzipped package
- Click on the "Import" button to load the collection

#### Configure the provider's Environment
The SW Test Suite package has an "env" folder with a set of files containing the connection parameters and credentials for each *SERVICE_PROVIDER_PLATFORM* tuple.
Edit the file for the given *SERVICE_PROVIDER_PLATFORM*, modifying the values of the json array in order to connect to a given Interface Delivery Point.

For example, change the corresponding "yourusername", "yourpassword", etc. with your account info.

#### Import the Environment
 
- Select "Environments" in the left most column of the interface
- Click the "Import" button in the top left section
- Click on "Choose Files" and select the appropriate environment file 
- Click on the "Import" button to load the environment

#### Disable SSL certificate verification
Disable the authentication when sending requests:

- From the Postman burger menu, click File -> Settings
- From the "Settings" window in the "General" tab:
- Set the "SSL certificate verification" button to "OFF"
- Close the window

#### Configure the external data file
The SW Test Suite package has a "params" folder with a set of files containing the specific parameters used for each *SERVICE_PROVIDER_PLATFORM* tuple.
Edit the file for the given *SERVICE_PROVIDER_PLATFORM* in order to use such parameters in the Extended tests executions.
Later on, during the configuration of the Collection Runner, you can import such data file.

#### Configure the Collection Runner
The Collection Runner enables to run the API requests of a collection in a specified sequence. 
The user can configure the Collection Runner and execute it using a specific environment with an external data file.

Execute the following steps to configure a collection run:
1. Click on the "Runner" icon from the Postman footer bar (or from File -> New Runner Tab)
2. Drag a collection or folder from the sidebar. *Note*: you can also select the Collection folder to run from the sidebar and then select the Run icon on the overview tab
3. Choose an Environment using the environment combo box at the top right of Postman interface
4. Optionally change the "Run Configuration" parameters (typical values are shown in parenthesis):

    * Iterations (1) - This option sets the number of iterations to run.
    * Delay (1000) - It applies an interval delay in milliseconds between each request.
    * Data (custom) - Click on "Data" button and choose an external data file for the collection run.
    * Save responses (disabled) - Save response headers and bodies to the log to review them later. For large collection runs, this setting can affect performance.
    * Keep variable values (enabled) - Persist the variables used in the run. This option saves the variables that have changed after the run completes. 
    * Run collection without using stored cookies (disabled) - If the requests use cookies, it is possible to optionally deactivate them.
    * Save cookies after collection run (enabled) - Save the used cookies.

#### Run the Collection
When the configuration of the Collection Runner is complete, the user can click on "Run *COLLECTION_NAME*" button to execute the tests and check the results. 
After test execution, the View Results page indicates for each request assertion the status of "passed" or "failed".

When the test is executed, some variables are saved as globals parameters and used for requests. 
The user can display them if he/she selects "Environments" in the left part of the interface and clicks on "Globals".

**Please note:**
It is necessary to delete all variables on the globals tab before running a macro test (e.g.: Products, Subscriptions).
On the contrary, variables must not be deleted between steps (e.g.: after running "Create Subscription")
 
 
#### Specific Examples

* [**LTA Minimum Compliance**](#LTA-Minimum-Compliance)
* [**LTA Extended Compliance**](#LTA-Extended-Compliance)
* [**CADIP Extended Compliance**](#CADIP-Extended-Compliance)

#### LTA Minimum Compliance

##### LTA Orders (Minimum Compliance)
The following steps show how to test Order requests for LTA (Minimum Compliance).

###### Step 1 - Create Order (Minimum Compliance).
Select and run the folder "LTA Create Order (Minimum Compliance)"

When the test stops, the "OnlineStatus" variable is stored in the Globals tab:
  - If "OnlineStatus" is true or false, run Step 2
  - If "OnlineStatus" is null or if it does not exist, repeat Step 1. 

###### Step 2 -  Download product
Select and run the folder "LTA Product Download (Minimum Compliance)"

When the test stops, "DownloadStatus" is stored in the Globals tab.
Repeat Step 2 until the "DownloadStatus" is "completed".

#### LTA Extended Compliance

##### LTA Orders
The following steps show how to test Order requests for LTA (Extended Compliance).

###### Step 1 - LTA Create Order
Select and run the folder "LTA Create Order"

When the test stops, the "OnlineStatus" variable is stored in the Globals tab:
 - If "OnlineStatus" is true or false, run Step 2  
 - If "OnlineStatus" is null or if it does not exist, repeat Step 1.
 
###### Step 2 - LTA Product Retrieval
Select and run the folder "LTA Product Retrieval"

When the test stops, "DownloadStatus" is stored in the Globals tab. 
Repeat Step 2 until "DownloadStatus" is "completed".

##### LTA Bulks and BatchOrders
The following steps show how to test Bulk Order and BatchOrder requests for LTA.

###### Step 1 - LTA Create Bulk
Select and run the folder "LTA Bulk Create"

When the test stops, the "BulkStatus" variable is saved in the Globals tab.
The Step 2 can be executed only if "BulkStatus" is "created".

###### Step 2 - LTA BatchOrder Triggering
Select and run the folder "LTA BatchOrder Triggering"

When the test stops, Step 3 can be executed.

###### Step 3 - LTA Check if the BatchOrder status is completed
Select and run the folder "LTA Retrieve Completed BatchOrder"

When the test stops, "BatchOrderStatus" is updated in the Globals tab.
Step 4 can be executed only if "BatchOrderStatus" is "completed". Otherwise, Step 3 should be repeated.

###### Step 4 - LTA Check if the Bulk status is completed
Select and run the folder "LTA Retrieve Completed Bulk"

If "BulkStatus" is "created" or "in_progress", run Step 5.

###### Step 5 - Cancel Bulk
If "BulkStatus" is "created" or "in_progress" the folder "LTA Delete Bulk" can be run to cancel the bulk order.

#### CADIP Extended Compliance

##### CADIP Query Sessions
The following step shows how to test sessions requests for CADIP (Extended Compliance).

###### Step 1 - CADIP Query Sessions.
Select and run the folder "CADIP Query Sessions"

When the test stops, the variables are stored in the Globals tab.
												  
																	  

##### CADIP Query Files
The following step shows how to test files requests for CADIP (Extended Compliance).

###### Step 1 - CADIP Query Files.
Select and run the folder "CADIP Query Files"

When the test stops, the "FinalFlag" variable is stored in the Globals tab:
  - If "FinalFlag" is false, repeat Step 1 until this condition is verified. 
  - If "FinalFlag" is true, the test is finished. 

##### CADIP QualityInfo
The following step shows how to test QualityInfo requests for CADIP (Extended Compliance).

###### Step 1 - CADIP QualityInfo.
Select and run the folder "CADIP QualityInfo"

When the test stops, the "FinalFlag" variable is stored in the Globals tab:
  - If "FinalFlag" is false, repeat Step 1 until this condition is verified. 
  - If "FinalFlag" is true, the test is finished. 


## The Python EDRS Conformance Test Suite
The test suite uses [python](https://www.python.org/) for testing the EDRS Interface Point.

### Folders and Files
---------------------

The EDRS Conformance Test Suite can be found in the "scripts" subdirectory.
The main script (CBA_EDRS_Test.py file) is in the root directory, while the other subdirectories hold test scripts and functions.

The scripts in the "test" subdirectory contain the implemented test features and the functions to create the report:

 *  \_\_init__.py
 *  report.py
 *  test.py

The utilities, methods and main functionalities used in test scripts are instead in the "lib" subdirectory:

 * \_\_init__.py 
 * download.py  
 * encrypt.py
 * ftp.py
 * interface.py
 * progressbar.py  
 * search_file.py  
 * wr_files.py

The script relies on these additional files to run:

 *  An environment configuration file
 *  The logger configuration file `logger.conf` in the main folder
 *  Certificate files for authentication if the connection is encrypted.

### Configure the Environment file

The test suite needs to read a JSON configuration file in which the environment variables are stored. The file is passed to the suite using the -e command line argument.

The following is a generic configuration file example, where the satellite platform to be tested is defined using the `sat_dir` parameter:

```json
{
	"name": "EDRS EXAMPLE ENV",
    "values": [
        {
            "key": "service-root-uri",
            "value": "serverhostname-or-ip.com"
        },
        {
			"key": "port",
			"value": "21"
		},
        {
            "key": "username",
            "value": "yourusername"
        },
        {
            "key": "password",
            "value": "yourpassword"
        },
        {
            "key": "sat_dir",
            "value": "NOMINAL/S1A/"
        }
    ]
}
```

### General Usage

When an environment file is available, the test suite can be executed using the command line.
The main parameters are shown on the help page, which you can get by typing:

    python3 CBA_EDRS_Test.py --help

The output is the following:

```bash
usage: python3 CBA_EDRS_Test.py [-h] [-v [VERBOSE]] [-e ENV] [-A CACERT]
                                [-C CERT] [-k KEY] [-c CHANNEL] [-l LOCALPATH]
                                [-a AUTH] [-s SESSIONS]

Launch one or more test to test ftp connection

optional arguments:
  -h, --help            show this help message and exit
  -v [VERBOSE], --verbose [VERBOSE]
                        Display more information during processing: 0 = info,
                        1 = debug, 2 = only warnings. No number means debug.
  -e ENV, --env ENV     environment file
  -A CACERT, --cacert CACERT
                        Certificate of the Certificate Authority
  -C CERT, --cert CERT  User Certificate to be used for the identification at
                        the DMZ gateway
  -k KEY, --key KEY     Private Key for the asymmetric key negotiation
  -c CHANNEL, --channel CHANNEL
                        The separate directory for each channel. Default means
                        all channel (ch_1 and ch_2)
  -l LOCALPATH, --localpath LOCALPATH
                        Local download directory. Default means the root
                        directory.
  -a AUTH, --auth AUTH  authentication process (encrypted or unencrypted).
                        Default means unencrypted.
  -s SESSIONS, --sessions SESSIONS
                        Compare old sessions list and check if a new session
                        is available. Default means False.
```

#### Authentication

The user can connect using two types of authentications, encrypted and not encrypted (default).
If the connection needs to be encrypted, each user will be given by the service provider also the following information for authentication via X.509 compliant self-signed certificates, beside login credentials (user name, password):

* CA.crt (Certificate of the Certificate Authority, only if needed)
* Client.crt (User Certificate)
* Client key (Private Key for the asymmetric key negotiation)

#### Specific Examples

When the configuration is complete, the user can execute the tests and check the results.
The available command-line arguments can be used, according to the required configuration and test.

For example, the following command can be run from the module root directory for testing all channels without encrypted authentication:

```bash
python3 CBA_EDRS_Test.py --channel=all -e=environment_file.json
```

With encrypted authentication instead:

```bash
python3 CBA_EDRS_Test.py --channel=all -e=environment_file.json --auth=encrypted --cert=client_certificate.crt --key=client_key.key
```

### Results

At the end of the execution a JSON file is saved in the current working directory. It contains all test results, with "passed" or "failed" status.

A second JSON file is saved if the `--sessions True` option is used, containing the list of available sessions found; it is saved in the directory of the python script.

A temporary folder is created by the file download test. This folder contains files for both channels, and can be safely deleted at the end of the test.

### Debugging

During execution, the script prints basic logging information about the performed steps. The -v flag enables more detailed logging, including executed commands and other information.
