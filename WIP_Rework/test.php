<?php

global $globalANSI;
global $caseNumber;
global $removeDUPS;
//include_once("axlfunctions.php");

error_reporting(E_ERROR | E_PARSE);

$removeDUPS = array();
$globalANSI = true;
colorText("boldCyan","Black","\r\nUse ANSI codes for color [Y]es/[n]o?\r\n");
$retValue = readLine();

if (strlen($retValue)==0) {$retValue="Y";colorText("boldWhite","Black","$retValue\r\n");}

if ($retValue=="n") {$globalANSI = false;}


/*
		Menu
		[1] Pull CUCM/CUC/IM&P/UCCX logs
		[2] Analyze system for configuration changes (Audit Logs/Tomcat Logs/DBL Logs) [CUCM-only]
		[3] Analyze system for a particular phone events (CUCM logs/filtered) [CUCM-only]
		[4] Analyze system for a call (CDR/CUCM/filtered) [CUCM-only]

*/


//$caseNumber = pullCUCMLogsMenu();
//colorText("White","Black","\r\nDownloaded files can be found in the '$caseNumber' directory.\r\n\r\n");

$cucmList = TUI_getCredentials();

	while (1)
	{
			//colorClearScreen();
			colorText("boldCyan","Black", "\r\n\rnOptanix IPT Menu\r\n");
			colorText("Cyan","Black","----------------\r\n");
			colorText("Cyan","Black", "\r\n");
			colorText("Cyan","Black", "[1]	Pull logs\r\n");					// DONE
			colorText("Cyan","Black", "[2]	Investigate system changes\r\n");	// DONE
			colorText("Cyan","Black", "[3]	Investigate SIP Trunk OOS\r\n");   		// CUCM logs/Event logs/OOS+ISV+Device Resets
			colorText("Cyan","Black", "[9]	RTMT Report\r\n");   		// CUCM logs/Event logs/OOS+ISV+Device Resets
			//colorText("Cyan","Black", "[4]	Investigate Phone DeRegistration\r\n");	// CUCM logs/Event logs/Phone HTTP
			//colorText("Cyan","Black", "[5]	Investigate phone call cause-codes\r\n");				// CUCM logs/CDR/call-identifiers
			//colorText("Cyan","Black", "[6]	Pull CDR for CaseSentry/MAP team\r\n");		//

			$retValue = readLine("");

			switch ($retValue)
			{
				case "1":
				pullCUCMLogsMenu();
				break;

				case "2":
				getLastChanges(false);
				break;

				case "3":
				SIPTrunkOOS();
				break;

				case "4":
				//PhoneDereg();
				break;

				case "A":
				getLastChanges(true);
				break;

				case "0":
				$includeList[0] = "Processor";
				$includeList[1] = "Memory";
				rtmtGetCpuAndMemoryRequest("getCpuAndMemoryRequest", $includeList);
				break;

				case "9":
				rtmtGetCpuAndMemoryRequest("getPhoneSummary", $includeList, "Phone Summary");
				rtmtGetCpuAndMemoryRequest("getPartitionInfoRequest", $includeList, "Partition Summary");
				rtmtGetCpuAndMemoryRequest("getCtiManagerInfoRequest", $includeList, "CTI Manager Summary");
				rtmtGetCpuAndMemoryRequest("getDbChngNotifyRequest", $includeList, "Database Replication Summary");
				rtmtGetCpuAndMemoryRequest("getServiceInfoRequest", $includeList, "Services Summary");
				//rtmtGetCpuAndMemoryRequest("getRegisteredDeviceRequest", $includeList, "Registered Phone Summary");
				rtmtGetCpuAndMemoryRequest("getSdlqueueInfoRequest", $includeList, "SDL Queue Summary");
				rtmtGetCpuAndMemoryRequest("getTftpInfoRequest", $includeList, "TFTP Summary");
				rtmtGetCpuAndMemoryRequest("getHeartbeatInfoRequest", $includeList, "Heartbeat Summary");
				rtmtGetCpuAndMemoryRequest("getCallActivityRequest", $includeList, "Call Activity Summary");
				rtmtGetCpuAndMemoryRequest("getGatewayActivityRequest", $includeList,  "Gateway Activity Summary");

				break;


			}
	}
			///  Check INPUT

//pullCUCMLogsMenu();exit;
//getLastChanges();


function rtmt()
{

}

function rtmtGetCpuAndMemoryRequest($astRequest, $includeList, $title)
{
			global $cucmPub, $cucmWebAdmin, $cucmWebPassw, $caseNumber,$cucmList,$removeDUPS;

            //curl_setopt($ch, CURLOPT_URL, "https://$CCMIP/ast/ASTIsapi.dll?GetClusterInfoList");
            $ch = curl_init();
		    curl_setopt($ch, CURLOPT_URL, "https://$cucmPub/ast/ASTIsapi.dll?GetPreCannedInfo&Items=$astRequest");


			$AXLHeader = array("Content-Type: text/xml; charset=utf-8",
					"Authorization: Basic ".base64_encode("$cucmWebAdmin:$cucmWebPassw"),
					"Content-Length: ".strlen($SVCRequest),
													$SVCHeaderSuffix);

			curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
			curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, false);
			curl_setopt($ch, CURLOPT_HTTPHEADER, $AXLHeader);
			curl_setopt($ch, CURLOPT_POST, 1);
			curl_setopt($ch, CURLOPT_POSTFIELDS, $SVCRequest);
			curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
			curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 15);
			curl_setopt($ch, CURLOPT_TIMEOUT, 15);

			$retValue = curl_exec($ch);

			//$astRequest = str_replace("Request","Reply", $astRequest);

			$retValue = strBetweenI($retValue, "<PreCannedReplies", "</PreCannedReplies>");
			//echo $retValue;exit;

			$xml = new SimpleXMLElement($retValue);

			$retValue = ""; $counter = 0;

			foreach ($xml->children() as $preCannedReply)
			{
				foreach ($preCannedReply->children() as $hostNode)
				{


					// Iterate through each host node
					colorText("boldCyan","black","\r\n\r\nNode: {$hostNode['Name']} $title\r\n-------------------------------------------------------------------\r\n");


					// Iterate through each nodes attributes
					foreach ($hostNode->attributes() as $hostNodeAttName => $hostNodeAttValue)
					{
						colorText("cyan","black","[$hostNodeAttName]: $hostNodeAttValue\r\n");
					}

					foreach ($hostNode->children() as $infoRequest)
					{
						// Iterate through each host's Cpu/Memory list
						if ( in_array($infoRequest->getName(), $includeList) || count($includeList)==0 )
						{
							colorText("Cyan","black","\r\n\r\n[{$infoRequest->getName()}]\r\n");

							// Iterate through each attribute
							foreach ($infoRequest->attributes() as $infoAttribute => $infoAttributeValue)
							{
								// If attribute is "ServiceStatus" or "ElapsedTime", convert over
								if ( $infoAttribute=="ServiceStatus" )
								{
									switch ($infoAttributeValue)
									{
										case '1':
										$infoAttributeValue="Running";
										break;

										case '2':
										$infoAttributeValue="Not Running";
										break;

									}
								}

								if ( $infoAttribute=="ReplicationStatus" )
								{
									switch ($infoAttributeValue)
									{
										case '1':
										$infoAttributeValue="Running";
										break;

										case '2':
										$infoAttributeValue="Not Running";
										break;

									}
								}

								if ( $infoAttribute=="ElapsedTime" )
								{

									$infoAttributeValue = convert_seconds($infoAttributeValue);
								}

								colorText("Cyan","black","{$infoAttribute}: [{$infoAttributeValue}]\r\n");
							}
						}
					}
				}
			}

			return $retValue;
}


function PhoneDereg()
{
	global $cucmPub, $cucmWebAdmin, $cucmWebPassw, $caseNumber,$cucmList,$removeDUPS;
	$removeDUPS = array();
	$logsToPull[0]="Cisco CallManager"; // Done
	$logsToPull[1]="Event Viewer-Application Log"; // Done
	$logsToPull[2]="Event Viewer-System Log"; // Done
	TUI_scheduleLogs($logsToPull);

	chdir("$caseNumber");usleep(500);
	$fpFinal = fopen("SIPTrunkOOS1.txt","w+");

	colorText("BoldCyan","Black","\r\nConsolidating data.  Please note the default timeout for each search is 20 seconds.\r\n");
	colorText("BoldCyan","Black","\r\nFor huge data pulls, please reconfigure these timeouts to prevent unprocessed information.\r\n");

	unlink("temp.txt");

	// Start processing files
	// ----------------------------------------------------------------------------------
		// Use GREP to get audit log changes
	shell_exec("grep -R \"StationRegister\|StationClose\|StationReg\|SIGTERM\|Device reset:\" * > temp.txt");
	$fp = fopen("temp.txt","r");


	echo "\r\n";
	while ( $logLine = fgets($fp) )
	{
		//echo $logLine;
		if ( strpos($logLine,"|FileHead")>0 )
		{
			$dateHeaderParse = explode(" ", $logLine);
			$dateHeader = explode("|",$dateHeaderParse[1]);
			$dateHeader = $dateHeader[1];
		}

		if ( strpos($logLine, "StationRegister")>0 )
		{

		}

		if ( strpos($logLine, "StationClose")>0 )
		{

		}

		if ( strpos($logLine, "StationReg")>0 )
		{

		}

		if ( strpos($logLine, "SIGTERM")>0 )
		{

		}

		if ( strpos($logLine, "Device reset:")>0 )
		{

		}

	// ----------------------------------------------------------------------------------
		// Use GREP to get audit log changes --Initialization Started--
	shell_exec("grep -R \"|Device reset:\|FileHead\" * > temp.txt");
	$fp = fopen("temp.txt","r");

	echo "\r\n";$dateHeader="";
	while ( $logLine = fgets($fp) )
	{
		if ( strpos($logLine,"|FileHead")>0 )
		{
			$dateHeaderParse = explode(",", $logLine);
			$dateHeader = str_replace("Date: ", "", $dateHeaderParse[1]);
		}
		else
		{
			$devResetEntry = strBetweenNI($logLine, "name", "pkid");
			fputs($fpFinal,"$dateHeader\tDevice Reset\t$devResetEntry \r\n");
		}


	}

	}
	chdir("..");
}



function SIPTrunkOOS()
{
	global $cucmPub, $cucmWebAdmin, $cucmWebPassw, $caseNumber,$cucmList,$removeDUPS;
	$removeDUPS = array();
	$logsToPull[0]="Cisco CallManager"; // Done

	$fpFinal = fopen("SIPTrunkOOS1.txt","w+");

	TUI_scheduleLogs($logsToPull);


	chdir("$caseNumber");usleep(500);

	colorText("BoldCyan","Black","\r\nConsolidating data.  Please note the default timeout for each search is 20 seconds.\r\n");
	colorText("BoldCyan","Black","\r\nFor huge data pulls, please reconfigure these timeouts to prevent unprocessed information.\r\n");

	unlink("temp.txt");

	// Start processing files
	// ----------------------------------------------------------------------------------
		// Use GREP to get audit log changes
	shell_exec("grep -R \"SIPTrunkOOS\|SIPTrunkISV\|FileHead\|RISCMAccess::SIPTrunk\" * > temp.txt");
	$fp = fopen("temp.txt","r");


	echo "\r\n";
	while ( $logLine = fgets($fp) )
	{
		//echo $logLine;
		if ( strpos($logLine,"|FileHead")>0 )
		{
			$dateHeaderParse = explode(" ", $logLine);
			$dateHeader = explode("|",$dateHeaderParse[1]);
			$dateHeader = $dateHeader[1];
		}

		if ( strpos($logLine,"::deviceName=")>0 || strpos($logLine,"::availList=")>0 || strpos($logLine,"::unAvailList=")>0 )
		{
			$entryTimeParse = explode("|", $logLine);
			$entryTime = trim($entryTimeParse[1]);

			$deviceNameParse = explode("=", $logLine);
			$deviceName = trim($deviceNameParse[1])." Error:".trim($deviceNameParse[2]);

			fputs($fpFinal,"$dateHeader ($entryTime) $deviceName\r\n");
		}

		if ( strpos($logLine,"RISCMAccess::SIPTrunkOOS")>0 || strpos($logLine,"RISCMAccess::SIPTrunkISV")>0 )
		{
			$entryTimeParse = explode("|", $logLine);
			$entryTime = $entryTimeParse[1];

			//$RISCMAccessParse = explode("|", $logLine);
			//$RISCMAccess = trim($RISCMAccessParse[3]);

			if ( strpos($logLine,"RISCMAccess::SIPTrunkOOS")>0 )
			{
				$RISCMAccess = "SIP Trunk Out of Service";
			}

			if ( strpos($logLine,"RISCMAccess::SIPTrunkISV")>0 )
			{
				$RISCMAccess = "SIP Trunk In Service";
			}

			if ( strpos($logLine,"-->")>0) {$entryDirection = "[Start]";}
			if ( strpos($logLine,"<--")>0) {$entryDirection = "[End]\r\n";}

			fputs($fpFinal,"$dateHeader ($entryTime) $RISCMAccess $entryDirection\r\n");
		}
	}
	echo "closing... $fpFinal";
	fclose($fpFinal);
	//unlink("temp.txt");

	colorText("BoldGreen","black", "\r\nSystem change results can be found in [cluster_changes.txt].\r\n\r\n");
	chdir("..");
}

function getLastChanges($debug)
{
	global $cucmPub, $cucmWebAdmin, $cucmWebPassw, $caseNumber,$cucmList,$removeDUPS;
	$removeDUPS = array();
	$logsToPull[0]="Cisco Tomcat";  // Done
	$logsToPull[1]="Cisco Audit Logs"; // Done
	$logsToPull[2]="Cisco Database Layer Monitor"; // Done
	$logsToPull[3]="Cisco Database Notification Service"; // Done

	$fpFinal = fopen("cluster_changes_$cucmPub.txt","w+");

	if (!$debug) {TUI_scheduleLogs($logsToPull);}



	chdir("$caseNumber");usleep(500);


	//colorText("BoldCyan","Black","\r\nConsolidating data.  Please note the default timeout for each search is 20 seconds.\r\n");
	//colorText("BoldCyan","Black","\r\nFor huge data pulls, please reconfigure these timeouts to prevent unprocessed information.\r\n");

	unlink("temp.txt");

	// Start processing files
	// ----------------------------------------------------------------------------------
		// Use GREP to get audit log changes
	shell_exec("grep -R \"GeneralConfigurationUpdate\|HDR\" * > temp.txt");
	$fp = fopen("temp.txt","r");

	echo "\r\n";
	while ( $logLine = fgets($fp) )
	{
		if ( strpos($logLine,"HDR|")>0 )
		{
			$dateHeaderParse = explode(" ", $logLine);
			$dateHeader = explode("|",$dateHeaderParse[1]);
			$dateHeader = $dateHeader[1];

		}
		else
		{
			$auditTime = strBetweenNI($logLine, ".log:", " |LogMessage");
			$auditDetails = strBetweenNI($logLine, "AuditDetails :", "App ID");
			$userID = strBetweenNI($logLine, "UserID :", "ClientAddress");
			$clientIPAddress = strBetweenNI($logLine, "ClientAddress :", "Severity");
			fputs($fpFinal,"$dateHeader ($auditTime) $userID $clientIPAddress  $auditDetails\r\n");
		}


	}
	// ----------------------------------------------------------------------------------
	unlink("temp.txt");

	shell_exec("grep -R \"POST\" * > temp.txt");
	$fp = fopen("temp.txt","r");

	echo "\r\n";
	while ( $logLine = fgets($fp) )
	{
		if ( strpos(strtolower($logLine),"delete")>0 | strpos(strtolower($logLine),"save")>0 | strpos(strtolower($logLine),"reset")>0 | strpos(strtolower($logLine),"restart")>0 | strpos(strtolower($logLine),"apply")>0)
		{
			$auditTime = strBetweenNI($logLine, "[", "]");
			$logLine = explode(" ", $logLine);
			//print_r($logLine);
			$userID = $logLine[4];
			$clientIPAddress = $logLine[2];
			$auditDetails = $logLine[8];
			fputs($fpFinal, "$userID ($auditTime) $clientIPAddress $auditDetails\r\n");

		}


	}

	unlink("temp.txt");


	// ----------------------------------------------------------------------------------
		// Use GREP to get audit log changes --Initialization Started--
	shell_exec("grep -R \"|Device reset:\|FileHead\" * > temp.txt");
	$fp = fopen("temp.txt","r");

	echo "\r\n";$dateHeader="";
	while ( $logLine = fgets($fp) )
	{
		if ( strpos($logLine,"|FileHead")>0 )
		{
			$dateHeaderParse = explode(",", $logLine);
			$dateHeader = str_replace("Date: ", "", $dateHeaderParse[1]);
		}
		else
		{
			$devResetEntry = strBetweenNI($logLine, "name", "pkid");
			fputs($fpFinal,"$dateHeader\tDevice Reset\t$devResetEntry \r\n");
		}


	}
	unlink("temp.txt");

	// ----------------------------------------------------------------------------------

	shell_exec("grep -R \"<action>\" * > temp.txt");
	$fp = fopen("temp.txt","r");

	fputs($fpFinal,  "\r\n");
	while ( $logLine = fgets($fp) )
	{
		//fputs($fpFinal,  "\r\n====================================================================================\r\n");
		$xml = strBetweenI($logLine, "<msg>", "</msg>");
		try {
			$xmlLine = new SimpleXMLElement($xml);
		} catch (Exception $e) {

			continue;
			//$xmlLine = new SimpleXMLElement("<wrapper>$xml</wrapper>");
			//print_r($xmlLine);
		}

			parseDBMonXML($fpFinal, $xmlLine);

	}

	unlink("temp.txt");

	fclose($fpFinal);
	colorText("BoldGreen","black", "\r\nSystem change results can be found in [cluster_changes.txt].\r\n\r\n");
	chdir("..");
}




















function parseDBMonXML($fpFinal, $xmlLine, $removeDUPS)
{
		global $removeDUPS;
		$updateType = "";


		switch ($xmlLine->action)
		{
			case 'U':
				$updateType = "Update";

				$dupHASH = md5($xmlLine->old->paramname.$xmlLine->old->cdrtime.$xmlLine->old->versionstamp);
				//fputs($fpFinal, $dupHASH);
				//fputs($fpFinal, "[".count($removeDUPS)."]");

				if ( !array_search($dupHASH, $removeDUPS) )
				{
					array_push($removeDUPS, $dupHASH);

					fputs($fpFinal, "\r\nTable ".$xmlLine->table." entry was UPDATED\r\n ");
					//fputs($fpFinal, "Old-----------------\r\n");

					foreach ($xmlLine->old->children() as $key1 => $newInfo1)
					{
						if ($key1=="cdrtime")
						{
							$newInfo1 = gmdate('M d Y H:i:s Z',$newInfo1);
						}
						$finalOutput = "\t$key1 [$newInfo1]";

						foreach ($xmlLine->new->children() as $key2 => $newInfo2)
						{

							if ( ($key1 == $key2) and ($newInfo1 != $newInfo2) )
							{
								$finalOutput .=  "\t ---> [$key2] : [$newInfo2]";
							}
						}
						fputs($fpFinal, $finalOutput."\r\n");

					}
				}
				//fputs($fpFinal, "New-----------------\r\n");

			break;

			case 'D':
				$updateType = "Delete";

				$dupHASH = md5($xmlLine->old->paramname.$xmlLine->old->cdrtime.$xmlLine->old->versionstamp);
				//fputs($fpFinal, $dupHASH);
				//fputs($fpFinal, "[".count($removeDUPS)."]");

				if ( !array_search($dupHASH, $removeDUPS) )
				{
					array_push($removeDUPS, $dupHASH);

					fputs($fpFinal, "\r\nTable ".$xmlLine->table." entry was DELETED\r\n ");
					//fputs($fpFinal, "Old-----------------\r\n");

					foreach ($xmlLine->old->children() as $key => $newInfo)
					{
						if ($key=="cdrtime")
						{
							$newInfo1 = date('M d Y H:i:s Z',$newInfo1);
						}

						fputs($fpFinal, "\t$key [$newInfo]\r\n");
					}
				}

				break;


			case 'I':
				$updateType = "Insert";

				$dupHASH = md5($xmlLine->old->paramname.$xmlLine->old->cdrtime.$xmlLine->old->versionstamp);
				//fputs($fpFinal, $dupHASH);

				if ( !array_search($dupHASH, $removeDUPS) )
				{
					array_push($removeDUPS, $dupHASH);

					fputs($fpFinal, "\r\nTable ".$xmlLine->table." was INSERTED\r\n ");

					//fputs($fpFinal, "New-----------------\r\n");
					fputs($fpFinal, "\r\n".$xmlLine->table."\t\t".$updateType."\r\n ");
					foreach ($xmlLine->new->children() as $key => $newInfo)
					{
						if ($key=="cdrtime")
						{
							$newInfo1 = date('M d Y H:i:s Z',$newInfo1);
						}

						fputs($fpFinal, "\t$key [$newInfo]\r\n");
					}
				}
				break;

		}
		unlink("temp.txt");

}

exit;

































function pullCUCMLogsMenu()
{
	global $caseNumber,$cucmList;


	while (1)
	{
		//$cucmList = TUI_getCredentials();
		$logsToPull = TUI_selectLogs($cucmList);
		if (TUI_scheduleLogs($logsToPull)) {break;}
	}

	//chdir("..");
	//echo "Current dir:".getcwd();

	return $caseNumber;
}
























function TUI_scheduleLogs($logsToPull)
{
	global $cucmPub, $cucmWebAdmin, $cucmWebPassw,$caseNumber;
	$ch = curl_init();

	while(1)
	{
		colorClearScreen();

		colorText("BoldWhite","Black","\r\n*** All time specified is in Eastern Time Zone (-5 GMT) ***\r\n");
		colorText("White","Black",    "-----------------------------------------------------------\r\n");
		colorText("BoldCyan","Black","\r\nDo you want to use a relative or absolute date range [R]elative/[a]bsolute:\r\n");

		colorText("boldWhite","Black");
		$retValue = readLine("");
		if (strlen($retValue)==0) {$retValue="R";colorText("boldWhite","Black","$retValue\r\n");}

		switch ( strtolower($retValue) )
		{
			case "a":

				colorText("BoldCyan","Black", "Input START absolute time EST in [mm/yy/dd hh:mm AM/PM] format:\r\n");
				colorText("boldWhite","black");$startTime = readline("");

				colorText("BoldCyan","Black", "Input END absolute time EST in [mm/yy/dd hh:mm AM/PM] format:\r\n");
				colorText("boldWhite","black");$endTime = readline("");

				$ABSTime[0] = $startTime;
				$ABSTime[1] = $endTime;

				colorClearScreen();

				colorText("boldWhite","black","Attempting to load files...\r\n\r\n");
				getClusterLogsABS($ch, $cucmPub, $cucmWebAdmin, $cucmWebPassw, $logsToPull, $ABSTime);
				return true;

			case "q":
				return;

			 default:
				colorText("BoldCyan","Black","Input relative time in minutes [60]:\r\n");
				colorText("boldWhite","Black");$relMinutes = readLine("");
				if (strlen($relMinutes)==0) {$relMinutes=60;colorText("White","Black","$relMinutes\r\n");}
				if (!filter_var($relMinutes, FILTER_VALIDATE_INT)) {colorText("boldRed","Black","\r\nPlease provide a whole integer!\r\n");continue;}

				colorClearScreen();
				colorText("boldWhite","black","Attempting to load files...\r\n\r\n");
				getClusterLogsREL($ch, $cucmPub, $cucmWebAdmin, $cucmWebPassw, $logsToPull, $relMinutes);
				return true;
		}
	}
}

function TUI_selectLogs()
{
		global $cucmPub, $cucmWebAdmin, $cucmWebPassw,$caseNumber, $cucmList;

		$ch = curl_init();

		$filtered = true;
		while (1)
		{
			colorClearScreen();

			///  List logs
			colorText("boldCyan","Black","\r\nPlease select logs you would like to pull multiple logs, delimit using spaces.  Example '1 2 3 4 5' \r\n");
			if ($filtered==true) {colorText("boldCyan","Black","\r\n* Output is FILTERED for most commonly used *\r\n\r\n");}
			//colorText("boldCyan","Black","Index        Log Name\r\n");
			//colorClearScreen();

			//$linePos=1;
			$colorPos = true;
			for ($i=0; $i < count($cucmList); $i++)
			{

					/*$linePos++;
					moveCursor(1,$linePos);
					colorText("boldcyan","Black","$i:     ".$cucmList[$i].""); $i++;
					moveCursor(70,$linePos);
					colorText("boldcyan","Black","$i:     ".$cucmList[$i]); $i++;

					$linePos++;
					moveCursor(1,$linePos);
					colorText("cyan","Black","$i:     ".$cucmList[$i].""); $i++;
					moveCursor(70,$linePos);
					colorText("cyan","Black","$i:     ".$cucmList[$i]);
					*/
					if ($filtered==true)
					{
						if ($colorPos)
						{
							$colorPos=false;
							colorTextFiltered("boldCyan","Black","$i:     ".$cucmList[$i]."\r\n");
						}
						else
						{
							$colorPos=true;
							colorTextFiltered("cyan","Black","$i:     ".$cucmList[$i]."\r\n");

						}
					}
					else
					{
						if ($colorPos)
						{$colorPos=!$colorPos; colorText("boldcyan","Black","$i:     ".$cucmList[$i]."\r\n");}
						else
						{$colorPos=!$colorPos; colorText("cyan","Black","$i:     ".$cucmList[$i]."\r\n");}
					}

			}

			colorText("boldCyan","Black","Input log indexes or 'X' to TOGGLE list ALL traces without a filter: \r\n");

			colorText("boldWhite","Black");
			$logIndexes = readLine("");

			if (strpos(" ".$logIndexes,"X")>0) {$filtered=!$filtered;continue 1;}
			$logIndexes = explode(" ",$logIndexes);

			///  Check INPUT
			for ($i=0; $i<count($logIndexes); $i++)
			{
				if (strlen($cucmList[$logIndexes[$i]])<1)
				{colorText("boldRed","black","\r\nInput invalid on entry #$i!! Please try again...");continue 2;}

			}

			///  List logs
			colorText("BoldCyan","Black","\r\nYou selected the following logs\r\n\r\n");

			colorText("boldWhite","Black");

			for ($i=0; $i<count($logIndexes); $i++)
			{
				$logsToPull[$i] = $cucmList[$logIndexes[$i]];
				echo $logsToPull[$i]."\r\n";
			}

			colorText("BoldCyan","Black","\r\nIs this correct [Y]es/[n]o:\r\n");

			colorText("boldWhite","Black");
			$retValue = readLine("");

			if (strlen($retValue)==0) {$retValue="Y";colorText("boldWhite","Black","$retValue\r\n");}

			if (strtolower($retValue)=="n")
				{continue;}
				else {return $logsToPull;}
		}
}


function TUI_getCredentials()
{
	global $cucmPub, $cucmWebAdmin, $cucmWebPassw, $caseNumber,$cucmList;

	$ch = curl_init();

	while (1)
	{
		///  INTRO
		colorClearScreen();
		colorText("boldWhite","Black","\r\nPlease provide case and credentials to CUCM/CUC/IMP& or UCCX cluster\r\n");
		colorText("white", "Black",        "-------------------------------------------------------------------\r\n\r\n");

		while (1)
		{

			colorText("boldCyan","black","\r\nPlease enter case# or folder# to store files [Defaut: 12345]:\r\n");
			colorText("white","black");
			$caseNumber = readLine();

			if (strlen($caseNumber)==0) {$caseNumber=12345;colorText("boldWhite","Black","$caseNumber\r\n");}

			if (!filter_var($caseNumber, FILTER_VALIDATE_INT))
			{
				colorText("BoldRed","Black","\r\nDoes not match a valid case number (INTEGER)!\r\n");continue;
			}

			///  CUCM IP
			colorText("boldCyan","Black","\r\nPlease enter CUCM Publishe node IP address/port (X.X.X.X:port) or number selection: \r\n");


				// Offer MySQL option
			if ($db = mysql_connect("localhost","root",""))
			{
				//colorText("BoldRed","Black","\r\n\r\n(found local MySQL database!)\r\n");

				mysql_select_db("CaseSentry");

				$qry = mysql_query("select publisher, port, entity from def_ccm_credentials where type='publisher'");

				$i=1; $publisher; $publisherport;
				while ($row = mysql_fetch_assoc($qry))
				{
					$publisher[$i] = $row['publisher'];
					$publisherport[$i] = $row['port'];
					colorText("boldCyan","black","\r\n[$i]\t{$row['publisher']}\t{$row['port']}\t{$row['entity']}");$i++;
				}

				//colorText("boldWhite","black","\r\n");
				colorText("boldWhite","black","\r\n");
				$serverID = readLine();

				if (filter_var($serverID, FILTER_VALIDATE_INT) && $serverID > 0 && $serverID <= $i )
					{$cucmPub="{$publisher[$serverID]}:{$publisherport[$serverID]}"; colorText("boldWhite","Black","$cucmPub\r\n");}
				else
					{
						if (!filter_var($serverID, FILTER_VALIDATE_IP))
						{
							colorText("BoldRed","Black","\r\nDoes not match a valid IP address format or valid selection!\r\n");continue;
						}
						$cucmPub=$serverID;
					}

			}
			else
			{
				colorText("boldWhite","Black");
				$cucmPub = readLine();
				if (strlen($cucmPub)==0) {$cucmPub="192.168.1.220";colorText("boldWhite","Black","192.168.1.220\r\n");}

				if (!filter_var($cucmPub, FILTER_VALIDATE_IP))
				{
					colorText("BoldRed","Black","\r\nDoes not match a valid IP address format!\r\n");continue;
				}
			}
			///  WebAdmin

			colorText("boldCyan","Black","\r\nPlease enter WebAdmin login: \r\n");

			colorText("boldWhite","Black");
			$cucmWebAdmin = readLine("");
			if (strlen($cucmWebAdmin)==0) {$cucmWebAdmin="CCMAdministrator";colorText("boldWhite","Black","CCMAdministrator\r\n");}

			///  WebAdmin PWD

			colorText("boldCyan","Black","\r\nPlease enter WebAdmin password: \r\n");

			colorText("Black","Black");
			$cucmWebPassw = readLine("");
			if (strlen($cucmWebPassw)==0) {$cucmWebPassw="N!5d5upp";colorText("boldWhite","Black","<password hidden>\r\n");}

			///  Check CREDENTIALS
			colorText("white","Black","\r\nChecking login...\r\n");

			$cucmList = ListNodeServiceLogs($ch, $cucmPub, $cucmWebAdmin, $cucmWebPassw);

			if ( count($cucmList)==0)
			{colorText("boldRed","black","\r\nUnable to authenticate to $cucmPub using credentials!\r\n");continue;}

			return $cucmList;
		}
	}
}

function downloadLogsABS($ch, $CCMIP, $CCMLogin, $CCMPassword, $logsToPull, $ABSTime)
{
	mkdir("$CCMIP");
	chdir("$CCMIP");


		$logFileList = ListLogFilesABS($ch, $CCMIP, $CCMLogin, $CCMPassword, $logsToPull, $ABSTime);

		colorText("Cyan","black", "\r\nService log: ".$logsToPull."\r\n");
		for ($counter=0; $counter < count($logFileList); $counter++)
		{

			$logFile = explode("|", $logFileList[$counter]);
			$logFile = $logFile[0];
			$logFileTimeStamp = $logFile[1];

			$fileContents = downloadSingleFile($ch, $CCMIP, $CCMLogin, $CCMPassword, $logFile);

			$stripSlash = explode("/", $logFile);
			$saveFileName = $stripSlash[count($stripSlash)-1];


			if (function_exists("gzdecode"))
			{
				if ( strpos($saveFileName, ".gz")>0 || strpos($saveFileName, ".gzo")>0)
				{
					$fileContents = gzdecode($fileContents);		// decompress!
					$saveFileName = str_replace(".gzo","",$saveFileName);
					$saveFileName = str_replace(".gz","",$saveFileName);
				}
			}

			colorText("boldWhite","black", "\tFilename: $saveFileName.\r\n");

			file_put_contents("$saveFileName", $fileContents);
			$new_date = strtotime($logFileTimeStamp); // set the required date timestamp here
			touch("$saveFileName",$new_date);

		}


	chdir("..");
}

function getClusterLogsABS($ch, $CCMIP, $CCMLogin, $CCMPassword, $logsToPull, $ABSTime)
{

	global $caseNumber;

	mkdir($caseNumber);
	chdir($caseNumber);
	$ccmList = getProcessNodeList($ch, $CCMIP, $CCMLogin, $CCMPassword);

	for ($ccmCounter=0; $ccmCounter < count($ccmList); $ccmCounter++)
	{
		//mkdir("$caseNumber");
		//chdir("$caseNumber");
		colorText("boldCyan","black","\r\n*** Downloading from server {$ccmList[$ccmCounter]} ***\r\n");

		for ($i=0; $i<count($logsToPull); $i++)
		{
				downloadLogsABS($ch, $ccmList[$ccmCounter], $CCMLogin, $CCMPassword, $logsToPull[$i], $ABSTime);
		}


	}
	chdir("..");
}

function getClusterLogsREL($ch, $CCMIP, $CCMLogin, $CCMPassword, $logsToPull, $RELTime)
{
	global $caseNumber;

	mkdir($caseNumber);
	chdir($caseNumber);

	$ccmList = getProcessNodeList($ch, $CCMIP, $CCMLogin, $CCMPassword);

	for ($ccmCounter=0; $ccmCounter < count($ccmList); $ccmCounter++)
	{
		//mkdir("$caseNumber");
		//chdir("$caseNumber");
		colorText("boldCyan","black","\r\n*** Downloading from server {$ccmList[$ccmCounter]} ***\r\n");

		for ($i=0; $i<count($logsToPull); $i++)
		{
				downloadLogs($ch, $ccmList[$ccmCounter], $CCMLogin, $CCMPassword, $logsToPull[$i], $RELTime);
		}


	}
	chdir("..");
}


function downloadLogs($ch, $CCMIP, $CCMLogin, $CCMPassword, $ServiceLogName, $hours=1)
{
	mkdir("$CCMIP");
	chdir("$CCMIP");
	$logFileList = ListLogFiles($ch, $CCMIP, $CCMLogin, $CCMPassword, $ServiceLogName, $hours);

	colorText("Cyan","black", "\r\nService log: ".$ServiceLogName."\r\n");
	for ($counter=0; $counter < count($logFileList); $counter++)
	{

		$logFile = explode("|", $logFileList[$counter]);
		$logFile = $logFile[0];
		$logFileTimeStamp = $logFile[1];

		$fileContents = downloadSingleFile($ch, $CCMIP, $CCMLogin, $CCMPassword, $logFile);

		$stripSlash = explode("/", $logFile);
		$saveFileName = $stripSlash[count($stripSlash)-1];

		//	if (function_exists("gzdecode"))
		//	{
		//		if ( strpos($saveFileName, ".gz")>0 || strpos($saveFileName, ".gzo")>0)
		//		{
		//			$fileContents = gzdecode($fileContents);		// decompress!
		//			$saveFileName = str_replace(".gzo","",$saveFileName);
		//			$saveFileName = str_replace(".gz","",$saveFileName);
		//		}
		//	}

		colorText("boldWhite","black", "\tFilename: $saveFileName.\r\n");

		file_put_contents("$saveFileName", $fileContents);
		$new_date = strtotime($logFileTimeStamp); // set the required date timestamp here
		touch("$saveFileName",$new_date);

	}
	chdir("..");
}



function getProcessNodeList($ch, $CCMIP, $CCMLogin, $CCMPassword, $version=0)
{
            //curl_setopt($ch, CURLOPT_URL, "https://$CCMIP/ast/ASTIsapi.dll?GetClusterInfoList");
            curl_setopt($ch, CURLOPT_URL, "https://$CCMIP/ast/ASTIsapi.dll?GetPreCannedInfo&Items=getCpuAndMemoryRequest");


			$AXLHeader = array("Content-Type: text/xml; charset=utf-8",
					"Authorization: Basic ".base64_encode("$CCMLogin:$CCMPassword"),
					"Content-Length: ".strlen($SVCRequest),
													$SVCHeaderSuffix);

			curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
			curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, false);
			curl_setopt($ch, CURLOPT_HTTPHEADER, $AXLHeader);
			curl_setopt($ch, CURLOPT_POST, 1);
			curl_setopt($ch, CURLOPT_POSTFIELDS, $SVCRequest);
			curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
			curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 15);
			curl_setopt($ch, CURLOPT_TIMEOUT, 15);

			$retValue = curl_exec($ch);

			//echo $retValue;

			$retValue = strBetweenI($retValue, "<getCpuAndMemoryReply", "</getCpuAndMemoryReply>");
			//echo $retValue;exit;

			$xml = new SimpleXMLElement($retValue);

			$retValue = ""; $counter = 0;

			foreach ($xml->children() as $newChild)
			{
					if ($newChild['ReturnCode']=="0")
					{
						$retValue[$counter] = $newChild['Name'];
						$counter++;
					}
					else
					{
						colorText("boldRed","black", "\r\nSkipping node {$newChild['Name']} for abnormal return code.\r\n");
					}
			}

			return $retValue;
}

function getProcessNodeList_old($ch, $CCMIP, $CCMLogin, $CCMPassword, $version=0)
{
		$AXLBody_[0] = "<SOAP-ENV:Envelope xmlns:SOAP-ENV='http://schemas.xmlsoap.org/soap/envelope/' xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance' xmlns:xsd='http://www.w3.org/2001/XMLSchema'> <SOAP-ENV:Body><axl:executeSQLQuery xmlns:axl='http://www.cisco.com/AXL/1.0'  xsi:schemaLocation='http://www.cisco.com/AXL/1.0 http://gkar.cisco.com/schema/axlsoap.xsd'  sequence='1234'><sql>{replaceMe}</sql></axl:executeSQLQuery></SOAP-ENV:Body></SOAP-ENV:Envelope>";
		$AXLBody_[1] = "<SOAP-ENV:Envelope xmlns:SOAP-ENV='http://schemas.xmlsoap.org/soap/envelope/' xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance' xmlns:xsd='http://www.w3.org/2001/XMLSchema'> <SOAP-ENV:Body><axl:executeSQLQuery xmlns:axl='http://www.cisco.com/AXL/API/8.0'  xsi:schemaLocation='http://www.cisco.com/AXL/API/8.0 http://gkar.cisco.com/schema/axlsoap.xsd'  sequence='1234'><sql>{replaceMe}</sql></axl:executeSQLQuery></SOAP-ENV:Body></SOAP-ENV:Envelope>";
		$AXLBody_[2] = "<SOAP-ENV:Envelope xmlns:SOAP-ENV='http://schemas.xmlsoap.org/soap/envelope/' xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance' xmlns:xsd='http://www.w3.org/2001/XMLSchema'> <SOAP-ENV:Body><axl:executeSQLQuery xmlns:axl='http://www.cisco.com/AXL/API/9.0'  xsi:schemaLocation='http://www.cisco.com/AXL/API/9.0 http://gkar.cisco.com/schema/axlsoap.xsd'  sequence='1234'><sql>{replaceMe}</sql></axl:executeSQLQuery></SOAP-ENV:Body></SOAP-ENV:Envelope>";
		$AXLBody_[3] = "<SOAP-ENV:Envelope xmlns:SOAP-ENV='http://schemas.xmlsoap.org/soap/envelope/' xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance' xmlns:xsd='http://www.w3.org/2001/XMLSchema'> <SOAP-ENV:Body><axl:executeSQLQuery xmlns:axl='http://www.cisco.com/AXL/API/10.0'  xsi:schemaLocation='http://www.cisco.com/AXL/API/10.0 http://gkar.cisco.com/schema/axlsoap.xsd'  sequence='1234'><sql>{replaceMe}</sql></axl:executeSQLQuery></SOAP-ENV:Body></SOAP-ENV:Envelope>";
		$AXLBody_[4] = "<SOAP-ENV:Envelope xmlns:SOAP-ENV='http://schemas.xmlsoap.org/soap/envelope/' xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance' xmlns:xsd='http://www.w3.org/2001/XMLSchema'> <SOAP-ENV:Body><axl:executeSQLQuery xmlns:axl='http://www.cisco.com/AXL/API/10.5'  xsi:schemaLocation='http://www.cisco.com/AXL/API/10.5 http://gkar.cisco.com/schema/axlsoap.xsd'  sequence='1234'><sql>{replaceMe}</sql></axl:executeSQLQuery></SOAP-ENV:Body></SOAP-ENV:Envelope>";

		$AXLVersion_[0] = "SOAPAction: \"CUCM:DB ver=6.0\"";
		$AXLVersion_[1] = "SOAPAction: \"CUCM:DB ver=8.0\"";
		$AXLVersion_[2] = "SOAPAction: \"CUCM:DB ver=9.0\"";
		$AXLVersion_[3] = "SOAPAction: \"CUCM:DB ver=10.0\"";
		$AXLVersion_[4] = "SOAPAction: \"CUCM:DB ver=10.5\"";

		$AXLVersion__[0] = "6.0";
		$AXLVersion__[1] = "8.0";
		$AXLVersion__[2] = "9.0";
		$AXLVersion__[3] = "10.0";
		$AXLVersion__[3] = "10.5";

		$AXLVersion_I = $AXLVersion__[$version];

		$AXLBody = $AXLBody_[$version];


		if ($version > 4) { echo "\r\nTried all versions and failed!\r\n";exit;}

        //$AXLBody = "<SOAP-ENV:Envelope xmlns:SOAP-ENV='http://schemas.xmlsoap.org/soap/envelope/' xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance' xmlns:xsd='http://www.w3.org/2001/XMLSchema'> <SOAP-ENV:Body><axl:executeSQLQuery xmlns:axl='http://www.cisco.com/AXL/1.0'  xsi:schemaLocation='http://www.cisco.com/AXL/1.0 http://gkar.cisco.com/schema/axlsoap.xsd'  sequence='1234'><sql>{replaceMe}</sql></axl:executeSQLQuery></SOAP-ENV:Body></SOAP-ENV:Envelope>";

             $SVCRequest = str_replace("{replaceMe}", "select * from processnode", $AXLBody);


            //$SVCHeaderSuffix = "SOAPAction: \"CUCM:DB ver=6.0\"";
			$SVCHeaderSuffix = $AXLVersion_[$version];

            curl_setopt($ch, CURLOPT_URL, "https://$CCMIP/axl/");


                        $AXLHeader = array("Content-Type: text/xml; charset=utf-8",
                                "Authorization: Basic ".base64_encode("$CCMLogin:$CCMPassword"),
                                "Content-Length: ".strlen($SVCRequest),
                                                                $SVCHeaderSuffix);

                                                curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
                                                curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, false);
                                                curl_setopt($ch, CURLOPT_HTTPHEADER, $AXLHeader);
                                                curl_setopt($ch, CURLOPT_POST, 1);
                                                curl_setopt($ch, CURLOPT_POSTFIELDS, $SVCRequest);
                                                curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
                        curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 15);
                        curl_setopt($ch, CURLOPT_TIMEOUT, 15);

                        $retValue = curl_exec($ch);

                        $retValue = strBetweenI($retValue, "<return", "</return>");

						if ( !$retValue )
						{
							echo "\r\nDetected newer API envelope necessary...\r\n";
							$retValue = getProcessNodeList($ch, $CCMIP, $CCMLogin, $CCMPassword, ++$version);
							return $retValue;
						}

                        $xml = new SimpleXMLElement($retValue);

                        //echo $xml->row[1]->name;exit;
                        $retValue = ""; $counter = 0;

                        //echo $retValue;

                        foreach ($xml->children() as $newChild)
                        {
                                //echo $newChild->name."\r\n";
                                $retValue[$counter] = $newChild->name;
                                $counter++;
                        }

                        return $retValue;
}





function ListNodeServiceLogs($ch, $CCMIP, $CCMLogin, $CCMPassword)
{
                        $SVCRequest = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\"
xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\"
xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">
 <soapenv:Body>
  <ns1:ListNodeServiceLogs
soapenv:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\"
xmlns:ns1=\"http://schemas.cisco.com/ast/soap/\">
   <ListRequest href=\"#id0\"/>
  </ns1:ListNodeServiceLogs>
  <multiRef id=\"id0\" soapenc:root=\"0\"
soapenv:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\"
xsi:type=\"ns2:ListRequest\" xmlns:soapenc=\"http://schemas.xmlsoap.org/soap/encoding/\"
xmlns:ns2=\"http://cisco.com/ccm/serviceability/soap/LogCollection/\">{replaceMe}</multiRef>
 </soapenv:Body>
</soapenv:Envelope>";

                        $SVCRequest = str_replace("{replaceMe}", $CCMIP, $SVCRequest);
            $SVCHeaderSuffix = "SOAPAction: \"http://schemas.cisco.com/ast/soap/action/#LogCollectionPort#ListNodeServiceLogs\"";
            curl_setopt($ch, CURLOPT_URL, "https://$CCMIP/logcollectionservice/services/LogCollectionPort");


                        $AXLHeader = array("Content-Type: text/xml; charset=utf-8",
                                "Authorization: Basic ".base64_encode("$CCMLogin:$CCMPassword"),
                                "Content-Length: ".strlen($SVCRequest),
                                                                $SVCHeaderSuffix);

                curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
                curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, false);
                curl_setopt($ch, CURLOPT_HTTPHEADER, $AXLHeader);
                curl_setopt($ch, CURLOPT_POST, 1);
                curl_setopt($ch, CURLOPT_POSTFIELDS, $SVCRequest);
                curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
                        curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 15);
                        curl_setopt($ch, CURLOPT_TIMEOUT, 15);

                        $retValue = curl_exec($ch);

						//print_r($AXLHeader);
						//echo $retValue;

                        $retValue = strBetweenI($retValue, "<ServiceLog", "</ServiceLog>");

                        try {
							$xml = new SimpleXMLElement($retValue);
						} catch (Exception $e) {
							return;
						}

                        $retValue = ""; $counter = 0;

                        foreach ($xml->children() as $newChild)
                        {
								//echo $newChild;
                                $retValue[$counter] = $newChild;
                                $counter++;
                        }
                        return $retValue;
}

function ListLogFilesABS($ch, $CCMIP, $CCMLogin, $CCMPassword, $ServiceLogName, $ABSTime)
{

 $SVCRequest = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>
 <soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\"
 xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\"
 xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">
  <soapenv:Body>
   <ns1:SelectLogFiles soapenv:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\"
 xmlns:ns1=\"http://schemas.cisco.com/ast/soap/\">
    <FileSelectionCriteria href=\"#id0\"/>
   </ns1:SelectLogFiles>
   <multiRef id=\"id0\" soapenc:root=\"0\"
soapenv:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\"
xsi:type=\"ns2:SchemaFileSelectionCriteria\"
xmlns:soapenc=\"http://schemas.xmlsoap.org/soap/encoding/\"
xmlns:ns2=\"http://cisco.com/ccm/serviceability/soap/LogCollection/\">
    <ServiceLogs xsi:type=\"soapenc:Array\" soapenc:arrayType=\"xsd:string[45]\">
     <item>{serviceLog}</item>
    </ServiceLogs>
<SystemLogs xsi:type=\"xsd:string\" xsi:nil=\"true\"/>

    <JobType href=\"#id2\"/>
    <SearchStr xsi:type=\"xsd:string\"/>
    <Frequency href=\"#id1\"/>
    <ToDate xsi:type=\"xsd:string\">{toDate}</ToDate>
    <FromDate xsi:type=\"xsd:string\">{fromDate}</FromDate>
    <TimeZone xsi:type=\"xsd:string\">Client:(GMT-5:0)Eastern Standard Time</TimeZone>
    <RelText xsi:type=\"xsd:string\" xsi:nil=\"true\" />
    <RelTime xsi:type=\"xsd:byte\"  xsi:nil=\"true\" />
    <Port xsi:type=\"xsd:byte\">0</Port>
    <IPAddress xsi:type=\"xsd:string\"></IPAddress>
    <UserName xsi:type=\"xsd:string\" xsi:nil=\"true\"/>
    <Password xsi:type=\"xsd:string\" xsi:nil=\"true\"/>
    <ZipInfo xsi:type=\"xsd:boolean\">False</ZipInfo>
   </multiRef>
     <multiRef id=\"id1\" soapenc:root=\"0\"
soapenv:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\" xsi:type=\"ns4:Frequency\"
xmlns:ns4=\"http://cisco.com/ccm/serviceability/soap/LogCollection/\"
xmlns:soapenc=\"http://schemas.xmlsoap.org/soap/encoding/\">OnDemand</multiRef>
     <multiRef id=\"id2\" soapenc:root=\"0\"
soapenv:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\" xsi:type=\"ns3:JobType\"
xmlns:ns3=\"http://cisco.com/ccm/serviceability/soap/LogCollection/\"
xmlns:soapenc=\"http://schemas.xmlsoap.org/soap/encoding/\">DownloadtoClient</multiRef>
     <multiRef id=\"id3\" soapenc:root=\"0\"
soapenv:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\" xsi:type=\"ns4:RelText\"
xmlns:ns4=\"http://cisco.com/ccm/serviceability/soap/LogCollection/\"
xmlns:soapenc=\"http://schemas.xmlsoap.org/soap/encoding/\">Minutes</multiRef>
  </soapenv:Body>
 </soapenv:Envelope>";

						//echo "List ServiceLog files: $ServiceLogName ".$ABSTime[0]. " ".$ABSTime[1];
                        $SVCRequest = str_replace("{serviceLog}", $ServiceLogName, $SVCRequest);
						$SVCRequest = str_replace("{fromDate}", $ABSTime[0], $SVCRequest);
                        $SVCRequest = str_replace("{toDate}", $ABSTime[1], $SVCRequest);
						//echo "\r\n\r\n".$SVCRequest;
                       // $SVCRequest = str_replace("{replaceMe2}", $CCMIP, $SVCRequest);

            $SVCHeaderSuffix = "SOAPAction: \"http://schemas.cisco.com/ast/soap/action/#LogCollectionPort#SelectLogFiles";
            curl_setopt($ch, CURLOPT_URL, "https://$CCMIP/logcollectionservice/services/LogCollectionPort");


                        $AXLHeader = array("Content-Type: text/xml; charset=utf-8",
                                "Authorization: Basic ".base64_encode("$CCMLogin:$CCMPassword"),
                                "Content-Length: ".strlen($SVCRequest),
                                                                $SVCHeaderSuffix);

                curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
                curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, false);
                curl_setopt($ch, CURLOPT_HTTPHEADER, $AXLHeader);
                curl_setopt($ch, CURLOPT_POST, 1);
                curl_setopt($ch, CURLOPT_POSTFIELDS, $SVCRequest);
                curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
                        curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 15);
                        curl_setopt($ch, CURLOPT_TIMEOUT, 15);

                        $retValue = curl_exec($ch)      ;
						//echo $retValue;exit;

                        $retValue = strBetweenI($retValue,"<SetOfFiles","</SetOfFiles>");


                        if (strlen($retValue)<100) {return;}

                        $xml = new SimpleXMLElement($retValue);

                        $counter = 0; $retValue = "";

                        for ($i=0; $i<count($xml); $i++)
                        {
                                /*echo "<tr>";
                                echo "<td>".$xml->item[$i]->name."</td>";
                                echo "<td>". $xml->item[$i]->absolutepath."</td>";
                                echo "<td>". $xml->item[$i]->filesize."</td>";
                                echo "<td>". $xml->item[$i]->modifiedDate."</td>";
                                echo "<td>". $LogType."</td>";
                                echo "</tr>"; */
                                $retValue[$i] = $xml->item[$i]->absolutepath."|".$xml->item[$i]->modifiedDate;
                        }

                        return $retValue;
}

function ListLogFiles($ch, $CCMIP, $CCMLogin, $CCMPassword, $ServiceLogName, $numMinutes)
{

 $SVCRequest = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>
 <soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\"
 xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\"
 xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">
  <soapenv:Body>
   <ns1:SelectLogFiles soapenv:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\"
 xmlns:ns1=\"http://schemas.cisco.com/ast/soap/\">
    <FileSelectionCriteria href=\"#id0\"/>
   </ns1:SelectLogFiles>
   <multiRef id=\"id0\" soapenc:root=\"0\"
soapenv:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\"
xsi:type=\"ns2:SchemaFileSelectionCriteria\"
xmlns:soapenc=\"http://schemas.xmlsoap.org/soap/encoding/\"
xmlns:ns2=\"http://cisco.com/ccm/serviceability/soap/LogCollection/\">
    <ServiceLogs xsi:type=\"soapenc:Array\" soapenc:arrayType=\"xsd:string[45]\">
     <item>{replaceMe}</item>
    </ServiceLogs>
<SystemLogs xsi:type=\"xsd:string\" xsi:nil=\"true\"/>

    <JobType href=\"#id2\"/>
    <SearchStr xsi:type=\"xsd:string\"/>
    <Frequency href=\"#id1\"/>
    <ToDate xsi:type=\"xsd:string\" xsi:nil=\"true\"/>
    <FromDate xsi:type=\"xsd:string\" xsi:nil=\"true\"/>
    <TimeZone xsi:type=\"xsd:string\">Client:(GMT-5:0)Eastern Standard Time</TimeZone>
    <RelText href=\"#id3\"/>
    <RelTime xsi:type=\"xsd:byte\">{replaceMe1}</RelTime>
    <Port xsi:type=\"xsd:byte\">0</Port>
    <IPAddress xsi:type=\"xsd:string\">{replaceMe2}</IPAddress>
    <UserName xsi:type=\"xsd:string\" xsi:nil=\"true\"/>
    <Password xsi:type=\"xsd:string\" xsi:nil=\"true\"/>
    <ZipInfo xsi:type=\"xsd:boolean\">false</ZipInfo>
   </multiRef>
     <multiRef id=\"id1\" soapenc:root=\"0\"
soapenv:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\" xsi:type=\"ns4:Frequency\"
xmlns:ns4=\"http://cisco.com/ccm/serviceability/soap/LogCollection/\"
xmlns:soapenc=\"http://schemas.xmlsoap.org/soap/encoding/\">OnDemand</multiRef>
     <multiRef id=\"id2\" soapenc:root=\"0\"
soapenv:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\" xsi:type=\"ns3:JobType\"
xmlns:ns3=\"http://cisco.com/ccm/serviceability/soap/LogCollection/\"
xmlns:soapenc=\"http://schemas.xmlsoap.org/soap/encoding/\">DownloadtoClient</multiRef>
     <multiRef id=\"id3\" soapenc:root=\"0\"
soapenv:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\" xsi:type=\"ns4:RelText\"
xmlns:ns4=\"http://cisco.com/ccm/serviceability/soap/LogCollection/\"
xmlns:soapenc=\"http://schemas.xmlsoap.org/soap/encoding/\">Minutes</multiRef>
  </soapenv:Body>
 </soapenv:Envelope>";


                        $SVCRequest = str_replace("{replaceMe}", $ServiceLogName, $SVCRequest);
                        $SVCRequest = str_replace("{replaceMe1}", $numMinutes, $SVCRequest);
                       // $SVCRequest = str_replace("{replaceMe2}", $CCMIP, $SVCRequest);

            $SVCHeaderSuffix = "SOAPAction: \"http://schemas.cisco.com/ast/soap/action/#LogCollectionPort#SelectLogFiles";
            curl_setopt($ch, CURLOPT_URL, "https://$CCMIP/logcollectionservice/services/LogCollectionPort");


                        $AXLHeader = array("Content-Type: text/xml; charset=utf-8",
                                "Authorization: Basic ".base64_encode("$CCMLogin:$CCMPassword"),
                                "Content-Length: ".strlen($SVCRequest),
                                                                $SVCHeaderSuffix);

                curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
                curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, false);
                curl_setopt($ch, CURLOPT_HTTPHEADER, $AXLHeader);
                curl_setopt($ch, CURLOPT_POST, 1);
                curl_setopt($ch, CURLOPT_POSTFIELDS, $SVCRequest);
                curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
                        curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 15);
                        curl_setopt($ch, CURLOPT_TIMEOUT, 15);

                        $retValue = curl_exec($ch)      ;

						//echo $retValue;
                        $retValue = strBetweenI($retValue,"<SetOfFiles","</SetOfFiles>");


                        if (strlen($retValue)<100) {return;}

                        $xml = new SimpleXMLElement($retValue);

                        $counter = 0; $retValue = "";

                        for ($i=0; $i<count($xml); $i++)
                        {
                                /*echo "<tr>";
                                echo "<td>".$xml->item[$i]->name."</td>";
                                echo "<td>". $xml->item[$i]->absolutepath."</td>";
                                echo "<td>". $xml->item[$i]->filesize."</td>";
                                echo "<td>". $xml->item[$i]->modifiedDate."</td>";
                                echo "<td>". $LogType."</td>";
                                echo "</tr>"; */
                                $retValue[$i] = $xml->item[$i]->absolutepath."|".$xml->item[$i]->modifiedDate;
                        }

                        return $retValue;
}
        //$testDownload = $xml->item[0]->absolutepath;

        //====================================================================
        // Now we pull the file(s) available //

$ch = curl_init();


function downloadSingleFile($ch, $CCMIP, $CCMLogin, $CCMPassword, $logFile)
{

                        $SVCRequest = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\"
xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\"
xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">
 <soapenv:Body>
  <ns1:GetOneFile soapenv:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\"
xmlns:ns1=\"DimeGetFileService\">
   <FileName xsi:type=\"xsd:string\">{replaceMe}</FileName>
  </ns1:GetOneFile>
 </soapenv:Body>
</soapenv:Envelope>";

            $SVCHeaderSuffix = "SOAPAction: \"http://schemas.cisco.com/ast/soap/action/#LogCollectionPort#GetOneFile";
            curl_setopt($ch, CURLOPT_URL, "https://$CCMIP/logcollectionservice/services/DimeGetFileService");

                        $SVCRequest = str_replace("{replaceMe}", $logFile, $SVCRequest);

                        $AXLHeader = array("Content-Type: text/xml; charset=utf-8",
                                                                        "Authorization: Basic ".base64_encode("$CCMLogin:$CCMPassword"),
                                                                        "Content-Length: ".strlen($SVCRequest),
                                                                $SVCHeaderSuffix);

                curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
                curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, false);
                curl_setopt($ch, CURLOPT_HTTPHEADER, $AXLHeader);
                curl_setopt($ch, CURLOPT_POST, 1);
                curl_setopt($ch, CURLOPT_POSTFIELDS, $SVCRequest);
                curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
                        curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 15);
                        curl_setopt($ch, CURLOPT_TIMEOUT, 15);

                        $retValue = curl_exec($ch);

						// Check for CSCuv89821
						if (strpos($retValue, "file not allowed for download")>0) {echo "\r\nDetected Bug: CSCuv89821.  Skipping...";return "";}

						// Must CLEAN the MIME multi-part
						preg_match('/(?<xml><.*?\?xml version=.*>)/', $retValue, $match);
						$xml = $match['xml'];

						// Strip SOAP http headers, and SOAP XML
						$offset = strpos($retValue, $xml) + strlen($xml . PHP_EOL);
						$retValue = substr($retValue, $offset);

						/////////////////////

						preg_match('/--(?<MIME_boundary>.+?)\s/', $retValue, $match);
						$mimeBoundary = $match['MIME_boundary']; // Always unique compared to content

						// Remove string headers and MIME boundaries from data
						preg_match('/(.*Content-Id.+'.PHP_EOL.')/', $retValue, $match);
						$start = strpos($retValue, $match[1]) + strlen($match[1]);
						$end = strpos($retValue, "--$mimeBoundary--");
						$retValue = substr($retValue, $start, $end-$start);

						$retValue = trim($retValue, "\r\n");
						echo "string len:".strlen($retValue);
                        return $retValue;
}



function moveCursor($x="", $y="")
{
	global $globalANSI;

	if ($globalANSI==false) {return;}

	echo "\e[{$y};{$x}f";
}
function colorClearScreen()
{
	global $globalANSI;

	if ($globalANSI==false) {echo $text;return;}

	//echo "\e[2J ";
}

function colorTextFiltered($foreGround, $backGround, $text="")
{
	global $globalANSI;

	if ($globalANSI==false) {echo $text;return;}

	$foreGround = strtolower($foreGround);
	$backGround = strtolower($backGround);
	$bold = 0;$invBold=1;


	if ( strpos( " ".$foreGround, "bold")>0 )
	{
		$bold = 1;$invBold=0;
		$foreGround = str_replace("bold","",$foreGround);
	}

	switch ( strtolower($foreGround) )
	{
		case 'black':
			$foreGround="30";
			break;
		case 'blue':
			$foreGround="34";
			break;
		case 'green':
			$foreGround="32";
			break;
		case 'cyan':
			$foreGround="36";
			break;
		case 'red':
			$foreGround="31";
			break;
		case 'purple':
			$foreGround="35";
			break;
		case 'yellow':
			$foreGround="33";
			break;
		case 'white':
			$foreGround="37";
			break;
	}

	switch ( strtolower($backGround) )
	{
		case 'black':
			$backGround="40";
			break;
		case 'blue':
			$backGround="44";
			break;
		case 'green':
			$backGround="42";
			break;
		case 'cyan':
			$backGround="46";
			break;
		case 'red':
			$backGround="41";
			break;
		case 'purple':
			$backGround="45";
			break;
		case 'yellow':
			$backGround="43";
			break;
		case 'white':
			$backGround="47";
			break;
	}


	$text = str_replace("[","[\e[{$invBold};{$foreGround};{$backGround}m",$text);
	$text = str_replace("]", "\e[{$bold};{$foreGround};{$backGround}m]",$text);

	$filtered=1;
	if (strpos(" ".$text,"CallManager")>0){$filtered=0;}
	if (strpos(" ".$text,"CDR")>0){$filtered=0;}
	if (strpos(" ".$text,"Tomcat")>0){$filtered=0;}
	if (strpos(" ".$text,"RIS")>0){$filtered=0;}
	if (strpos(" ".$text,"DRF")>0){$filtered=0;}
	if (strpos(" ".$text,"CTI")>0){$filtered=0;}
	if (strpos(" ".$text,"Tftp")>0){$filtered=0;}
	if (strpos(" ".$text,"IP Voice Media")>0){$filtered=0;}
	if (strpos(" ".$text,"Event Viewer")>0){$filtered=0;}
	if (strpos(" ".$text,"Install")>0){$filtered=0;}
	if (strpos(" ".$text,"Packet Capture")>0){$filtered=0;}
	if (strpos(" ".$text,"XCP")>0){$filtered=0;}
	if (strpos(" ".$text,"Proxy")>0){$filtered=0;}
	if (strpos(" ".$text,"Presence")>0){$filtered=0;}
	if (strpos(" ".$text,"Connection")>0){$filtered=0;}
	if ($filtered==1){return;}

	echo "\e[{$bold};{$foreGround};{$backGround}m$text";
	if (strlen($text)>0) {echo "\e[0;37;40m";}
}

function colorText($foreGround, $backGround, $text="")
{
	global $globalANSI;

	if ($globalANSI==false) {echo $text;return;}

	$foreGround = strtolower($foreGround);
	$backGround = strtolower($backGround);
	$bold = 0;$invBold=1;


	if ( strpos( " ".$foreGround, "bold")>0 )
	{
		$bold = 1;$invBold=0;
		$foreGround = str_replace("bold","",$foreGround);
	}

	switch ( strtolower($foreGround) )
	{
		case 'black':
			$foreGround="30";
			break;
		case 'blue':
			$foreGround="34";
			break;
		case 'green':
			$foreGround="32";
			break;
		case 'cyan':
			$foreGround="36";
			break;
		case 'red':
			$foreGround="31";
			break;
		case 'purple':
			$foreGround="35";
			break;
		case 'yellow':
			$foreGround="33";
			break;
		case 'white':
			$foreGround="37";
			break;
	}

	switch ( strtolower($backGround) )
	{
		case 'black':
			$backGround="40";
			break;
		case 'blue':
			$backGround="44";
			break;
		case 'green':
			$backGround="42";
			break;
		case 'cyan':
			$backGround="46";
			break;
		case 'red':
			$backGround="41";
			break;
		case 'purple':
			$backGround="45";
			break;
		case 'yellow':
			$backGround="43";
			break;
		case 'white':
			$backGround="47";
			break;
	}


	$text = str_replace("[","[\e[{$invBold};{$foreGround};{$backGround}m",$text);
	$text = str_replace("]", "\e[{$bold};{$foreGround};{$backGround}m]",$text);


	echo "\e[{$bold};{$foreGround};{$backGround}m$text";
	if (strlen($text)>0) {echo "\e[0;37;40m";}
}


function strBetweenI($source, $str1, $str2,$offSet=0)
{
        $source = " ".$source;
        //echo "\r\n\r\nVars".strpos($source, $str1)."\t\t".strpos($source,$str2)."\r\n";

        if (strpos($source,$str1)>0 && strpos($source,$str2)>0) return substr($source, ( strpos($source,$str1) ),
		( (strpos($source,$str2,(strpos($source,$str1)))+strlen($str2)) - (strpos($source,$str1))  ));

        return "";
}

function strBetweenNI($source, $str1, $str2,$offSet=0)
{
        $source = " ".$source;
        //echo "\r\n\r\nVars".strpos($source, $str1)."\t\t".strpos($source,$str2)."\r\n";

        if (strpos($source,$str1)>0 && strpos($source,$str2)>0) return substr($source, ( strpos($source,$str1)+strlen($str1) ),
		(    (	strpos($source,$str2,strpos($source,$str1)+strlen($str1))) - (strpos($source,$str1)+strlen($str1))	)   );

        return "";
}


function convert_seconds($ss)
 {
$s = $ss%60;
$m = floor(($ss%3600)/60);
$h = floor(($ss%86400)/3600);
$d = floor(($ss%2592000)/86400);
$M = floor($ss/2592000);

return "$M months, $d days, $h hours, $m minutes, $s seconds";  }
?>