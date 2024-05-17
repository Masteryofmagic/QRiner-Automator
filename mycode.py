#system_check class
    #check for file options.json in current directory
        #if exists then load options into options dictonary
        #if does not exist then call option_build class￼
        #if --options argument is given on command line, then call option build class

#option_build class
    #if options.json exist, load into dictionary before asking questions
    #Ask user the following questions And store in dictionary for later writing to file.
        #Allow CPU Mining?   default is Yes.  Y/n  (JSON Code CPUMining)
        #CPU Alias?   Defuatl is CPU.  Only as if CPU Mining is True  (JSON Code CPUAlias)
        #Allow GPU Mining (CUDA ONLY)?   default is no.  Y/n   (JSON Code GPUMining)
        #GPU Alias?   Defuatl is GPU.  Only as if GPU Mining is True  (JSON Code GPUAlias)
        #Start Mining on Application Startup?  Default is yes.  Y/n   (JSON Code Autostart)
        #Automatically Update File When Available?  Default is yes.  Y/n   (JSON Code AutoUpdate)
        #Automatically Benchmark CPU Versions?   Default as yes.  Y/n   (JSON Code AutoBench)
        #Automatically Restart Miners as Needed?    Default is yes.  Y/n   (JSON Code AutoRestart)
        #Please Enter File Path for Mining Files?  Default his current directory.   (JSON Code FilePath)
        #Please Enter Payout ID?  Required field. No default.   (JSON Code PayID)
        #How Many CPU Threads?  default is maximum logical processors   (JSON Code ThreadCount)
        #Hide Mining Windows?  default is no. Y/n.  (JSON Code HideWindows)
    #Save Options.json file

#update_files class
    #if auto update equals true
        #if Update required = true
            #compare local exe file to github repository files
            #if github file newer delete local file
            #download newer file to file path
            #set updated file flag true else updated flag false

#start_process class (type of process)
    #if autostart = true
        #if type = cpu
            #read benchmark file and pull highest exe hash rate
            #store file name to be run
            #read hide window flag from dictionary
            #if hide window flag true change arguments
                #else run with show window true
            #create command with arguments from dictionary
            #run command and pass proc back to calling function
        #if type = gpu
            #store file name to be run
            #read hide window flag from dictionary
            #if hide window flag true change arguments
                #else run with show window true
            #create command with arguments from dictionary
            #run command and pass proc back to calling function


#monitor_proc class (proc)
    # start thread for monitoring
        #Start monitor timer
            #when time expires, call update class
                #update returned as true kill proc
                #set restart flag to true
                #check and see if process is running
                    #process not running, restart flag to true
