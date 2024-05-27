import subprocess
import pyautogui as pya
import os
from datetime import datetime
import ctypes
import sys
import logging

def create_cache_file(path:str) -> str:
    
    # Create if doesn't exist
    if not os.path.exists(path):
        logger.info("Cache not found. Creating new.")
        with open(path, 'w') as f:
            f.write(DEFAULT_EXE_PATH)
            logger.info(f"Cache created on {path}.")
    else:
        # Populate with default if exists but it's empty
        with open(path, 'r+') as f:
            contents = f.read()
            if contents == '':
                logger.info("Empty cache found. Setting default.")
                f.write(DEFAULT_EXE_PATH)
            else:
                pass
                logger.info("Existing cached value found.")

def extract_valid_exe_path(cache_file_path:str) -> str:
    with open(cache_file_path, 'r') as f:
        f_lines = f.readlines()
        exe_path = f_lines[0]

        # Validate cached exe path
        while not os.path.exists(exe_path) or not os.path.basename(exe_path).endswith('.exe'):
            exe_path = input("The specified file does not exists or is invalid. Try again or press q to exit: ")
            if exe_path == 'q':
                quit()
            with open(cache_file_path, 'w') as f:
                f.write(exe_path)

        # logger.info("Valid path provided.")
        return exe_path

def record_save_data():
    average_core_temp = 0
    with open(DESTINATION_FILE, 'r') as f:
        lst_data = f.readlines()
        lst_data = [float(data[data.find('\t\t')+2:data.find('\t\t')+4]) for data in lst_data if is_core_temp_data(data)]
        average_core_temp = sum(lst_data)/len(lst_data)
        logger.info(f'Average core temp of {round(average_core_temp,2)}')

    with open(OUTPUT_FILE, 'a+') as o:
        o.seek(0)
        lstTemps = o.readlines()
        last_temp = 0
        if len(lstTemps) > 0:
            last_temp_recording = lstTemps[len(lstTemps)-1]
            last_temp = float(last_temp_recording[last_temp_recording.find(',')+1:])
        if last_temp != average_core_temp:
            logger.info('Saving temp.')
            o.writelines(str(datetime.now()) + ',' + str(average_core_temp) + '\r')

def is_core_temp_data(string:str) -> bool:
    return string.find('degC') != -1 and string.find('Core') != -1

def terminate_process():

    subps = subprocess.Popen(['powershell', 'get-process'], stdout=subprocess.PIPE)
    output, _ = subps.communicate()

    for line in output.splitlines():
        if 'HWMonitor' in str(line):
            logger.info('Killing HWMonitor process.')
            pid_int = int(line.split(None)[5])
            os.kill(pid_int, 9)

def is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if __name__ == "__main__":
    
    DEFAULT_EXE_PATH = r'C:\Program Files\CPUID\HWMonitor\HWMonitor.exe'
    CACHE_NAME = 'cache.txt'
    DESTINATION_FILE = 'HWMonitor.txt'
    OUTPUT_FILE = 'Temps.txt'

    # Argument handler
    logger = logging.getLogger()
    if len(sys.argv) > 1:
        if sys.argv[1] == '-v':
            logging.basicConfig(level=logging.DEBUG)
            logging.getLogger('PIL').setLevel(logging.WARNING) # Disable PIL logging debug messages

    # Request higher permissions if not granted
    logger.info('Checking for admin privileges.')
    if not is_admin():
        logger.info('Requesting admin privileges.')
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    else:
        logger.info('Admin privileges granted.')

    # Terminate HWMonitor if instance is active
    terminate_process()

    # Record the current saved data, if any
    os.chdir(os.path.dirname(__file__))
    if os.path.exists(DESTINATION_FILE):
        logger.info('Saving previous data file.')
        record_save_data()

    # Open the HWMonitor window to make sure it is visible
    create_cache_file(CACHE_NAME)
    valid_exe_path = extract_valid_exe_path(CACHE_NAME)
    logger.info('Opening HWMonitor.')
    os.popen(valid_exe_path)
    pya.sleep(2)

    # Refresh the source data
    while(True):
        try:
            Box = pya.locateOnScreen('CPUID Window.png')
        except:
            logger.error("Screenshot failed. Check admin privileges.")
        
        if type(Box) == pya.pyscreeze.Box:
            logger.info('Exporting data...')
            pya.click(Box.left + 10, Box.top + 200, clicks=2)
            pya.hotkey('ctrl', 's')
            pya.sleep(2)
            if type(pya.locateOnScreen('SAVEAS Window.png')) == pya.pyscreeze.Box:
                logger.info('Save as window detected.')
                pya.typewrite(os.path.join(os.getcwd(), DESTINATION_FILE))
                pya.press('enter')
                pya.press('left')
                pya.press('enter')
                pya.press('right')
            pya.sleep(2)
            record_save_data()
            logger.info('Waiting loop.')
            pya.sleep(60)
