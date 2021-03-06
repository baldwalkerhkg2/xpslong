import crcmod
from selfdrive.car.hyundai.values import CAR, CHECKSUM

hyundai_checksum = crcmod.mkCrcFun(0x11D, initCrc=0xFD, rev=False, xorOut=0xdf)


def create_lkas11(packer, frame, car_fingerprint, apply_steer, steer_req,
                  lkas11, sys_warning, sys_state, enabled,
                  left_lane, right_lane,
                  left_lane_depart, right_lane_depart, lfa_available, bus):
  values = lkas11
  values["CF_Lkas_LdwsSysState"] = 3 if steer_req else sys_state
  values["CF_Lkas_SysWarning"] = sys_warning
  values["CF_Lkas_LdwsLHWarning"] = left_lane_depart
  values["CF_Lkas_LdwsRHWarning"] = right_lane_depart
  values["CR_Lkas_StrToqReq"] = apply_steer
  values["CF_Lkas_ActToi"] = steer_req
  values["CF_Lkas_ToiFlt"] = 0
  values["CF_Lkas_MsgCount"] = frame % 0x10
  values["CF_Lkas_Chksum"] = 0

  if lfa_available:
    values["CF_Lkas_LdwsActivemode"] = int(left_lane) + (int(right_lane) << 1)
    values["CF_Lkas_LdwsOpt_USM"] = 2

    # FcwOpt_USM 5 = Orange blinking car + lanes
    # FcwOpt_USM 4 = Orange car + lanes
    # FcwOpt_USM 3 = Green blinking car + lanes
    # FcwOpt_USM 2 = Green car + lanes
    # FcwOpt_USM 1 = White car + lanes
    # FcwOpt_USM 0 = No car + lanes
    values["CF_Lkas_FcwOpt_USM"] = 2 if enabled else 1

    # SysWarning 4 = keep hands on wheel
    # SysWarning 5 = keep hands on wheel (red)
    # SysWarning 6 = keep hands on wheel (red) + beep
    # Note: the warning is hidden while the blinkers are on
    values["CF_Lkas_SysWarning"] = 4 if sys_warning else 0

  elif car_fingerprint == CAR.HYUNDAI_GENESIS:
    # This field is actually LdwsActivemode
    # Genesis and Optima fault when forwarding while engaged
    values["CF_Lkas_LdwsActivemode"] = 2
  elif car_fingerprint == CAR.KIA_OPTIMA:
    values["CF_Lkas_LdwsActivemode"] = 0

  dat = packer.make_can_msg("LKAS11", 0, values)[2]

  if car_fingerprint in CHECKSUM["crc8"]:
    # CRC Checksum as seen on 2019 Hyundai Santa Fe
    dat = dat[:6] + dat[7:8]
    checksum = hyundai_checksum(dat)
  elif car_fingerprint in CHECKSUM["6B"]:
    # Checksum of first 6 Bytes, as seen on 2018 Kia Sorento
    checksum = sum(dat[:6]) % 256
  else:
    # Checksum of first 6 Bytes and last Byte as seen on 2018 Kia Stinger
    checksum = (sum(dat[:6]) + dat[7]) % 256

  values["CF_Lkas_Chksum"] = checksum

  return packer.make_can_msg("LKAS11", bus, values)


def create_clu11(packer, bus, clu11, button, speed, cnt):
  values = clu11

  if bus != 1:
    values["CF_Clu_CruiseSwState"] = button
    values["CF_Clu_Vanz"] = speed
  else:
    values["CF_Clu_Vanz"] = speed
  values["CF_Clu_AliveCnt1"] = cnt
  return packer.make_can_msg("CLU11", bus, values)

def create_lfa_mfa(packer, frame, enabled):
  values = {
    "ACTIVE": enabled,
  }

  # ACTIVE 1 = Green steering wheel icon

  # LFA_USM 2 & 3 = LFA cancelled, fast loud beeping
  # LFA_USM 0 & 1 = No mesage

  # LFA_SysWarning 1 = "Switching to HDA", short beep
  # LFA_SysWarning 2 = "Switching to Smart Cruise control", short beep
  # LFA_SysWarning 3 =  LFA error

  # ACTIVE2: nothing
  # HDA_USM: nothing

  return packer.make_can_msg("LFAHDA_MFC", 0, values)

def create_scc11(packer, enabled, set_speed, lead_visible, gapsetting, standstill, scc11, usestockscc, nosccradar, frame):
  values = scc11

  if not usestockscc:
    if enabled:
      values["VSetDis"] = set_speed
    if standstill:
      values["SCCInfoDisplay"] = 0
    values["DriverAlertDisplay"] = 0
    values["TauGapSet"] = gapsetting
    values["ObjValid"] = lead_visible
    values["ACC_ObjStatus"] = lead_visible

    if nosccradar:
      values["MainMode_ACC"] = 1
      values["AliveCounterACC"] = frame // 2 % 0x10
  elif nosccradar:
    values["AliveCounterACC"] = frame // 2 % 0x10

  return packer.make_can_msg("SCC11", 0, values)

def create_scc12(packer, apply_accel, enabled, standstill, gaspressed, brakepressed, cruise_on, aebcmdact, scc12,
                 usestockscc, nosccradar, cnt):
  values = scc12

  if not usestockscc and not aebcmdact:
    if enabled and cruise_on and not brakepressed:
      values["ACCMode"] = 2 if gaspressed else 1
      if apply_accel < -0.5:
        values["StopReq"] = standstill
      values["aReqRaw"] = apply_accel
      values["aReqValue"] = apply_accel
    else:
      values["ACCMode"] = 0
      values["aReqRaw"] = 0
      values["aReqValue"] = 0

    if nosccradar:
      values["CR_VSM_Alive"] = cnt
      values["ACCMode"] = 1 if enabled else 0

    values["CR_VSM_ChkSum"] = 0
    dat = packer.make_can_msg("SCC12", 0, values)[2]
    values["CR_VSM_ChkSum"] = 16 - sum([sum(divmod(i, 16)) for i in dat]) % 16
  elif nosccradar:
    values["CR_VSM_Alive"] = cnt
    values["CR_VSM_ChkSum"] = 0
    dat = packer.make_can_msg("SCC12", 0, values)[2]
    values["CR_VSM_ChkSum"] = 16 - sum([sum(divmod(i, 16)) for i in dat]) % 16

  return packer.make_can_msg("SCC12", 0, values)

def create_scc13(packer, scc13):
  values = scc13
  return packer.make_can_msg("SCC13", 0, values)

def create_scc14(packer, enabled, usestockscc, aebcmdact, scc14):
  values = scc14
  if not usestockscc and not aebcmdact:
    if enabled:
      values["JerkUpperLimit"] = 3.2
      values["JerkLowerLimit"] = 0.1
      values["SCCMode"] = 1
      values["ComfortBandUpper"] = 0.24
      values["ComfortBandLower"] = 0.24

  return packer.make_can_msg("SCC14", 0, values)

