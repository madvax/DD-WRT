#!/usr/bin/env python3

# This python 3 script set a DD-WRT Access Point to use 
# WEP 128-bit encryption
# See the usage funcftion for more details 


# Theory of Operation
#    Import the selenium site library, if installed
#    Validate and process any command line arguments
#    Load the Selenium Firefox web driver a.k.a. geckodriver 
#    Load the wrireless router DD-WRT web interface into the web driver   
#    Navigate to Wriless Settings then Wireless Security page
#    Select WEP, then select 128-bit encryption 
#    Save and apply new settings 
#    Close the web driver 
#    Clean exit

# H. Wilson, November 2017 

# -----------------------------------------------------------------------------
# Imports
import sys, os, time                                    # standard library imports
from getopt  import getopt                              # used to process command line arguments
try:
   from selenium                       import webdriver # used to provide access to Firefox web driver 
   from selenium.webdriver.support.ui  import Select    # used to access and interface with Pulldown elements
except: 
   sys.stderr.write("\nERROR -- Unable to import from the Selenium site package.")
   sys.stderr.write("\n         Use pip3 to install Selenium:  pip3 install selenium")
   sys.stderr.write("\n")
   sys.exit(1)

# -----------------------------------------------------------------------------
# Dictionary
VERSION       =  "1.2.0" # Version number for this test case
VERBOSE       = False    # Verbose flag, when true generates additional output
DEBUG         = False    # Degug flag, when true generates debug output
FIRST         =  0       # Generic first element index
LAST          = -1       # Generic last element index 
ME            = os.path.split(sys.argv[FIRST])[LAST]        # Name of this file
MY_PATH       = os.path.dirname(os.path.realpath(__file__)) # Path for this file
username      = "test"                                           # DD-WRT Username 
password      = "testtest"                                       # DD-WRT Password
url           = "http://%s:%s@192.168.1.1" %(username, password) # DD-WRT URL with embedded credentials 
delay         = 3  # Generic time dela (in seconds) to accomodate for web page loading times      
encryptionKey = "1234567890abcdef1234567890"  # Default 128-bit encryption key 
interfaceId   = "0"                           # Defaul wireless interface (0->2.4GHz, 1->5GHz) 
band          = "2.4GHz"                      # Default Band, should align with Default wireless interface  
wirelessTabXPATH         = "/html/body/div/div/div[1]/div[2]/div/ul/li[2]/a"               # XPATH to the Wireless Tab
wirelessSecurityTabXPATH = "/html/body/div/div/div[1]/div[2]/div/ul/li[2]/div/ul/li[3]/a"  # XPATH to the Wireles Security Tab
# -----------------------------------------------------------------------------
# Native functions 

#------------------------------------------------------------------------------ usage()
def usage():
   """ usage() Displays a usage message on standard output """ 
   print("""
%s, Version %s
 
SUMARY: Sets up a DD-WRT 3.0 Access Point to use WEP 128-bit encryption 

USAGE: %s [OPTIONS]

OPTIONS:
  -h --help         Show this help message

  -v --verbose      Print verbose output to stdout

  -d --debug        Print debugging informatio to stdout

  -i --interface=   The wireless interface to use, either 2 or 5 for 
                    2.4GHz and 5GHz respectively.       
                    Default is 2 for the 2.4 GHz interface   

  -k --key=         The key to use for the encryption
                    Default encryption key: %s  

DEFINED EXIT CODES:
  0 - Successful completion of the task
  1 - Unable to import the Selenium site package    
  2 - Bad or missing command line arguments 
  3 - Bad interface specified, must be either 2 or 5
  4 - Bad encryption key specified, must be 26 hex digits, no ':'s
  5 - Unable to locatet and/or interact with web page element
  6 - Unable to open the Firefox web driver for Selenium (geckodriver)
  7 - Unable to access the URL, Check netowrk connection
  8 - Unabel to close the Firefox web driver for Selenium   
   """ %(ME, VERSION, ME, encryptionKey) )
   return

# -----------------------------------------------------------------------------
# Process command line arguments
try: arguments = getopt(sys.argv[1:]         , 
                        "hvdi:k:"            , 
                        [ 'help'       ,
                          'verbose'    , 
                          'debug'      , 
                          'interface=' ,
                          'key='       ]     )   
except Exception as e:
   sys.stderr.write("ERROR -- Bad command line argument(s)\n         %s\n" %str(e))
   sys.stderr.flush()
   usage()
   sys.exit(2)

# ------------------------------------------------------------------------------
# Check the command line options
# --- Check for a help option
for arg in arguments[FIRST]:
   if arg[FIRST]== "-h" or arg[FIRST] == "--help":
      usage()
      sys.exit(0)
# --- Check for a verbose option
for arg in arguments[FIRST]:
   if arg[FIRST]== "-v" or arg[FIRST] == "--verbose":
      VERBOSE = True               
# --- Check for a debug option
for arg in arguments[FIRST]:
   if arg[FIRST]== "-g" or arg[FIRST] == "--debug":
      DEBUG   = True
      VERBOSE = True   
# --- Check for an interface  option
for arg in arguments[FIRST]:
   if arg[FIRST]== "-i" or arg[FIRST] == "--interface":
      try:
         if arg[LAST] in ("2","5"):
            if arg[LAST] ==  "2":
               interfaceId = "0"
               band        = "2.4GHz"  
            elif  arg[LAST] ==  "5":
               interfaceId = "1"
               band        = "5GHz"
            else:
               raise ValueError("Interface Not 2 or 5") # Trust no one 
         else: 
            raise ValueError("Interface not in list [\"2\", \"5\"]")  
      except ValueError as e :
         sys.stderr.write("\nERROR -- Bad interace specified: \'%s\'\n         Valid Values are: 2 or 5" %arg[LAST])
         sys.stderr.write("\n         %s\n\n" %str(e))
         sys.exit(3)          
# --- Check for 128-bit encryption key option                   
for arg in arguments[FIRST]:
   if arg[FIRST]== "-k" or arg[FIRST] == "--key":
      try: 
         if len(arg[LAST]) == 26:
            try:    
               temp = int(arg[LAST], 16) # assert all characters are hex digits 
               encryptionKey = arg[LAST]   
            except: raise ValueError("Key is not hex digits, use [0-9][a-f][A-F]")
         else:
            raise ValueError("Wrong size key, key length: %s, should be 26" %len(arg[LAST])) 
      except ValueError as e:
         sys.stderr.write("\nERROR -- Bad encryption key specified: \'%s\'\n         Valid key must have 26 hex digist, no ':' characters" %arg[LAST])
         sys.stderr.write("\n         %s\n\n" %str(e))
         sys.exit(4)          


# -----------------------------------------------------------------------------
# Load Firefox web driver a.k.a. geckodriver 
if VERBOSE:
   sys.stdout.write("Loading Firefox ... ")
   sys.stdout.flush()
try: 
   driver = webdriver.Firefox()
except Exception as e:
   sys.stderr.write("\nERROR -- Unable to load Firefix webdriver")
   sys.stderr.write("\n         Check path to geckodriver and Firefox profile")
   sys.stderr.write("\n         %s\n\n" %str(e))
   sys.exit(6)
if VERBOSE: sys.stdout.write("done.\n")

# -----------------------------------------------------------------------------
# Open the URL (DD-WRT Router web interface)
if VERBOSE:
   sys.stdout.write("Opening \"%s\" ..." %url)
   sys.stdout.flush()
try:
   driver.get(url)
except Exception as e:
   sys.stderr.write("\nERROR -- Unable to access url \"%s\"" %url)
   sys.stderr.write("\n         Check network connection")
   sys.stderr.write("\n         %s\n\n" %str(e))
   sys.exit(7)          
if VERBOSE: sys.stdout.write("done.\n")

# -----------------------------------------------------------------------------
# Navigate to the wireless page in the DD-WRT web interface 
if VERBOSE:
   sys.stdout.write("Selecting Wrieless Tab ... ")
   sys.stdout.flush()
try:
   wirelessTab = driver.find_element_by_xpath(wirelessTabXPATH)
   wirelessTab.click()
   time.sleep(delay)
except Exception as e:
   sys.stderr.write("\nERROR -- Unable to find and/or click on \"Wireless\" tab")
   sys.stderr.write("\n         %s\n\n" %str(e))
   sys.exit(5)          
if VERBOSE: sys.stdout.write("done.\n")

# -----------------------------------------------------------------------------
# Navigate to the Wireless Security submenu in the DD-WRT web interface  
if VERBOSE:
   sys.stdout.write("Selecting Wrieless Security Submenu Tab ... ")
   sys.stdout.flush()
try:
   wirelessSecurityTab = driver.find_element_by_xpath(wirelessSecurityTabXPATH)
   wirelessSecurityTab.click()
   time.sleep(delay)
except Exception as e:
   sys.stderr.write("\nERROR -- Unable to find and/or click on \"Wireless Security\" tab")
   sys.stderr.write("\n         %s\n\n" %str(e))
   sys.exit(5)          
if VERBOSE: sys.stdout.write("done.\n")

# -----------------------------------------------------------------------------
# Select WEP as the Security Mode  
if VERBOSE:
   sys.stdout.write("Selecting WEP for %s interface  ... " %band)
   sys.stdout.flush()
try:
   securityModeDropdown = Select(driver.find_element_by_name( "wl%s_security_mode" %interfaceId))
   securityModeDropdown.select_by_visible_text("WEP")
   time.sleep(delay)
except Exception as e:
   sys.stderr.write("\nERROR -- Unable to find and/or click on \"Security Mode\" pulldown for WEP")
   sys.stderr.write("\n         %s\n\n" %str(e))
   sys.exit(5)          
if VERBOSE: sys.stdout.write("done.\n")

# -----------------------------------------------------------------------------
# Select 128-bit encryption 
if VERBOSE:
   sys.stdout.write("Selecting 128 Bit Encryption for WEP for %s interface  ... " %band)
   sys.stdout.flush()
try:
   encryptionDropdown = Select(driver.find_element_by_name( "wl%s_wep_bit" %interfaceId))
   encryptionDropdown.select_by_value("128")
   time.sleep(delay)
except Exception as e:
   sys.stderr.write("\nERROR -- Unable to find and/or click on \"Encryption (128-bit)\" pulldown for WEP")
   sys.stderr.write("\n         %s\n\n" %str(e))
   sys.exit(5)          
if VERBOSE: sys.stdout.write("done.\n")

# -----------------------------------------------------------------------------
# Clear the Key 1 text box
if VERBOSE: 
   sys.stdout.write("Clearing 128 Bit Encryption key 1 for WEP for %s interface  ... " %(band))
   sys.stdout.flush()
try:
   key1Text = driver.find_element_by_name( "wl%s_key1" %interfaceId)
   key1Text.clear()
   time.sleep(delay)
except Exception as e:
   sys.stderr.write("\nERROR -- Unable to find and/or clear the Key 1 WEP Key")
   sys.stderr.write("\n         %s\n\n" %str(e))
   sys.exit(5)          
if VERBOSE: sys.stdout.write("done.\n")

# -----------------------------------------------------------------------------
# Enter the encryption ket in the Key 1 text box
if VERBOSE:
   sys.stdout.write("Entering 128 Bit Encryption key 1 \"%s\" for WEP for %s interface  ... " %(encryptionKey,band))
   sys.stdout.flush()
try:
   key1Text.send_keys(encryptionKey)
   time.sleep(delay)
except Exception as e:
   sys.stderr.write("\nERROR -- Unable to find and/or enter 128-bit key in Key 1 text box")
   sys.stderr.write("\n         %s\n\n" %str(e))
   sys.exit(5)          
if VERBOSE: sys.stdout.write("done.\n")

# -----------------------------------------------------------------------------
# Save the changes  
if VERBOSE:
   sys.stdout.write("Saving Changes  ... ")
   sys.stdout.flush()
try:
   saveButton = driver.find_element_by_name( "save_button")
   saveButton.click()
   time.sleep(delay)
except Exception as e:
   sys.stderr.write("\nERROR -- Unable to save changes using the \"Save\" button")
   sys.stderr.write("\n         %s\n\n" %str(e))
   sys.exit(5)          
if VERBOSE: sys.stdout.write("done.\n")

# -----------------------------------------------------------------------------
# Apply the changes to the router
if VERBOSE:
   sys.stdout.write("Applying Changes  ... ")
   sys.stdout.flush()
try:
   applyButton = driver.find_element_by_name( "apply_button")
   applyButton.click()
   time.sleep(delay)
   time.sleep(delay)
except Exception as e:
   sys.stderr.write("\nERROR -- Unable to apply changes using the \"Apply Changes\" button")
   sys.stderr.write("\n         %s\n\n" %str(e))
   sys.exit(5)          
if VERBOSE: sys.stdout.write("done.\n")

# -----------------------------------------------------------------------------
# Close the web driver  
if VERBOSE:
   sys.stdout.write("Close Firefox  ... ")
   sys.stdout.flush()
try:
   driver.close()
   time.sleep(delay)
except Exception as e:
   sys.stderr.write("\nERROR -- Unable to close Firefox")
   sys.stderr.write("\n         GOK") 
   sys.stderr.write("\n         %s\n\n" %str(e))
   sys.exit(8)          
if VERBOSE: sys.stdout.write("done.\n")

# -----------------------------------------------------------------------------
# Clean exit  
if VERBOSE: sys.stdout.write("Task complete. By your command.\n")
sys.exit(0)
