import logging
import logging.config
from pathlib import Path
import sys
import os
from lib.search_file import SearchFile
from lib.wr_files import FileManagement


class TestConformance:
    def get_sessions_list(self, ftps, remote_dir, report_name, flag):
        logger = logging.getLogger("TestConformance")
        sf = SearchFile()
        mf = FileManagement()
        old_list = []
        matchedFolder = []

        # change into remote directory
        ftps.cwd(remote_dir)  

        # provide the list of available sessions
        logger.info("Retrieving the remote sessions list ...")
        matchedFolder = sf.get_folders_list(ftps, "LIST *_dat*", matchedFolder)
        
        if flag:
            # check if JSON file exist.
            # In JSON file are listed available sesssions.
            logger.info("Retrieving the local sessions list ...")
            mf.verify_file_exist(report_name, {"sessions": ""})
    
            # load a JSON object in python
            data = mf.read_json_file(report_name)
    
            for i in data["sessions"]:
                old_list.append(i)
    
            # Compare the remote list with the local one to check if a new session is available
            logger.info("Compare the remote list with the local one ...")
            
        new_sessions = list(set(matchedFolder).difference(old_list))
        return new_sessions, matchedFolder

    def write_testcase(
        self,
        test_names,
        test_messages,
        test_results,
        failure_type,
        error_messages,
        stack_trace,
    ):
        logger = logging.getLogger("TestConformance")
        test_cases = {}
        if test_results == "false":
            val = 0
            test_cases.update(
                {
                    "name": test_names,
                    "assertions": 1,
                    "failures": val,
                    "testCases": [{"name": test_messages, "failed": test_results}],
                }
            )
        else:
            val = 1
            test_cases.update(
                {
                    "name": test_names,
                    "assertions": 1,
                    "failures": val,
                    "testCases": [
                        {
                            "name": test_messages,
                            "failed": test_results,
                            "failureType": failure_type,
                            "failures": 1,
                            "errorMessage": error_messages,
                            "stacktrace": stack_trace,
                        }
                    ],
                }
            )
        return test_cases

    def write_more_testcases(
        self,
        test_names,
        test_messages,
        test_results,
        failure_type,
        error_messages,
        stack_trace,
    ):
        logger = logging.getLogger("TestConformance")
        failures = 0
        counter = 0
        test_cases = []
        for item in test_messages:
            if test_results[counter] == "false":
                test_cases.append({"name": item, "failed": test_results[counter]})
            else:
                failures += 1
                test_cases.append(
                    {
                        "name": item,
                        "failed": test_results[counter],
                        "failureType": failure_type[counter],
                        "failures": 1,
                        "errorMessage": error_messages[counter],
                        "stacktrace": stack_trace[counter],
                    }
                )
            counter += 1

        return {
            "name": test_names,
            "assertions": counter,
            "failures": failures,
            "testCases": test_cases,
        }
        
    def test_connection(self, ftp, msg, ftp_flag):
        logger = logging.getLogger("TestConformance")
        test_names = "Connect to the FTP server"
        test_messages = "Establish a connection with the FTP server"
        if msg == '':
           msg = "Connection failed, verify the credentials"
          
        if ftp is not None and ftp_flag:
            logger.info("Establish FTPES connection")
            test_results = "false"
            failure_type = ""
            error_messages = ""
            stack_trace = ""
        else:
            logger.warning(f"Failed FTPES connection")
            test_results = "true"
            failure_type = "AssertionError"
            error_messages = "FTPES not working"
            stack_trace = msg

        return self.write_testcase(
            test_names,
            test_messages,
            test_results,
            failure_type,
            error_messages,
            stack_trace,
        )
        
    def test_ch_dir(self, path, ch, flag, msg_error):
        logger = logging.getLogger("TestConformance")
        test_names = f"Directory channel {ch.replace('ch_','')}"
        test_messages = f"Check directory for channel {ch.replace('ch_','')}"
        
        if flag == "true":
            logger.info(f"Found directory for channel {ch.replace('ch_','')}: {path}")
            test_results = "false"
            failure_type = ""
            error_messages = ""
            stack_trace = ""
        else:
            logger.warning(f"Not found directory for channel {ch.replace('ch_','')}: {path} ...")
            test_results = "true"
            failure_type = "AssertionError"
            error_messages = f"Not found directory for channel {ch.replace('ch_','')}: {path} "
            stack_trace = f"{msg_error}"
           
        return self.write_testcase(
            test_names,
            test_messages,
            test_results,
            failure_type,
            error_messages,
            stack_trace,
        )

    def test_sessions_available(self, matchedFolder):
        logger = logging.getLogger("TestConformance")
        test_names = "Number of available sessions"
        test_messages = "Expected minimum number of available sessions: 1"

        if len(matchedFolder) > 0:
            logger.info(f"Found {len(matchedFolder)} available sessions in the satellite directory ...")
            test_results = "false"
            failure_type = ""
            error_messages = ""
            stack_trace = ""
        else:
            logger.warning("Not found sessions in the satellite directory ...")
            test_results = "true"
            failure_type = "AssertionError"
            error_messages = (f"Available sessions were not found")
            stack_trace = f"Found {len(matchedFolder)} sessions"

        return self.write_testcase(
            test_names,
            test_messages,
            test_results,
            failure_type,
            error_messages,
            stack_trace,
        )

    def test_satellite_directory(self, matchedFolder):
        logger = logging.getLogger("TestConformance")

        test_names = "Satellite Directory structure"
        test_messages = "The actual session directories are correctly named"

        res = [ele for ele in matchedFolder if ("_dat" in ele)]
        if len(res) == len(matchedFolder):
            test_results = "false"
            failure_type = ""
            error_messages = ""
            stack_trace = ""
        else:
            test_results = "true"
            failure_type = "AssertionError"
            error_messages = f"At least one folder name does not contain the '_dat' substring"
            stack_trace = f"Found {len(res)} items while the total number is {len(matchedFolder)}"

        return self.write_testcase(
            test_names,
            test_messages,
            test_results,
            failure_type,
            error_messages,
            stack_trace,
        )

    def test_dsdb_files_list(self, raw_files_list, nn, session_id, ch):
        logger = logging.getLogger("TestConformance")
        test_cases = []

        test_messages = []
        test_results = []
        failure_type = []
        error_messages = []
        stack_trace = []
        test_names = f"DSDB files in {ch}"
        test_messages.append(f"The channel directory contains DSDB files in {ch}")
        if len(raw_files_list) >= 1:
            logger.info(f"Found {len(raw_files_list)} DSDB file in the actual channel directory ... ")
            test_results.append("false")
            failure_type.append("")
            error_messages.append("")
            stack_trace.append("")
            
            invalid_counter = 0
            for rf in raw_files_list:
                if nn in rf and session_id in rf:
                    logger.debug(f"Valid DSDB file: {rf}. Found session ({session_id}) and unit id ({nn})")

                else:
                    logger.error(f"Invalid DSDB file: {rf}. Not found session ({session_id}) or unit id ({nn})")
                    invalid_counter += 1
             
            test_messages.append(f"DSDB file names in {ch}")      
            if invalid_counter == 0:
                   test_results.append("false")
                   failure_type.append("")
                   error_messages.append("")
                   stack_trace.append("")
            else:
                   test_results.append("true")
                   failure_type.append("AssertionError")
                   error_messages.append(f"Found {invalid_counter} invalid DSDB files")
                   stack_trace.append(f"At least one filename does not contain the specific session or unit id ({session_id}, {nn})")                   
        else:
            test_results.append("true")
            failure_type.append("AssertionError")
            error_messages.append(f"Not found raw file")
            stack_trace.append(f"Found {len(raw_files_list)} raw file in the actual channel directory")
            logger.error(f"Found {len(raw_files_list)} raw file in the actual channel directory !!! ")

        return self.write_more_testcases(
            test_names,
            test_messages,
            test_results,
            failure_type,
            error_messages,
            stack_trace,
        )

    def test_dsib_file(self, xml_files_list, nn, session_id, ch):
        logger = logging.getLogger("TestConformance")
        test_cases = []
        test_names = []
        test_messages = []
        test_results = []
        failure_type = []
        error_messages = []
        stack_trace = []
        test_names.append(f"DSIB XML file in {ch}")
        test_messages.append("The channel directory contains DSIB XML file")
        xml_file = xml_files_list[0]
        if len(xml_files_list) == 1:
            logger.info(f"Found xml file: {xml_file}")
            test_results.append("false")
            failure_type.append("")
            error_messages.append("")
            stack_trace.append("")

        else:
            logger.warn(f"Found {len(xml_files_list)} xml files ...")
            test_results.append("true")
            failure_type.append("AssertionError")
            error_messages.append(f"Not found xml files in the channel directory")
            stack_trace.append(f"Found {len(xml_files_list)} xml files")

        ## check name of files
        test_messages.append("DSIB XML file name")
        if nn in xml_file and session_id in xml_file:
            test_results.append("false")
            failure_type.append("")
            error_messages.append("")
            stack_trace.append("")
            logger.debug("The XML file name is correct ...")
        else:
            test_results.append("true")
            failure_type.append("AssertionError")
            error_messages.append(f"Invalid XML file: {xml_file}")
            stack_trace.append(f"XML file name does not contain session ({session_id}) or unit id ({nn})")
            logger.error(f"Invalid XML file: {xml_file}. Not found session ({session_id}) or unit id ({nn})")

        return xml_file, self.write_more_testcases(
            test_names[0],
            test_messages,
            test_results,
            failure_type,
            error_messages,
            stack_trace,
        )

    def test_dsdb_files_list_in_xml(self, element_names, nn, session_id, root, ch, xml_filename):
        logger = logging.getLogger("TestConformance")
        test_cases = []
        test_names = f"Items in DSIB XML file ({ch})"
        test_messages = []
        test_results = []
        failure_type = []
        error_messages = []
        stack_trace = []
        dsdb_list = []
        mf = FileManagement()
        for el in element_names:
            try:
                if el != "dsdb_list":
                    el_tag, el_text = mf.get_xml_tag(root, el)
                    logger.info(f"The {el_tag} is: {el_text} ")
                    test_messages.append(f"DSIB XML file contains {el_tag}")
                    test_results.append("false")
                    failure_type.append("")
                    error_messages.append("")
                    stack_trace.append("")
                
                # provide data size in xml file
                data_size_tag, data_size_value = mf.get_xml_tag(root, 'data_size')
                if el == "dsdb_list" and  int(data_size_value) > 0:
                    logger.info("Search DSDB files list in xml ... ")
                    dsdb_list = mf.get_all_xml_tag(root, el, "dsdb_name")

                    test_messages.append("DSIB XML file contains a DSDB list")
                    
                    if len(dsdb_list) > 0 and dsdb_list[0] != None:
                        logger.info(f"Found {len(dsdb_list)} dsdb files ...")
                        test_results.append("false")
                        failure_type.append("")
                        error_messages.append("")
                        stack_trace.append("")
                        
                        invalid_counter = 0
                        for rf in dsdb_list:
                            if nn in rf and session_id in rf:
                                logger.debug(f"Valid DSDB file name: {rf}. Found session ({session_id}) and unit id ({nn})")
                                
                            else:
                                logger.error(f"Invalid DSDB file name in xml: {rf}. Not found session ({session_id}) or unit id ({nn})")
                                invalid_counter += 1
                                
                        test_messages.append(f"DSDB file name in xml")
                        if invalid_counter == 0:
                            test_results.append("false")
                            failure_type.append("")
                            error_messages.append("")
                            stack_trace.append("")
                        else:
                            test_results.append("true")
                            failure_type.append("AssertionError")
                            error_messages.append(f"Found {invalid_counter} invalid DSDB file")
                            stack_trace.append(f"At least one filename does not contain the specific session or unit id ({session_id}, {nn})")
   
                    else:
                        logger.error(f"Not found dsdb files !!!")
                        test_results.append("true")
                        failure_type.append("AssertionError")
                        error_messages.append("Not found DSDB files")
                        stack_trace.append(f"{len(dsdb_list)} elements returned in {xml_filename}")

            except Exception as e:
                logger.error(f"Not found {el} !!! ")
                test_messages.append(f"The {el} is present in DSIB file")
                test_results.append("true")
                failure_type.append("AssertionError")
                error_messages.append(f"Not found item in XML")
                stack_trace.append(f"Element {el} was not found in XML {xml_filename}")
                continue

        return (
            self.write_more_testcases(
                test_names,
                test_messages,
                test_results,
                failure_type,
                error_messages,
                stack_trace,
            ),
            dsdb_list,
        )

    def test_download(self, filename, filetype, size, ftp_size, ch, download_flag, err_msg):
        logger = logging.getLogger("TestConformance")
        mf = FileManagement()
        test_cases = []
        test_names = f"{filetype} file download ({ch})"
        test_messages = []
        test_results = []
        failure_type = []
        error_messages = []
        stack_trace = []
        
        if download_flag:
            test_messages, test_results, failure_type, error_messages, stack_trace = self.test_file_download(
            filename,
            filetype,
            size,
            ftp_size,
            ch,
            test_messages,
            test_results,
            failure_type,
            error_messages,
            stack_trace,
            )
            
            test_messages, test_results, failure_type, error_messages, stack_trace = self.test_file_size(
            filename,
            filetype,
            size,
            ftp_size,
            ch,
            test_messages,
            test_results,
            failure_type,
            error_messages,
            stack_trace,
            )
            
            return self.write_more_testcases(
                test_names,
                test_messages,
                test_results,
                failure_type,
                error_messages,
                stack_trace,
            )
        else:
            test_messages = "Failed download"
            test_results = "true"
            failure_type = "AssertionError"
            error_messages = "The downloading is abnormally stopped"
            stack_trace = err_msg
    
            return self.write_testcase(
                test_names,
                test_messages,
                test_results,
                failure_type,
                error_messages,
                stack_trace,
            )           
           
    def test_file_download(
        self,
        filename,
        filetype,
        size,
        ftp_size,
        ch,
        test_messages,
        test_results,
        failure_type,
        error_messages,
        stack_trace,
    ):
        logger = logging.getLogger("TestConformance")
        mf = FileManagement()

        test_messages.append(f"{filetype} file is downloaded")
        if mf.verify_path_exist(filename):
            test_results.append("false")
            failure_type.append("")
            error_messages.append("")
            stack_trace.append("")
            #logger.info(f"Found file: {filename} ")

        else:
            test_results.append("true")
            failure_type.append("AssertionError")
            error_messages.append("Failed download")
            stack_trace.append(f"Not found file: {filename}")
            logger.debug(f"No such file: {filename} ")

        return test_messages, test_results, failure_type, error_messages, stack_trace

    def test_file_size(
        self,
        filename,
        filetype,
        size,
        ftp_size,
        ch,
        test_messages,
        test_results,
        failure_type,
        error_messages,
        stack_trace,
    ):
        logger = logging.getLogger("TestConformance")
        mf = FileManagement()
        
        test_messages.append(f"{filetype} file size ({ch})")
        if '.xml' in filename:
            if size == ftp_size:
                test_results.append("false")
                failure_type.append("")
                error_messages.append("")
                stack_trace.append("")
                #logger.info(f"Finished transferring (local file {size} bytes, ftp file {ftp_size} bytes) ")
            else:
                test_results.append("true")
                failure_type.append("AssertionError")
                error_messages.append("Failed download")
                stack_trace.append(f"No finished transferring (local file {size} bytes, ftp file {ftp_size} bytes)")
                logger.debug(f"No finished transferring (local file {size} bytes, ftp file {ftp_size} bytes)")
        else:
            if size == 1024:
                test_results.append("false")
                failure_type.append("")
                error_messages.append("")
                stack_trace.append("")
                #logger.info(f"Finished transferring (local file {size} bytes, ftp file {ftp_size} bytes) ")
            else:
                test_results.append("true")
                failure_type.append("AssertionError")
                error_messages.append("Failed download")
                stack_trace.append(f"No finished transferring (local file {size} bytes, ftp file {ftp_size} bytes)")
                logger.warn(f"No finished transferring (local file {size} bytes, ftp file {ftp_size} bytes)")

        return test_messages, test_results, failure_type, error_messages, stack_trace
