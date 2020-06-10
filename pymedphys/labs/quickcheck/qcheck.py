# -*- coding: utf-8 -*-
# Copyright (C) 2020 Rafael Ayala

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import codecs
import datetime
import re
import socket

from pymedphys._imports import numpy as np
from pymedphys._imports import pandas as pd
from pymedphys._imports import tqdm


class QuickCheck:
    def __init__(self, ip):
        self.ip = ip
        self.port = 8123
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
        self.sock.settimeout(3)
        self.MSG = b""
        self.raw_MSG = ""
        self.measurements = pd.DataFrame()
        self.data = []
        self.raw_data = ""
        self.connected = False

    def connect(self):
        print("UDP target IP:", self.ip)
        print("UDP target port:", self.port)
        self.send_quickcheck("SER")
        if "SER" in self.data:
            self.connected = True
            print("Connected to Quickcheck")
            print(self.data)

    def close(self):
        self.sock.close()
        del self.sock

    def prepare_qcheck(self):
        self.MSG = (
            self.raw_MSG.encode()
            + codecs.decode("0d", "hex")
            + codecs.decode("0a", "hex")
        )

    def send_quickcheck(self, MESSAGE):
        self.raw_MSG = MESSAGE
        self.prepare_qcheck()
        max_retries = 3
        n_retry = 0

        while True:
            try:
                self.sock.sendto(self.MSG, (self.ip, self.port))
                self.raw_data, _ = self.sock.recvfrom(4096)
                data = self.raw_data.decode(encoding="utf-8")
                self.data = data.strip("\r\n")
                break
            except socket.timeout:
                if n_retry == max_retries:
                    print(
                        """
                          Connection Error  - Reached max retries
                          Quickcheck device unreachable, please check your settings"""
                    )
                    self.data = []
                    break
                else:
                    print("Connection Timeout")
                    n_retry += 1
                    print("Retrying connection {}/{}".format(n_retry, max_retries))
                    continue

    def parse_measurements(self):
        data_split = self.data.split(";")
        m = {}  # Dictionary with measurements
        if data_split[0] == "MEASGET":
            #  MD section:__________________________________________________________
            MD = re.findall("MD=\[(.*?)\]", self.data)[0]
            m["MD_ID"] = np.int(re.findall("ID=(.*?);", MD)[0])
            meas_date = re.findall("Date=(.*?);", MD)[0]
            m["MD_Date"] = datetime.datetime.strptime(meas_date, "%Y-%m-%d").date()
            meas_time = re.findall("Time=(.*?)$", MD)[0]
            m["MD_Time"] = datetime.datetime.strptime(meas_time, "%H:%M:%S").time()
            m["MD_DateTime"] = datetime.datetime.combine(m["MD_Date"], m["MD_Time"])
            #  MV section:__________________________________________________________
            str_val = re.findall("MV=\[(.*?)\]", self.data)[0]
            m["MV_CAX"] = np.float(re.findall("CAX=(.*?);", str_val)[0])
            m["MV_G10"] = np.float(re.findall("G10=(.*?);", str_val)[0])
            m["MV_L10"] = np.float(re.findall("L10=(.*?);", str_val)[0])
            m["MV_T10"] = np.float(re.findall("T10=(.*?);", str_val)[0])
            m["MV_R10"] = np.float(re.findall("R10=(.*?);", str_val)[0])
            m["MV_G20"] = np.float(re.findall("G20=(.*?);", str_val)[0])
            m["MV_L20"] = np.float(re.findall("L20=(.*?);", str_val)[0])
            m["MV_T20"] = np.float(re.findall("T20=(.*?);", str_val)[0])
            m["MV_R20"] = np.float(re.findall("R20=(.*?);", str_val)[0])
            m["MV_E1"] = np.float(re.findall("E1=(.*?);", str_val)[0])
            m["MV_E2"] = np.float(re.findall("E2=(.*?);", str_val)[0])
            m["MV_E3"] = np.float(re.findall("E3=(.*?);", str_val)[0])
            m["MV_E4"] = np.float(re.findall("E4=(.*?);", str_val)[0])
            m["MV_Temp"] = np.float(re.findall("Temp=(.*?);", str_val)[0])
            m["MV_Press"] = np.float(re.findall("Press=(.*?);", str_val)[0])
            m["MV_CAXRate"] = np.float(re.findall("CAXRate=(.*?);", str_val)[0])
            m["MV_ExpTime"] = np.float(re.findall("ExpTime=(.*?)$", str_val)[0])

            #  AV section:__________________________________________________________
            AV = re.findall("AV=\[(.*?)\]\]", self.data)[0]
            AV = AV + "]"  # add last character ]
            for s in ("CAX", "FLAT", "SYMGT", "SYMLR", "BQF", "We"):
                str_val = re.findall(s + "=\[(.*?)\]", AV)[0]
                m["AV_" + s + "_Min"] = np.float(re.findall("Min=(.*?);", str_val)[0])
                m["AV_" + s + "_Max"] = np.float(re.findall("Max=(.*?);", str_val)[0])
                m["AV_" + s + "_Target"] = np.float(
                    re.findall("Target=(.*?);", str_val)[0]
                )
                m["AV_" + s + "_Norm"] = np.float(re.findall("Norm=(.*?);", str_val)[0])
                m["AV_" + s + "_Value"] = np.float(
                    re.findall("Value=(.*?);", str_val)[0]
                )
                m["AV_" + s + "_Valid"] = np.int(re.findall("Valid=(.*?)$", str_val)[0])

            #  WORK section:__________________________________________________________
            str_val = re.findall("WORK=\[(.*?)\]", self.data)[0]

            m["WORK_ID"] = np.int(re.findall("ID=(.*?);", str_val)[0])
            m["WORK_Name"] = re.findall("Name=(.*?)$", str_val)[0]

            #  TASK section:__________________________________________________________
            str_val = re.findall("TASK=\[(.*?)\];MV", self.data)[0]
            m["TASK_ID"] = np.int(re.findall("ID=(.*?);", str_val)[0])
            m["TASK_TUnit"] = re.findall("TUnit=(.*?);", str_val)[0]
            m["TASK_En"] = np.int(re.findall("En=(.*?);", str_val)[0])
            m["TASK_Mod"] = re.findall("Mod=(.*?);", str_val)[0]
            m["TASK_Fs"] = re.findall("Fs=(.*?);", str_val)[0]
            m["TASK_SSD"] = np.int(re.findall("SDD=(.*?);", str_val)[0])
            m["TASK_Ga"] = np.int(re.findall("Ga=(.*?);", str_val)[0])
            m["TASK_We"] = np.int(re.findall("We=(.*?);", str_val)[0])
            m["TASK_MU"] = np.int(re.findall("MU=(.*?);", str_val)[0])
            m["TASK_My"] = np.float(re.findall("My=(.*?);", str_val)[0])
            m["TASK_Info"] = re.findall("Info=(.*?)$", str_val)[0]

            str_val = re.findall("Prot=\[(.*?)\];", str_val)[0]
            m["TASK_Prot_Name"] = re.findall("Name=(.*?);", str_val)[0]
            m["TASK_Prot_Flat"] = np.int(re.findall("Flat=(.*?);", str_val)[0])
            m["TASK_Prot_Sym"] = np.int(re.findall("Sym=(.*?)$", str_val)[0])
        elif data_split[0] == "MEASCNT":
            m[data_split[0]] = np.int(data_split[1:][0])
        elif data_split[0] in ("PTW", "SER", "KEY"):
            m[data_split[0]] = data_split[1:]
        return m

    def get_measurements(self):
        self.send_quickcheck("MEASCNT")
        if "MEASCNT" not in self.data:
            self.send_quickcheck("MEASCNT")
        m = self.parse_measurements()
        n_meas = m["MEASCNT"]
        print("Receiving Quickcheck measurements")
        meas_list = []
        for m in tqdm.tqdm(range(n_meas)):
            control = False
            while not control:
                self.send_quickcheck("MEASGET;INDEX-MEAS=" + "%d" % (m,))
                control = self.raw_MSG in self.data

            meas = self.parse_measurements()
            meas_list.append(meas)
        self.measurements = pd.DataFrame(meas_list)
