import logging
import logging.config
import json
import socket
#from datetime import datetime
#from pathlib import Path
#import sys
#import os

class Results:
    def write_report(self, results, started_test, sat_dir, collection, env_filename, env_name):
        logger = logging.getLogger("Results")
        logger.info("Results ...")
        hostname, host_ip = self.get_host()
        # ----- Save the results in the reports
        dictionary = self.create_dict(started_test, env_filename, env_name, sat_dir, collection.replace('_', ' '), results)
        self.write_json_report(dictionary, 'cba_testSuiteResults.json')
        
# Function to display hostname and IP address 
    def get_host(self): 
      logger = logging.getLogger("Results")
      try: 
         host_name = socket.gethostname() 
         host_ip = socket.gethostbyname(host_name) 
         # logger.info("Hostname :  ",host_name) 
         # logger.info("IP : ",host_ip) 
      except: 
         logger.debug("Unable to get Hostname and IP")
         
      return host_name, host_ip

    def create_dict(self, started_date, env_filename, env_name, sat_dir, collection, sample):
            failed_tests_number = 0
            testcases_number = 0
            for el in sample:
              for val in el['testCases']:
                 testcases_number += 1
                 if val['failed'] == "true":
                    failed_tests_number += 1
                    
                
            d = {"startedAt":started_date, "testResults":[{
                 "collection": {"name":collection}, 
                 "environment": {"name":env_name, "fileName":env_filename}, 
                 "run": {"stats": {"iterations":{"total":1, "pending": 0, "failed": 0}, "requests":{"total":len(sample), "pending": 0, "failed": 0},"assertions":{"total":testcases_number, "pending": 0, "failed": failed_tests_number}}}, 
                 "testSuites": sample}]}
                 
            return d

    def write_json_report(self, d, report_name):
        with open(report_name, 'w') as fp:
            json.dump(d, fp)
            return d
            