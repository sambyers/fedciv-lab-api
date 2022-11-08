import paramiko
from time import sleep
import sys


def restore_appliance(ipaddress, uname, passw, appliance_type, backup_id):
    print("Restoring ", appliance_type, " with backup ", backup_id)

    if appliance_type == "DNAC":
        print("DNAC restore stub ", ipaddress)

        # Connect to appliance
        conn = paramiko.SSHClient()
        conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        conn.connect(ipaddress, username=uname, password=passw, port=2222)
        sleep(4)
        router_conn = conn.invoke_shell()
        sleep(4)
        print("Successfully connected to %s" % ipaddress)

        # kickoff restore
        restore_cmd = "maglev restore apply " + backup_id + "\n"
        router_conn.send(restore_cmd)
        sleep(6)
        response = router_conn.recv(5000).decode("utf-8")
        print(response)
        if "username" in response:
            router_conn.send("admin\n")
            sleep(6)
            response = router_conn.recv(5000).decode("utf-8")
            print(response)
        else:
            print("Did not ask for username!, skipping to password")
        if "password" in response:
            router_conn.send(DNACPASS + "\n")
            sleep(6)
            response = router_conn.recv(5000).decode("utf-8")
            print(response)
        else:
            print("Did not ask for password... Restore failed!!!  Aborting!")
            sys.exit()
        print("DNAC restoring :)")

    elif appliance_type == "ISE":
        print("ISE restore stub")

        # Connect to appliance
        conn = paramiko.SSHClient()
        conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        conn.connect(ipaddress, username=uname, password=passw)
        router_conn = conn.invoke_shell()
        print("Successfully connected to %s" % ipaddress)

        # kickoff restore
        restore_cmd = (
            "restore Ready-for-DNAC-demo-CFG10-210317-1813.tar.gpg "
            + "repository labdash-ftp encryption-key plain C1sco123\n"
        )
        print(restore_cmd)
        router_conn.send(restore_cmd)

        sleep(2)

        print(router_conn.recv(5000).decode("utf-8"))
        print("ISE restoring... please wait approx 30 minutes")
        sleep(1800)
        print(router_conn.recv(5000).decode("utf-8"))
        print("ISE restore complete... We will continue while ISE reboots")

    elif appliance_type == "VMANAGE":

        # Connect to appliance
        conn = paramiko.SSHClient()
        conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        conn.connect(ipaddress, username=uname, password=passw)
        router_conn = conn.invoke_shell()
        print("Successfully connected to %s" % ipaddress)

        # kickoff restore
        router_conn.send("\n")
        sleep(2)
        print(router_conn.recv(5000).decode("utf-8"))
        restore_cmd = (
            "request nms configuration-db restore path /home/admin/" + backup_id + "\n"
        )
        print(restore_cmd)
        router_conn.send(restore_cmd)

        sleep(2)

        print(router_conn.recv(5000).decode("utf-8"))
        print("vManage restoring...")

        sleep(600)
        print(router_conn.recv(5000).decode("utf-8"))
        print("vManage restore complete... ")

    else:
        pass  # ERROR MESSAGES HERE
        print("Not sure what you want me to restore... erroring out")
        sys.exit()
