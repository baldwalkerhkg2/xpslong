#!/usr/bin/env python3
from tqdm import tqdm

from panda.python.uds import NegativeResponseError

from panda import Panda
from panda.python.uds import UdsClient, SESSION_TYPE, CONTROL_TYPE, MESSAGE_TYPE

ADDR=0x7d0

if __name__ == "__main__":
  panda = Panda()
  panda.set_safety_mode(Panda.SAFETY_ALLOUTPUT)
  uds_client = UdsClient(panda, ADDR, bus=0, timeout=1, debug=True)
  uds_client.diagnostic_session_control(SESSION_TYPE.EXTENDED_DIAGNOSTIC)
  uds_client.communication_control(CONTROL_TYPE.DISABLE_RX_DISABLE_TX, MESSAGE_TYPE.NORMAL)

  print("querying addresses ...")
  l = list(range(ADDR))
  with tqdm(total=len(l)) as t:
    for i in l:
      ct = i >> 8
      mt = i & 0xFF
      t.set_description(f"{hex(ct)} - {hex(mt)}")
      try:
        data = uds_client.diagnostic_session_control(ct, mt)
        print(f"\n{ct} - {mt}: success")
      #except NegativeResponseError as e:
      #  if e.message != "COMMUNICATION_CONTROL - sub-function not supported" and e.message != "COMMUNICATION_CONTROL - request out of range":
      #    print(f"\n{ct} - {mt}: {e.message}")
      t.update(1)
