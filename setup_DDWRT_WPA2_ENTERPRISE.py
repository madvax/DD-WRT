#!/usr/bin/env python3

# This python 3 script sets up a DD-WRT Access Point to use 
# WPA2 Enterprise Security using a RADIUS Server
# See the usage funcftion for more details 

# Theory of Operation
#    Import the selenium site library, if installed
#    Validate and process any command line arguments
#    Load the Selenium Firefox web driver a.k.a. geckodriver 
#    Load the wrireless router DD-WRT web interface into the web driver   
#    Navigate to Wriless Settings then Wireless Security page
#    Select WPA2 Enterprise (may take a few seconds to load this page)
#    Select Encryption (TKIP, AES)
#    Clear and enter RADIUS IPv4 Address
#    Clear and enter RADIUS Port number 
#    Clear and enter RADIUS Shared Secret 
#    Save and apply new settings 
#    Close the web driver 
#    Clean exit

# H. Wilson, November 2017 

# -----------------------------------------------------------------------------
# Imports
import sys, os, time                                    # standard library imports
from getopt  import getopt                              # used to process command line arguments
import socket                                           # Used to validate IPv4 IP Address
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
VERSION       = "1.2.0" # Version number for this test case
VERBOSE       = False    # Verbose flag, when true generates additional output
DEBUG         = False    # Degug flag, when true generates debug output
FIRST         =  0       # Generic first element index
LAST          = -1       # Generic last element index 
ME            = os.path.split(sys.argv[FIRST])[LAST]        # Name of this file
MY_PATH       = os.path.dirname(os.path.realpath(__file__)) # Path for this file
username      = "test"                                            # DD-WRT Username 
password      = "testtest"                                        # DD-WRT Password
url           = "https://%s:%s@192.168.1.1" %(username, password) # DD-WRT URL with embedded credentials 
delay         = 3  # Generic time dela (in seconds) to accomodate for web page loading times      
presharedKey  = "0123abcdEFGH`~!?.,@#$%^&*-=_+;:' '\" \"< >[ ]{ }( )|/\\"  # Default preshared key 
interfaceId   = "0"           # Defaul wireless interface (0->2.4GHz, 1->5GHz) 
band          = "2.4GHz"      # Default Band, should align with Default wireless interface  
encryption    = "aes"         # default encryption 
wirelessTabXPATH         = "/html/body/div/div/div[1]/div[2]/div/ul/li[2]/a"               # XPATH to the Wireless Tab
wirelessSecurityTabXPATH = "/html/body/div/div/div[1]/div[2]/div/ul/li[2]/div/ul/li[3]/a"  # XPATH to the Wireles Security Tab
# RADIUS_SHARED_SECRET = "H5ZG8t8i&gX3s#!zX1!p2ykIqR3T5Ge" # \
# RADIUS_IP_1 = "104.154.91.253"                           #  > Jump Cloud Radius Settings
# RADIUS_IP_2 = "104.196.54.120"                           # /
RADIUS_SHARED_SECRET = "testing123"            # Local RADIUS settings for the Access Point 
RADIUS_IP_1          = ["192","168","1","128"] # For additional RADIUS Settings see:  /etc/freeradius/radiusd.conf
RADIUS_PORT          = "1812"                  # or see your RADIUS server's configurations 

# -----------------------------------------------------------------------------
# Native functions 

#------------------------------------------------------------------------------ usage()
def usage():
   """ usage() Displays a usage message on standard output """ 
   print("""
%s, Version %s
 
SUMARY: Sets up a DD-WRT 3.0 Access Point to use WPA2 Enterprise Security (RADIUS) 

USAGE: %s [OPTIONS]

OPTIONS:
  -h --help         Show this help message

  -v --verbose      Print verbose output to stdout

  -d --debug        Operate script in debug mode, implies verbose

  -i --interface=   The wireless interface to use, either 2 or 5 for 
                    2.4GHz and 5GHz respectively.       
                    Default is 2 for the 2.4 GHz interface   

  -s --secret=      The shared secret between the Radius server and Access Point
                    Default secret: %s  

  -e --encryption=  The encryption to use: aes or tkip
                    Default is %s

  -a --address=     The IP Address of the Radius Server 
                    Default is %s.%s.%s.%s    

  -p --port=       The Port number of the rasius service running on the 
                   Radius server, Default is %s 

DEFINED EXIT CODES:
  0 - Successful completion of the task
  1 - Unable to import the Selenium site package    
  2 - Bad or missing command line arguments 
  3 - Bad interface specified, must be either 2 or 5
  4 - Bad encryption key specified, must be 8 - 79 ASCII Enocded characters
  5 - Bad encrpption specified, must be 'aes' or 'tkip' 
  6 - Bad RADIUS IP Address specified
  7 - Bad RADIUS Port nuber specified
  8 - Unable to locatet and/or interact with web page element
  9 - Unable to open the Firefox web driver for Selenium (geckodriver)
 10 - Unable to access the URL, Check netowrk connection
 11 - Unabel to close the Firefox web driver for Selenium   
   """ %(ME, VERSION, ME, RADIUS_SHARED_SECRET, encryption, RADIUS_IP_1[0], RADIUS_IP_1[1], RADIUS_IP_1[2], RADIUS_IP_1[3], RADIUS_PORT) )
   return

# ----------------------------------------------------------------------------- is_ascii()
def is_ascii(s):
   """ The poor man function that checks to see if all characgters in s are 
       valid ascii characters.
       returns True | False  """ 
   result = False
   try: 
      result = all(ord(c) < 128 for c in s)
   except: pass   
   return result 

# -----------------------------------------------------------------------------
# Process command line arguments
try: arguments = getopt(sys.argv[1:]         , 
                        "hvdi:k:e:s:a:p:"    , 
                        [ 'help'        ,
                          'verbose'     , 
                          'debug'       , 
                          'interface='  ,
                          'secret='     ,
                          'encryption=' , 
                          'address'     ,
                          'port'        ]    )   
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
   if arg[FIRST]== "-d" or arg[FIRST] == "--debug":
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
# --- Check for RADIUS Shared Secret option                   
for arg in arguments[FIRST]:
   if arg[FIRST]== "-s" or arg[FIRST] == "--secret":
      try: 
         if len(arg[LAST]) >= 8 and len(arg[LAST]) <= 79: # DD-WRT limit, FreeRADIUS supports 8k key length
            if is_ascii(arg[LAST]):  # Check to see if all characters are valid ASCII 
               RADIUS_SHARED_SECRET = arg[LAST]
            else:   
               raise ValueError("Key is not valid ASCII characters")
         else:
            raise ValueError("Wrong size key, key length: %s, should be (8 or more) and (79 or less)" %len(arg[LAST])) 
      except ValueError as e:
         sys.stderr.write("\nERROR -- Bad RADIUS Shared Secret specified: \'%s\'\n         Valid key must be valid ASCII, size [8-79]" %arg[LAST])
         sys.stderr.write("\n         %s\n\n" %str(e))
         sys.exit(4)          
# --- Check for an encryption option                   
for arg in arguments[FIRST]:
   if arg[FIRST]== "-e" or arg[FIRST] == "--encryption":
      try: 
         enc = arg[LAST].lower()
         if enc == "aes" or enc == "tkip":
            encryption = enc
         else:
            raise ValueError("Wrong encryption: %s, should be aes or tkip" %arg[LAST]) 
      except ValueError as e:
         sys.stderr.write("\nERROR -- Bad encryption specified: \'%s\'\n         Valid encryption must be aes or tkip" %arg[LAST])
         sys.stderr.write("\n         %s\n\n" %str(e))
         sys.exit(5)
# --- Check for a valid IP Address 
#     We'll need to enter the IP address in to four text boxes, one for each octet. So, we 
#     need to split the address up into four strings. This is a good a time as any.                   
for arg in arguments[FIRST]:
   if arg[FIRST]== "-a" or arg[FIRST] == "--address":
      try:
         temp         = socket.inet_aton(arg[LAST])
         temp_address = arg[LAST].split('.')
         if len(temp_address) != 4:
            raise ValueError("IP Address needs four (4) octets, %d provided" %len(temp_address))
         else: 
            for i in temp_address:
               i = int(i)  
               if i < 0 or i > 255:
                  raise ValueError("IP Address octets must be between (0-255)")
               else: 
                  pass
         RADIUS_IP_1 = temp_address
      except Exception as e:
         sys.stderr.write("\nERROR -- Bad RADIUS IP Adress specified: \'%s\'\n         Address must be a valid IPv4 Address" %arg[LAST])
         sys.stderr.write("\n         %s\n\n" %str(e))
         sys.exit(6)
# --- Check for a "port" or "-p" option 
for arg in arguments[FIRST]:
   if arg[FIRST]== "-p" or arg[FIRST]== "--port":
      try:
         try:
            tryPort = int(arg[LAST])
            if tryPort < 65535 and tryPort > 1024:
               RADIUS_PORT = tryPort
            else:
               raise ValueError("Invalid port specified \"%s\", port must be an integer between (1024-65535)." %arg[LAST] )
         except:
            raise ValueError("Invalid port specified \"%s\", port must be an integer between (1024-65535)." %arg[LAST])
      except Exception as e:
         sys.stderr.write("\nERROR -- Bad RADIUS port number specified: \'%s\'\n         Port number must be an integer between (1024-65535)" %arg[LAST])
         sys.stderr.write("\n         %s\n\n" %str(e))
         sys.exit(7)

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
   sys.exit(9)
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
   driver.close() 
   sys.exit(10)          
if VERBOSE: sys.stdout.write("done.\n")

# -----------------------------------------------------------------------------
# Navigate to the wireless page in the DD-WRT web interface 
if VERBOSE:
   sys.stdout.write("Selecting Wrieless Tab ... ")
   sys.stdout.flush()
try:
   wirelessTab = driver.find_element_by_xpath(wirelessTabXPATH)
   wirelessTab.click()
except Exception as e:
   sys.stderr.write("\nERROR -- Unable to find and/or click on \"Wireless\" tab")
   sys.stderr.write("\n         %s\n\n" %str(e))
   driver.close()
   sys.exit(8)          
if VERBOSE: sys.stdout.write("done.\n")

# -----------------------------------------------------------------------------
# Navigate to the Wireless Security submenu in the DD-WRT web interface  
if VERBOSE:
   sys.stdout.write("Selecting Wrieless Security Submenu Tab ... ")
   sys.stdout.flush()
try:
   wirelessSecurityTab = driver.find_element_by_xpath(wirelessSecurityTabXPATH)
   wirelessSecurityTab.click()
except Exception as e:
   sys.stderr.write("\nERROR -- Unable to find and/or click on \"Wireless Security\" tab")
   sys.stderr.write("\n         %s\n\n" %str(e))
   driver.close()
   sys.exit(8)          
if VERBOSE: sys.stdout.write("done.\n")

# -----------------------------------------------------------------------------
# Select WPA2 Enterprise as the Security Mode  
if VERBOSE:
   sys.stdout.write("Selecting WPA2 Personal for %s interface  ... " %band)
   sys.stdout.flush()
try:
   securityModeDropdown = Select(driver.find_element_by_name( "wl%s_security_mode" %interfaceId))
   securityModeDropdown.select_by_visible_text("WPA2 Enterprise")
   time.sleep(delay)
except Exception as e:
   sys.stderr.write("\nERROR -- Unable to find and/or click on \"Security Mode\" pulldown for WPA2 Enterprise")
   sys.stderr.write("\n         %s\n\n" %str(e))
   driver.close() 
   sys.exit(8)          
if VERBOSE: sys.stdout.write("done.\n")

# -----------------------------------------------------------------------------
# Select encryption AES or TKIP 
if VERBOSE:
   sys.stdout.write("Selecting Encryption for WPA1 for %s interface  ... " %band)
   sys.stdout.flush()
try:
   encryptionDropdown = Select(driver.find_element_by_name("wl%s_crypto" %interfaceId))
   encryptionDropdown.select_by_value(encryption)
except Exception as e:
   sys.stderr.write("\nERROR -- Unable to find and/or click on \"Encryption\" pulldown for WPA2 Enterprise")
   sys.stderr.write("\n         %s\n\n" %str(e))
   driver.close()
   sys.exit(8)          
if VERBOSE: sys.stdout.write("done.\n")

# -----------------------------------------------------------------------------
# Clear and enter the IPv4 RADIUS Addresses text boxes
if VERBOSE: 
   sys.stdout.write("Clearing and entering the RADIUS Server IPv4 address for %s interface  ... " %(band))
   sys.stdout.flush()
for i in ("0", "1", "2", "3"): 
   try: 
      ipAddressText = driver.find_element_by_name( "wl%s_radius_ipaddr_%s" %(interfaceId, i))
      ipAddressText.clear()
      ipAddressText.send_keys(RADIUS_IP_1[int(i)])
   except Exception as e:
      sys.stderr.write("\nERROR -- Unable to find and/or clear RADIUS IP Address text box(%s)" %i)
      sys.stderr.write("\n         %s\n\n" %str(e))
      driver.close() 
      sys.exit(8)          
if VERBOSE: sys.stdout.write("done.\n")

# -----------------------------------------------------------------------------
# Clear and enter the port number RADIUS Addresses text boxes
if VERBOSE: 
   sys.stdout.write("Clearing and entering the RADIUS Server port number for %s interface  ... " %(band))
   sys.stdout.flush()
try: 
   portText = driver.find_element_by_name("wl%s_radius_port" %(interfaceId))
   portText.clear()
   portText.send_keys(RADIUS_PORT)
except Exception as e:
   sys.stderr.write("\nERROR -- Unable to find and/or clear RADIUS text box")
   sys.stderr.write("\n         %s\n\n" %str(e))
   driver.close() 
   sys.exit(8)          
if VERBOSE: sys.stdout.write("done.\n")

# -----------------------------------------------------------------------------
# Enter the RADIUS Shared Secret into the text box
if VERBOSE:
   sys.stdout.write("Clear an enter the RADIUS Shared Secret \"%s\" for %s interface  ... " %(presharedKey,band))
   sys.stdout.flush()
try:
   sharedSecretText = driver.find_element_by_name("wl%s_radius_key" %(interfaceId))
   sharedSecretText.clear()
   sharedSecretText.send_keys(RADIUS_SHARED_SECRET)
   if DEBUG: 
      # Visual Check of the RADIUS shared secret if operating in debug mode  
      sharedSecretUnmask = driver.find_element_by_name("wl%s_radius_unmask" %(interfaceId))
      sharedSecretUnmask.click()
      time.sleep(delay)
      sharedSecretUnmask.click()
except Exception as e:
   sys.stderr.write("\nERROR -- Unable to find and/or interact with the RADIUS Shared Secret text box")
   sys.stderr.write("\n         %s\n\n" %str(e))
   driver.close()
   sys.exit(8)          
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
   time.sleep(delay)
except Exception as e:
   sys.stderr.write("\nERROR -- Unable to save changes using the \"Save\" button")
   sys.stderr.write("\n         %s\n\n" %str(e))
   driver.close()
   sys.exit(8)          
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
   time.sleep(delay)
except Exception as e:
   sys.stderr.write("\nERROR -- Unable to apply changes using the \"Apply Changes\" button")
   sys.stderr.write("\n         %s\n\n" %str(e))
   driver.close() 
   sys.exit(8)          
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
   sys.exit(11)          
if VERBOSE: sys.stdout.write("done.\n")

# -----------------------------------------------------------------------------
# Clean exit  
if VERBOSE: sys.stdout.write("Task complete. By your command.\n")
sys.exit(0)
