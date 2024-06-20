"""
###############################################################################
#
# Test Conformance EDRS
# How to: Establish FTPES connection, get new files and download them for EDRS
#   
###############################################################################

"""

import argparse
import logging
import logging.config
import ssl
#from ftplib import FTP_TLS
from ftplib import FTP
import time
from datetime import datetime
from pathlib import Path
import sys
import re
import json
import random
import os

#from requests.exceptions import SSLError
from lib.interface import Interface
from lib.search_file import SearchFile
from lib.download import Download
from lib.wr_files import FileManagement
from lib.ftp import FTP_Connection
from test.test import TestConformance
from test.report import Results

MAIN_PATH = os.path.dirname(sys.argv[0])
FTP_FLAG = False

def main():
    # init
    test_suites = []
    test_cases = {}
    xml_file = ''
    raw_file = ''
    report_name = os.path.join(MAIN_PATH, 'sessions_list.json')
    remote_path_credential = '/download/vsftp/'
    total_results = 0
    pending_results = 0
    failed_results = 0 
    it = Interface()
    sf = SearchFile()
    dw = Download()
    mf = FileManagement()
    rp = Results()
    ts = TestConformance()
    cn = FTP_Connection()
    dsdb_size = 0
    xml_size = 0
    ftp_dsdb_size = 0
    ftp_xml_size = 0
    new_sessions = []
    matchedFolder = []
    ftps = None
    msg = ""
    dsdb_flag = False
    xml_flag = False
    data_size_value = 0
    error_message_dsib = ''
    error_message_dsdb = ''
    msg_error_dir = ''
    xml_file_path = ''
    
    # get args from command line
    args = it.execute_command_line()
    
    # Configure Log
    logging = it.configure_log(args, MAIN_PATH)
    logger = logging.getLogger('Main')
    
    logger.info('Executing Conformance test ...')
    logger.info('version 1.0')
    logger.info('Loading credential ... ')
    
    # return credentioals (user, password, host, etc ... )
    (env, ca_ctr, client_ctr, key, channel, local_dir, auth, check_sessions) = it.get_args(args)
    host, user, password, remote_dir, port, env_name = it.get_config(env)
    
    # connect to FTPES
    logger.info('************************************************')
    logger.info('*               EXECUTING TEST                 *')
    logger.info('************************************************')
    
    ## We need to initialize this SSL context with self-sign certificate.
    
    if auth == "encrypted":  
       logger.info(f'Authentication is encrypted ...')
       ctx, msg = cn.load_cert(ca_ctr, client_ctr, key)
       ftps, FTP_FLAG = cn.connected_ftpes(host, user, password, port, key, ca_ctr, client_ctr, ctx)
    else:     
       # Connecting to the FTP server via user account login (without certificates)
       logger.info(f'Authentication is not encrypted ...')
       ftps, FTP_FLAG = cn.connected_ftp(host, user,password)
       
    # write result of test connectivity in JSON file
    test_suites.append(ts.test_connection(ftps, str(msg), FTP_FLAG))    
    
    started_test = datetime.utcnow()  
    started_test_str = started_test.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + 'Z'  
    
    # Create download directory
    if local_dir == "":
       timestamp = int(datetime.timestamp(started_test))
       local_dir = "{}/data_{}".format(os.path.dirname(sys.argv[0]), str(timestamp))
    
    if not mf.verify_path_exist(local_dir):
       logger.debug('Created local download directory ... ')
       mf.create_folder(local_dir)
       
    logger.debug(f"Local downloads folder is: {local_dir}")
    
    if ftps is not None and FTP_FLAG:  
       ## Provide the list of sessions in the satellite directory
       # Change the current working directory
       logger.info(f"Changing the working directory: {remote_dir} ...")       
       
       # retrieve new sessions list and test it
       new_sessions, matchedFolder = ts.get_sessions_list(ftps, remote_dir, report_name, check_sessions)
       
       logger.info("Checking the available sessions ...")
       test_suites.append(ts.test_sessions_available(matchedFolder))
       if len(matchedFolder) > 0:
          test_suites.append(ts.test_satellite_directory(matchedFolder))
       
       # Check if a new session is available 
       logger.debug(f"Found {len(new_sessions)} new sessions ...")
       
       # Chosen a random file from new file list and download it
       if len(new_sessions) != 0 :
          # check sessions name
          logger.info("Choose randomly a session ... ")
          selected_random_session = random.choice(new_sessions)
          
          logger.info(f"The selected session is: {selected_random_session}")
          logger.info(f"Changing the working directory: {remote_dir}{selected_random_session} ...")
          
          nn = selected_random_session.split('_')[1]
          logger.debug(f"Station unit ID is: {nn} ...")
          
          session_id = selected_random_session.split('_')[2]
          logger.debug(f"The session ID is: {session_id} ...")
          
          ## change directory in /selected_random_session
          try:
             ftps.cwd(selected_random_session)
          except Exception as e:
             logger.error(e)
             
          ## select channel (1 or 2)
          if channel != "all":
             channels = [channel]
          else:
             channels = ["ch_1","ch_2"]
          
          for ch in channels:
              logger.info(f"Execute test for {ch}")
              logger.info(f"Changing the working directory: {remote_dir}{selected_random_session}/{ch} ...")
              raw_files_list = []
              xml_files_list = []
              try:
                 ftps.cwd(ch)
                 xml_files_list = sf.get_folders_list(ftps, 'LIST *.xml*', xml_files_list) 
                 test_suites.append(ts.test_ch_dir(remote_dir + selected_random_session + '/' + ch, ch, "true", msg_error_dir))    
              except Exception as e:
                  logger.error(e)
                  msg_error_dir = str(e)
                  test_suites.append(ts.test_ch_dir(remote_dir + selected_random_session + '/' + ch, ch, "false", msg_error_dir))
                  
                 
              if len(xml_files_list) > 0:
                 #test dsib file
                 try:
                    xml_file, result_string = ts.test_dsib_file(xml_files_list, nn, session_id, ch)
                    ftp_xml_size = ftps.size(xml_file)
                    test_suites.append(result_string)
                 except Exception as e:
                    logger.error(e)
                 
                 # download xml file
                 try:
                    xml_size, xml_flag, error_message_dsib = dw.download_files(ftps, local_dir, xml_file, ftp_xml_size)
                    xml_file_path = os.path.join(local_dir, xml_file)
                 except Exception as e:
                    logger.error(e)
                 
                 # read xml file
                 if xml_flag:
                    try:
                       logger.info(f"The DSIB file is downloaded: {xml_file_path} ")
                       root = mf.read_xml_file(xml_file_path)
                       
                       element_names = ['session_id','time_start','time_stop','time_created','time_finished','data_size','dsdb_list']
                       result_string, dsdb_list = ts.test_dsdb_files_list_in_xml(element_names, nn, session_id, root, ch, xml_file)
                       test_suites.append(result_string)
                       
                       # provide data size in xml file
                       data_size_tag, data_size_value = mf.get_xml_tag(root, 'data_size')
                    except Exception as e:
                       logger.error(e)
                       
                 # check download xml file
                 test_suites.append(ts.test_download(xml_file_path, 'DSIB', xml_size, ftp_xml_size, ch, xml_flag, error_message_dsib))
                 
                 # test dbds list
                 if int(data_size_value) > 0:
                   try:
                       logger.debug(f"The data size is: {data_size_value} bytes. Channel is not empty. ")
                       raw_files_list = sf.get_folders_list(ftps, 'LIST *.raw*', raw_files_list)
                       test_suites.append(ts.test_dsdb_files_list(raw_files_list, nn, session_id, ch))
                       
                       if dsdb_list == raw_files_list:
                         logger.info("The raw files list is completed ...")
                         raw_file, ftp_dsdb_size = sf.search_file(ftps, dsdb_list)
          
                       else:
                         logger.warn("The raw files list is not completed ...")
                         raw_file, ftp_dsdb_size = sf.search_file(ftps, raw_files_list)
                         
          
                       # download raw file
                       dsdb_size, dsdb_flag, error_message_dsdb = dw.download_files(ftps, local_dir, raw_file, ftp_dsdb_size)
                       dsdb_file_path = os.path.join(local_dir, raw_file)
                       logger.info(f"The DSDB file is downloaded: {dsdb_file_path}")
                
                       # check download raw file
                       test_suites.append(ts.test_download(dsdb_file_path, 'DSDB', dsdb_size, ftp_dsdb_size, ch, dsdb_flag, error_message_dsdb))
                       
                   except Exception as e:
                       logger.error(e)
                 else:
                     logger.warn(f"In the xml file the data size is: {int(data_size_value)} ")                                                 
                 # change folder
                 ftps.cwd('../')  
              else:  
                 if msg_error_dir == '':
                    logger.warn(f"Channel {ch.split('_')[1]} is empty !!!")
                 # change folder
                 ftps.cwd('../')                             
       else:
          logger.warning("Not found new sessions ...")
          
       # write new sessions in JSON file
       if check_sessions:
          mf.write_json_file("sessions_list.json", {"sessions":matchedFolder,"new_sessions_list":new_sessions, "xml_file":xml_file, "raw_file":raw_file})

    mf.clear_folder(local_dir)
    mf.remove_folder(local_dir)
    
    collection = os.path.basename(__file__)   
    rp.write_report(test_suites, started_test_str, remote_dir, collection, env.split("/")[-1], env_name)  
    
    if ftps is not None and FTP_FLAG:     
       ftps.quit()
       ftps.close()
       
    # verify if all download folder are removed.
    path = os.path.dirname(sys.argv[0])
    data_folders = [filename for filename in os.listdir(path)  if filename.startswith("data_")]
    for el in data_folders:
       os.system("rm -rf " + path + "/" + el)
    
    # connect to FTPES
    logger.info('************************************************')
    logger.info('*               COMPLETED TEST                 *')
    logger.info('************************************************')


             
             
if __name__ == "__main__":
    main()
    

