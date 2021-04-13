#!/usr/bin/python3.6

'''
Need to install Python3.6 or higher version,***-tools,pycrypto and paramiko on Linux driver.
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

DEFAULT_PASSWORD = "DEFAULT_PASSWORD"
AV_PASSWORD = "AV_PASSWORD"

def script_usage():
    print("Usage: install_av_remote.py -s ****_Server_IP -v ****_Server_Version,eg.19.4.0.9")

def opt_arg():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hs:v:", ["server_ip=", "av_version="])
    except getopt.GetoptError as err:
        print(err)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            script_usage()
        elif opt in ("-s", "--server_ip"):
            av_server_ip = arg
            #print("**** Server IP is " + av_server_ip)
        elif opt in ("-v", "--av_version"):
            av_server_version_list = arg.split('.')[:-1]
            av_server_version = ''.join(av_server_version_list)
            #print("**** Server Version is " + av_server_version)
            return av_server_version, av_server_ip

if __name__ == '__opt_arg__':
    opt_arg()


def support_key():
    if re.match('73[0-1]', opt_arg()[0]):
        supportkey = 'KEY1'
    elif re.match('74[0-1]', opt_arg()[0]):
        supportkey = 'KEY2'
    elif re.match('75[0-1]', opt_arg()[0]):
        supportkey = 'KEY3'
    elif re.match('18[1-2]0', opt_arg()[0]):
        supportkey = 'KEY4'
    elif re.match('19[1-5]0', opt_arg()[0]):
        supportkey = 'KEY5'
    return supportkey

def wait_until_package_status_is_accept():
    cmd = "avi-cli " + opt_arg()[1] + " --password " + DEFAULT_PASSWORD + " --supportkey " + support_key() + " --listrepository --port 7543 | grep .avp | awk -F ' ' '{print $5}'"
    print(cmd)
    pack_status = subprocess.getoutput(cmd)
    #print(pack_status)
    while 'Accepted' not in pack_status:
        print("Wait 10s for package available...")
        time.sleep(10)
        pack_status = subprocess.getoutput(cmd)
    if 'Accepted' in pack_status:
        print("Package status is Accepted.")

# Clear host info in /root/.ssh/known_hosts.
def clear_host():
    os.system('sed -i "/^' + opt_arg()[1] + '/d" /root/.ssh/known_hosts')

# Wait Until AV boot up.
def ping_av():
    av_status = os.system('ping -c 1 ' + opt_arg()[1])
    while av_status != 0:
        print("Waiting 5s for **** Server booting up...")
        time.sleep(5)
        av_status = os.system('ping -c 1 ' + opt_arg()[1])
    print("**** Server is online.")
    print("Sleep 30s until avi-cli available...")
    time.sleep(30) #Wait until avi-cli available.

# Install AV
def install_av():
    os.system('cp /root/install_av.yaml /root/install_av_' + opt_arg()[1] + '.yaml')
    os.system('echo "hfsaddr: ' + opt_arg()[1] +'"  >> /root/install_av_' + opt_arg()[1] +'.yaml')
    cmd = "avi-cli " + opt_arg()[1] + " -v --password " + DEFAULT_PASSWORD + " --supportkey " + support_key() + " --install ave-config --userinput /root/install_av_" + opt_arg()[1] + ".yaml --port 7543"
    print("Start to install **** Server...")
    print(cmd)
    install_status = subprocess.getoutput(cmd)
    print(install_status)
    os.system('rm -f /root/install_av_' + opt_arg()[1] + '.yaml')

#Enable root login over ssh.
def enable_ssh():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=opt_arg()[1], port=22, username='admin', password=AV_PASSWORD)
    stdin, stdout, stderr = ssh.exec_command('su - root')
    time.sleep(1)
    stdin.write(AV_PASSWORD + '\n')
    stdin.write('cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup\n')
    stdin.flush()
    cmd = "sed -i '/^PermitRootLogin/s/no/yes/' /etc/ssh/sshd_config"
    stdin.write(cmd + '\n')
    stdin.flush()
    time.sleep(1)
    stdin.write('service sshd restart\n')
    ssh.close()
    print("root login over ssh is enabled.")


clear_host()

print("**** Server IP is " + opt_arg()[1])

print("**** Server Version is " + opt_arg()[0])

ping_av()

support_key()

print("SupportKey is " + support_key())

wait_until_package_status_is_accept()

install_av()

enable_ssh()
