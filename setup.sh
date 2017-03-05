#!/bin/sh    
if [ $1 = 'start' ];then
	if [ $2 = 'all' ];then
		cd eggtart
        cd main_control
		python Maincontrol.py start
        cd ..
        cd business_handle
		python BusinessHandle.py start
		cd ..
		cd test_engine
		python TestEngine.py start
		cd ..

	else
        cd eggtart
		case  $2  in 
		"main_control")
		cd main_control
		python Maincontrol.py start
		cd ..
		;;
		"business_handle")
		cd business_handle
		python BusinessHandle.py start
		cd ..
		;;
		"test_engine")
		cd test_engine
		python TestEngine.py start
		cd ..
		;;
		esac
	fi
elif [ $1 = 'stop' ]; then
		if [ $2 = 'all' ];then
		cd eggtart
        cd main_control
		python Maincontrol.py stop
        cd ..
        cd business_handle
		python BusinessHandle.py stop
		cd ..
		cd test_engine
		python TestEngine.py stop
		cd ..

	else
        cd eggtart
		case  $2  in 
		"main_control")
		cd main_control
		python Maincontrol.py stop
		cd ..
		;;
		"business_handle")
		cd business_handle
		python BusinessHandle.py stop
		cd ..
		;;
		"test_engine")
		cd test_engine
		python TestEngine.py stop
		cd ..
		;;
		esac
	fi

elif [ $1 = 'restart' ]; then
		if [ $2 = 'all' ];then
		cd eggtart
        cd main_control
		python Maincontrol.py restart
        cd ..
        cd business_handle
		python BusinessHandle.py restart
		cd ..
		cd test_engine
		python TestEngine.py restart
		cd ..

	else
        cd eggtart
		case  $2  in 
		"main_control")
		cd main_control
		python Maincontrol.py restart
		cd ..
		;;
		"business_handle")
		cd business_handle
		python BusinessHandle.py restart
		cd ..
		;;
		"test_engine")
		cd test_engine
		python TestEngine.py restart
		cd ..
		;;
		esac
	fi

else
	echo 'NO this param'
fi
