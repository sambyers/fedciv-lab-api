import os
import pytest
from unittest.mock import MagicMock
from genie.testbed import load
from lab_api.services import ISE, Appliance, DNAC, DeviceLab


# DeviceLab Setup


@pytest.fixture()
def testbed():
    # Setup testbed for testing
    yield load(os.getenv("CIVLAB_NETDEVICE_DATA"))


@pytest.fixture()
def devicelab(testbed):
    # Setup LabDevice object
    obj = DeviceLab(testbed)
    yield obj


@pytest.fixture()
def device():
    # Mock device
    obj = MagicMock()
    obj.connect = MagicMock()
    obj.api.get_platform_default_dir = MagicMock(return_value="test")
    obj.api.verify_file_exists = MagicMock(return_value=True)
    obj.api.get_running_config_dict = MagicMock(return_value="test")
    obj.api.get_config_from_file = MagicMock(return_value="test")
    obj.api.compare_config_dicts = MagicMock(return_value="")
    yield obj


# DeviceLab tests


def test_devicelab_testbed(testbed, devicelab):
    assert testbed == devicelab.testbed


def test_devicelab_default_cfg_file(testbed, devicelab):
    assert testbed.custom.default_cfg_file == devicelab.default_cfg_file


def test_devicelab_get_default_cfg_exists(devicelab, device):
    devicelab.get_default_cfg_exists(device)
    device.api.get_platform_default_dir.assert_called_once()
    device.api.verify_file_exists.assert_called_once_with(device.default_cfg_path)
    assert device.default_config_exists


def test_devicelab_get_default_cfg_exists_all(devicelab, device):
    devicelab.get_default_cfg_exists = MagicMock()
    devicelab.get_default_cfg_exists_all()
    devicelab.get_default_cfg_exists.assert_called()


def test_devicelab_get_running_default_cfg_diff(devicelab, device):
    device.connect()
    devicelab.get_running_default_cfg_diff(device)
    device.api.get_running_config_dict.assert_called_once()
    device.api.get_config_from_file.assert_called_with(
        device.default_dir, devicelab.default_cfg_file
    )
    device.api.compare_config_dicts.assert_called_with(
        device.running_cfg, device.default_cfg
    )


def test_devicelab_get_running_default_cfg_diff_all(devicelab, device):
    devicelab.get_running_default_cfg_diff = MagicMock()
    devicelab.get_running_default_cfg_diff_all()
    devicelab.get_running_default_cfg_diff.assert_called()


def test_devicelab_reset_device_to_default(devicelab, device):
    # Mock setup
    devicelab.get_running_default_cfg_diff = MagicMock(return_value="test")
    device.default_cfg_path = "test"
    device.api.execute_copy_to_startup_config = MagicMock()
    device.api.execute_reload = MagicMock()
    # Test
    devicelab.reset_device_to_default(device, sleep=1, timeout=2)
    # Asserts
    device.api.execute_copy_to_startup_config.assert_called_once_with(
        device.default_cfg_path
    )
    device.api.execute_reload.assert_called_once_with(
        prompt_recovery=False,
        reload_creds="default",
        sleep_after_reload=1,
        timeout=2,
    )


# Appliance Setup


@pytest.fixture()
def appliance(mocker):
    mocker.patch("paramiko.SSHClient")
    appl = Appliance("10.1.1.1", "test", "test", 22)
    yield appl


@pytest.fixture()
def dnac(mocker):
    mocker.patch("paramiko.SSHClient")
    dnac = DNAC("10.1.1.1", "test", "test", 22)
    yield dnac


@pytest.fixture()
def ise(mocker):
    mocker.patch("paramiko.SSHClient")
    ise = ISE("10.1.1.1", "test", "test", 22)
    yield ise


# Test Appliance


def test_appliance_connect(mocker, appliance):
    mocker.patch.object(Appliance, "_connect_ssh")
    r = appliance.connect()
    Appliance._connect_ssh.assert_called_once()
    assert r
    assert appliance.connected


def test_appliance_disconnect(mocker, appliance):
    appliance.connect()
    mocker.patch.object(appliance, "_disconnect")
    appliance._disconnect.return_value = False
    r = appliance.disconnect()
    appliance._disconnect.assert_called_once()
    assert not r


def test_appliance__disconnect(mocker, appliance):
    appliance.connect()
    mocker.patch.object(appliance, "_ssh")
    mocker.patch.object(appliance, "_do_before_disconnect")
    mocker.patch.object(appliance, "_do_after_disconnect")
    r = appliance._disconnect()
    appliance._ssh.close.assert_called_once()
    appliance._do_before_disconnect.assert_called_once()
    appliance._do_after_disconnect.assert_called_once()
    assert not r


def test_appliance__connect_ssh(mocker, appliance):
    mocker.patch.object(appliance, "_ssh")
    r = appliance._connect_ssh()
    appliance._ssh.connect.assert_called_once_with("10.1.1.1", 22, "test", "test")
    appliance._ssh.invoke_shell.assert_called_once()
    assert r


def test_appliance__send_command(mocker, appliance):
    cmd = "test"
    cmd_nl = f"{cmd}\n"
    mocker.patch.object(appliance, "_shell")
    mocker.patch.object(appliance, "_read_shell")
    appliance._shell.send.return_value = len(cmd_nl.encode("utf-8"))
    appliance._read_shell.return_value = cmd
    r = appliance._send_command(cmd)
    appliance._shell.send.assert_called_once_with(cmd_nl)
    appliance._read_shell.assert_called_once()
    assert r == cmd


def test_appliance__read_shell_recv_ready(mocker, appliance):
    data = "test"
    mocker.patch.object(appliance, "_shell")
    appliance._shell.recv_ready.return_value = True
    appliance._shell.recv.return_value = data.encode("utf-8")
    r = appliance._read_shell(wait=1)
    appliance._shell.recv_ready.assert_called_once()
    assert r == data


# Test DNAC


def test_dnac__handle_kong_prompt(mocker, dnac):
    dummy_usr_prompt = " [administration] username "
    dummy_pwd_prompt = " [administration] password "
    mocker.patch.object(dnac, "_send_command")
    dnac._send_command.return_value = dummy_pwd_prompt
    r = dnac._handle_kong_prompt(dummy_usr_prompt)
    dnac._send_command.assert_called_with("test")
    dnac._send_command.assert_called_with(dnac.password)
    assert r == dummy_pwd_prompt


def test_dnac__parse_maglev_restore_history(dnac):
    with open("mock_data/dnac_maglev_restore_history") as stream:
        data = stream.read()
    r = dnac._parse_maglev_restore_history(data, dnac._default_result)
    assert "ee84abae-a11b-45c6-94c3-d578cfe888f6" == r["restore_id"]


def test_dnac_get_status(mocker, dnac):
    dummy_resp = 'test'
    mocker.patch.object(dnac, "_send_command")
    mocker.patch.object(dnac, "_handle_kong_prompt")
    mocker.patch.object(dnac, "_parse_maglev_restore_history")
    dnac._send_command.return_value = dummy_resp
    dnac._handle_kong_prompt.return_value = dummy_resp
    dnac._parse_maglev_restore_history.return_value = dummy_resp
    dnac.get_status()
    dnac._send_command.assert_called_once_with(dnac._status_cmd)
    dnac._handle_kong_prompt.assert_called_once_with(dummy_resp)
    dnac._parse_maglev_restore_history.assert_called_once_with(dummy_resp, dnac._default_result)


# Test ISE


def test_ise__parse_show_restore_history(ise):
    with open("mock_data/ise_show_restore_history") as stream:
        data = stream.read()
    r = ise._parse_show_restore_history(data)
    assert "ise-with-users-ready4DNACb-CFG10-220325-1518.tar.gpg" == r["restore_file"]


def test_ise___do_after_connect(mocker, ise):
    mocker.patch.object(ise, "_handle_session_prompt")
    mocker.patch.object(ise, "_send_command")
    ise._do_after_connect()
    ise._handle_session_prompt.assert_called_once()
    ise._send_command.assert_called_once_with(ise._term_len_cmd)


def test_ise__handle_session_prompt(mocker, ise):
    mocker.patch.object(ise, "_read_shell")
    mocker.patch.object(ise, "_send_command")
    ise._read_shell.return_value = " press <Enter> to start a new one: "
    ise._handle_session_prompt()
    ise._read_shell.assert_called_once()
    ise._send_command.assert_called_once_with("")


def test_ise_get_status(mocker, ise):
    dummy_resp = "test"
    mocker.patch.object(ise, "_send_command")
    mocker.patch.object(ise, "_parse_show_restore_history")
    ise._send_command.return_value = dummy_resp
    ise._parse_show_restore_history.return_value = dummy_resp
    r = ise.get_status()
    assert r == dummy_resp
    ise._send_command.assert_called_once_with(ise._status_cmd)
    ise._parse_show_restore_history.assert_called_once_with(dummy_resp)
