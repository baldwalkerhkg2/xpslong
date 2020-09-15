#!/usr/bin/env python3
import traceback

import cereal.messaging as messaging
from selfdrive.car.isotp_parallel_query import IsoTpParallelQuery
from selfdrive.swaglog import cloudlog

EXT_DIAG_REQUEST = b'\x10\x03'
EXT_DIAG_RESPONSE = b'\x50\x03'
COM_CONT_REQUEST = b'\x28\x83\x03'
TESTER_PRESENT = b'\x02\x3E\x80\x00\x00\x00\x00\x00'
COM_CONT_RESPONSE = b''

def disable_radar(ecu_addr, logcan, sendcan, bus=2, timeout=0.1, retry=5, debug=False):
  print(f"ecu disable {hex(ecu_addr)} ...")
  for i in range(retry):
    try:
      # enter extended diagnostic session
      #query = IsoTpParallelQuery(sendcan, logcan, bus, [ecu_addr], [COM_CONT_REQUEST], [COM_CONT_RESPONSE], debug=debug)
      query = IsoTpParallelQuery(sendcan, logcan, bus, [ecu_addr], [EXT_DIAG_REQUEST], [EXT_DIAG_RESPONSE], debug=debug)
      for ecu_addr, dat in query.get_data(timeout).items():
        print(f"ecu communication control disable tx/rx ...")
        # communication control disable tx and rx
        query = IsoTpParallelQuery(sendcan, logcan, bus, [ecu_addr], [COM_CONT_REQUEST], [COM_CONT_RESPONSE], debug=debug)
        query.get_data(0)
        return True
      print(f"ecu disable retry ({i+1}) ...")
    except Exception:
      cloudlog.warning(f"ecu disable exception: {traceback.format_exc()}")

  return False


if __name__ == "__main__":
  import time
  sendcan = messaging.pub_sock('sendcan')
  logcan = messaging.sub_sock('can')
  time.sleep(1)
  disabled = disable_radar(0x7d0, logcan, sendcan, 2, debug=True)
  print(f"disabled: {disabled}")