#!/bin/bash
#############################################
#Need to install ***-tools,sshpass in driver.
#############################################

DEFAULT_PASSWORD=default_password
AV_PASSWORD=av_password

function Wait_Until_Package_Status_Is_Accepted(){
    pack_status=`avi-cli $av_server_ip --password $DEFAULT_PASSWORD --supportkey $SUPPORTKEY --listrepository --port 7543 | grep .avp | awk -F " " '{print $5}'`
    if [[ $pack_status == Accepted ]]; then
        echo "Package status is Accepted."
        else
        echo "Wait until package is available..."
	    while [[ $pack_status != Accepted ]]
	    do
	        echo "Wait 10s for package available..."
		    sleep 10
		    pack_status=`avi-cli $av_server_ip --password $DEFAULT_PASSWORD --supportkey $SUPPORTKEY --listrepository --port 7543 | grep .avp | awk -F " " '{print $5}'`
        done
fi
}

while getopts "s:v:h" opt
do
    case $opt in
        s)
            echo "Avamar Server IP is $OPTARG"
            av_server_ip=$OPTARG
            ;;
        v)
            echo "Avamar Server Version is $OPTARG"
            av_server_version=`echo $OPTARG | awk -F "." '{print $1""$2""$3}'`
			;;
		h)
            echo "Usage: install_av_remote.sh -s Avamar_Server_IP -v Avamar_Server_Version,eg.19.4.0.7"
            exit
            ;;
        :)
            echo "You need to add -s and -v followed by this script, use "install_av_remote.sh -h" to see details."
                exit 1
            ;;
        ?)
            echo "Wrong parameters."
                exit 2
            ;;
    esac
done


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

#Clear host info in /root/.ssh/known_hosts
sed -i "/^$av_server_ip/d" /root/.ssh/known_hosts

#Wait Until AV boot up.
while ! ping -c 1 $av_server_ip &> /dev/null
	do
	    echo "Waiting 5s for *** Server booting up..."
		sleep 5
	done
	echo "*** Server is online."

sleep 30s
Wait_Until_Package_Status_Is_Accepted

#Install AV.
cp /root/install_av.yaml /root/install_av_$av_server_ip.yaml
echo "hfsaddr: $av_server_ip" >> /root/install_av_$av_server_ip.yaml
avi-cli $av_server_ip -v --password $DEFAULT_PASSWORD --supportkey $SUPPORTKEY --install ave-config --userinput /root/install_av_$av_server_ip.yaml --port 7543
rm -f /root/install_av_$av_server_ip.yaml

#Enable root login
sshpass -p "$AV_PASSWORD" ssh -o StrictHostKeyChecking=no admin@$av_server_ip 'su root -c "cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup" <<END
av_password(plain text)
END'

sshpass -p "$AV_PASSWORD" ssh -o StrictHostKeyChecking=no admin@$av_server_ip 'su root -c "sed -i '/^PermitRootLogin/s/no/yes/' /etc/ssh/sshd_config" <<END
av_password(plain text)
END'

sshpass -p "$AV_PASSWORD" ssh -o StrictHostKeyChecking=no admin@$av_server_ip 'su root -c "service sshd restart" <<END
av_password(plain text)
END'
