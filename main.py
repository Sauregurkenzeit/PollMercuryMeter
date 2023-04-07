import csv
import serial
from virtual_serial_device import DummySerial
import struct
import time
from flask import Flask, render_template, request, redirect, url_for
import json
import serial.tools.list_ports

app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    config = read_config("config.json")
    results = poll_devices(config)
    return render_template("index.html", results=results)


@app.route("/settings", methods=["GET", "POST"])
def settings():
    config = read_config("config.json")
    all_commands, required_commands = read_commands(config)
    available_com_ports = get_available_com_ports()

    if request.method == "POST":
        action = request.form.get("action")
        if action == "add_device":
            new_device = {
                "com_port": request.form.get("com_port"),
                "serial_number": request.form.get("serial_number")
            }
            config["devices"].append(new_device)
        elif action == "delete_device":
            device_index = int(request.form.get("device_index"))
            config["devices"].pop(device_index)
        elif action == "add_command":
            new_command = int(request.form.get("command"), 16)
            config["commands"].append(new_command)
        elif action == "delete_command":
            command_index = int(request.form.get("command_index"))
            config["commands"].pop(command_index)
        save_config(config)
        return redirect(url_for("settings"))
    return render_template("settings.html", config=config, required_commands=required_commands,
                           all_commands=all_commands, available_com_ports=available_com_ports)


def crc16(data):
    crc = 0xFFFF
    l = len(data)
    i = 0
    while i < l:
        j = 0
        crc = crc ^ data[i]
        while j < 8:
            if (crc & 0x1):
                mask = 0xA001
            else:
                mask = 0x00
            crc = ((crc >> 1) & 0x7FFF) ^ mask
            j += 1
        i += 1
    if crc < 0:
        crc -= 256
    result = data + chr(crc % 256).encode() + chr(crc // 256).encode('latin-1')
    return result


def get_available_com_ports():
    ports = list(serial.tools.list_ports.comports())
    return [port.device for port in ports] + ["Virtual/COM1"]


def save_config(config, file_path="config.json"):
    with open(file_path, "w") as json_file:
        json.dump(config, json_file, indent=4)


def read_config(filename):
    with open(filename, "r") as f:
        config = json.load(f)
    return config


def read_commands(config):
    commands = []
    with open("commands.csv", "r", encoding="utf-8-sig") as f:
        csv_reader = csv.reader(f, delimiter=";")
        for row in csv_reader:
            commands.append({"command": int(row[0], 16), "description": row[1], "handle_function": row[2]})
    selected_commands = [cmd for cmd in commands if cmd["command"] in config["commands"]]
    return commands, selected_commands


def handle_command_27(out):
    # ... (handle the response for command \x27)
    data = ''.join('{:02x}'.format(c) for c in out[5:9])
    result = f"{data}"
    return result


def handle_command_63(out):
    # ... (handle the response for command \x63)
    result = f"Result for command 63: ..."
    return result


def poll_device(ser, sn, command, handle_function):
    chunk = struct.pack('>L', int(sn))
    chunk += command.to_bytes(1, 'big')
    chunk = crc16(chunk)

    # Send data
    ser.write(chunk)
    time.sleep(1)
    out = ser.read_all()
    print(f"Received: {out}")
    # Call the handle function for the command and return the result
    return handle_function(out)


def poll_devices(config):
    _, commands = read_commands(config)
    results = {}

    for device in config["devices"]:
        device_results = {}
        com_port = device["com_port"]
        if not com_port.startswith("Virtual"):
            serial_port = serial.Serial(device["com_port"], 9600, serial.EIGHTBITS, serial.PARITY_NONE,
                                        serial.STOPBITS_ONE)
        else:
            serial_port = DummySerial()

        with serial_port as ser:
            print(f"Connected: {ser.isOpen()}")
            for command_row in commands:
                command = command_row["command"]
                handle_function = globals()[command_row["handle_function"]]
                print(f"Polling device with serial number {device['serial_number']}"
                      f" on port {device['com_port']} using command {command} ({command_row['description']})")
                result = poll_device(ser, device["serial_number"], command, handle_function)
                device_results[command_row['description']] = result

        results[device['serial_number']] = device_results

    return results


def main():
    app.run(host="0.0.0.0", port=5000)


if __name__ == "__main__":
    main()
