#!/usr/bin/python3.6

'''
Need to install Python3.6 or higher version,***-tools,pycrypto and paramiko on Linux Driver.
pip3 install pycrypto
pip3 install paramiko
'''

import getopt
import os
import re
import subprocess
import sys
import time
import paramiko


AV_PASSWORD = "av_password"

def script_usage():
    print("Usage: upgrade_av_remote.py -s ****_Server_IP -u ****_Upgrade_Version,eg.19.4.0.1")

def opt_arg():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hs:u:", ["server_ip=", "av_upgrade_version="])
    except getopt.GetoptError as err:
        print(err)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            script_usage()
        elif opt in ("-s", "--server_ip"):
            av_server_ip = arg
            #print("**** Server IP is " + av_server_ip)
        elif opt in ("-u", "--av_upgrade_version"):
            av_server_upgrade_full_name = arg
            av_server_upgrade_version_list = arg.split('.')[:-1]
            av_server_upgrade_version = ''.join(av_server_upgrade_version_list)
            #print("**** Server Version is " + av_server_version)
            return av_server_upgrade_version, av_server_ip, av_server_upgrade_full_name

if __name__ == '__opt_arg__':
    opt_arg()

def support_key():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=opt_arg()[1], port=22, username='admin', password=AV_PASSWORD)
    cmd = "avmgr --version | grep version | grep -v OS | awk -F ' ' '{print $2}' | awk -F '.' '{print $1""$2""$3""}' | awk -F '-' '{print $1}'"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    av_server_version = stdout.readlines()
    if re.match('73[0-1]', av_server_version[0]):
        supportkey = 'key1'
    elif re.match('74[0-1]', av_server_version[0]):
        supportkey = 'key2'
    elif re.match('75[0-1]', av_server_version[0]):
        supportkey = 'key3'
    elif re.match('18[1-2]0', av_server_version[0]):
        supportkey = 'key4'
    elif re.match('19[1-5]0', av_server_version[0]):
        supportkey = 'key5'
    return supportkey

def wait_until_package_status_is_accept():
    cmd = "avi-cli " + opt_arg()[1] + " --password " + AV_PASSWORD + " --supportkey " + support_key() + " --listrepository --port 7543 | grep .avp | awk -F ' ' '{print $5}'"
    print(cmd)
    pack_status = subprocess.getoutput(cmd)
    while 'Accepted' not in pack_status:
        print("Wait 10s for package available...")
        time.sleep(10)
        pack_status = subprocess.getoutput(cmd)
    if 'Accepted' in pack_status:
        print("Package status is Accepted.")

def validate_a_checkpoint():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=opt_arg()[1], port=22, username='admin', password=AV_PASSWORD)
    cmd_cp = "mccli checkpoint show | grep cp. | awk -F ' ' '{print $5}'"
    stdin, stdout, stderr = ssh.exec_command(cmd_cp)
    cp_status = stdout.readlines()
    if 'Validated\n' not in cp_status:
        print("Start to validate the latest checkpoint...")
        cmd_last_cptag = "mccli checkpoint show | grep cp. | awk -F ' ' '{print $1}' | tail -n 1"
        stdin, stdout, stderr = ssh.exec_command(cmd_last_cptag)
        last_cptag = stdout.readlines()
        print(last_cptag)
        print(last_cptag[0])
        cmd_validate_last_cp = "mccli checkpoint validate --cptag=" + last_cptag[0]
        stdin, stdout, stderr = ssh.exec_command(cmd_validate_last_cp)
        cmd_all_status = "mccli checkpoint show | grep cp. | awk -F ' ' '{print $5}'"
        stdin, stdout, stderr = ssh.exec_command(cmd_all_status)
        all_status = stdout.readlines()
        while 'Validated\n' not in all_status:
            print("Wait 30s for checkpoint validation...")
            time.sleep(30)
            stdin, stdout, stderr = ssh.exec_command(cmd_all_status)
            all_status = stdout.readlines()
            print(all_status)
        if 'Validated\n' in all_status[:]:
            print("Checkpoint has been validated.")
    else:
        print("There is a validated checkpoint already.")

def cp_upgrade_pack_to_av():
    print("Start to copy upgrade package to **** server...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=opt_arg()[1], port=22, username='root', password=AV_PASSWORD)
    av_upgrade_build_list = opt_arg()[2].split('.')[0:-1]
    av_upgrade_build = '.'.join(av_upgrade_build_list)
    av_upgrade_version_list = opt_arg()[2].split('.')
    av_upgrade_version = av_upgrade_version_list[-1]
    #print(av_upgrade_build)
    #print(av_upgrade_version)
    cmd = "/etc/init.d/avfirewall stop"
    print(cmd)
    ssh.exec_command('/etc/init.d/avfirewall stop')
    cmd = "wget http://build_server_ip/builds/v" + opt_arg()[2] + "/PACKAGES/A****Upgrade-" + av_upgrade_build + "-" + av_upgrade_version + ".avp -P /****/****/repo/packages/"
    print(cmd)
    stdin, stdout, stderr = ssh.exec_command(cmd)
    result_info = ""
    for line in stderr.readlines():
        result_info += line

def install_upgrade_pack():
    cmd = "avi-cli " + opt_arg()[1] + " --password " + AV_PASSWORD + " --supportkey " + support_key() + " --userinput /root/install_upgrade_" + opt_arg()[1] + ".yaml --install ****Upgrade" + opt_arg()[0] + " --port 7543"
    print("Start to upgrade **** Server...")
    print(cmd)
    install_status = subprocess.getoutput(cmd)
    print(install_status)


print("**** Server IP is " + opt_arg()[1])

print("**** Server Upgrade Version is " + opt_arg()[0])

support_key()

print("SupportKey is " + support_key())

#Copy upgrade package to ****.
cp_upgrade_pack_to_av()

validate_a_checkpoint()

wait_until_package_status_is_accept()

#Create the YAML file.
os.system('echo -e "required_packages: false\nlinux_root_password: ' + AV_PASSWORD +'\nlinux_admin_password: ' + AV_PASSWORD + '" > /root/install_upgrade_' + opt_arg()[1] + '.yaml')

install_upgrade_pack()

#Remove the YAML file.
os.system('rm -f /root/install_upgrade_' + opt_arg()[1] + '.yaml')

