#!/bin/bash
#############################################
#Need to install ***-tools, sshpass in driver.
#############################################

AV_PASSWORD=av_password

function Wait_Until_Package_Status_Is_Accepted(){
    pack_status=`avi-cli $av_server_ip --password $AV_PASSWORD --supportkey $SUPPORTKEY --listrepository --port 7543 | grep .avp | awk -F " " '{print $5}'`
    if [[ $pack_status == Accepted ]]; then
        echo "Package status is Accepted."
        else
        echo "Wait until package is available..."
	    while [[ $pack_status != Accepted ]]
	    do
	        echo "Wait 10s for package available..."
		    sleep 10
		    pack_status=`avi-cli $av_server_ip --password $AV_PASSWORD --supportkey $SUPPORTKEY --listrepository --port 7543 | grep .avp | awk -F " " '{print $5}'`
        done
fi
}

function Validate_A_Checkpoint(){
    cp_status=`sshpass -p "$AV_PASSWORD" ssh -o StrictHostKeyChecking=no admin@$av_server_ip mccli checkpoint show | grep cp. | awk -F " " '{print $5}'`
    if [[ $cp_status == *Validated* ]]; then
    echo "There is a validated checkpoint already."
	else
	echo "Start to validate the latest checkpoint..."
	last_cptag=`sshpass -p "$AV_PASSWORD" ssh -o StrictHostKeyChecking=no admin@$av_server_ip mccli checkpoint show | grep cp. | awk -F " " '{print $1}' | tail -n 1`
    sshpass -p "$AV_PASSWORD" ssh -o StrictHostKeyChecking=no admin@$av_server_ip mccli checkpoint validate --cptag=$last_cptag
	all_cp_status=`sshpass -p "$AV_PASSWORD" ssh -o StrictHostKeyChecking=no admin@$av_server_ip mccli checkpoint show | grep cp. | awk -F " " '{print $5}'`
	while [[ $all_cp_status != *Validated* ]]
	do
	    echo "Waiting 30s for checkpoint validation..."
	    sleep 30
		all_cp_status=`sshpass -p "$AV_PASSWORD" ssh -o StrictHostKeyChecking=no admin@$av_server_ip mccli checkpoint show | grep cp. | awk -F " " '{print $5}'`
	done 
    fi
}

while getopts "s:u:h" opt
do
    case $opt in
        s)
            echo "**** Server IP is $OPTARG"
            av_server_ip=$OPTARG
            ;;
		#v)
        #    echo "**** Server Version is $OPTARG"
        #    av_server_version=`echo $OPTARG | awk -F "." '{print $1""$2""$3}'`
		#	;;
        u)
            echo "**** Upgrade Version is $OPTARG"
			av_upgrade_version_full=$OPTARG
            av_upgrade_version=`echo $OPTARG | awk -F "." '{print $1""$2""$3}'`
			;;
		h)
            echo "Usage: upgrade_av_remote.sh -s ****_Server_IP -v ****_Server_Version,eg.19.4.0.1 -u ****_Upgrade_Version,eg.19.*.0.1"
            exit
            ;;
        :)
            echo "You need to add -s -v and -u followed by this script, use "upgrade_av_remote.sh -h" to see details."
                exit 1
            ;;
        ?)
            echo "Wrong parameters."
                exit 2
            ;;
    esac
done

av_server_version=`sshpass -p "$AV_PASSWORD" ssh -o StrictHostKeyChecking=no admin@$av_server_ip avmgr --version | grep version | grep -v OS | awk -F " " '{print $2}' | awk -F "." '{print $1""$2""$3""}' | awk -F "-" '{print $1}'`
case $av_server_version in
    73[0-1]) 
	    SUPPORTKEY=key1
		;;
	74[0-1])
	    SUPPORTKEY=key2
		;;
	75[0-1])
	    SUPPORTKEY=key3
		;;
	18[1-2]0)
	    SUPPORTKEY=key4
		;;
	19[1-5]0)
	    SUPPORTKEY=key5
		;;
esac

#Mount build server to driver
mount -t nfs -o vers=3 build_server_ip:/qadepot /qadepot/

#cp upgrade package to ****
sshpass -p "$AV_PASSWORD" scp -o StrictHostKeyChecking=no /qadepot/builds/v$av_upgrade_version_full/PACKAGES/****Upgrade*.avp root@$av_server_ip:/****/****/repo/packages/

#Validate A Checkpoint
Validate_A_Checkpoint

#Wait Until Upgrade Package Is Accepted
Wait_Until_Package_Status_Is_Accepted

#Create YAML file.
echo -e "required_packages: false\nlinux_root_password: ${AV_PASSWORD}\nlinux_admin_password: ${AV_PASSWORD}" > /root/install_upgrade_${av_server_ip}.yaml

#Install Upgrade Package
avi-cli $av_server_ip --password $AV_PASSWORD --supportkey $SUPPORTKEY --userinput /root/install_upgrade_${av_server_ip}.yaml --install ****Upgrade$av_upgrade_version --port 7543
