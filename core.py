from communication_library.communication_manager import CommunicationManager, TransportType
from communication_library.tcp_transport import TcpSettings
from communication_library.frame import Frame
from communication_library import ids
from communication_library.exceptions import TransportTimeoutError, TransportError, UnregisteredCallbackError
import time
import matplotlib.pyplot as plt
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class MissionState:
    sensors: Dict[str, float] = field(default_factory=lambda: {"fuel": 0.0, "ox": 0.0, "press": 0.0, "height": 0.0})
    status: str = "Przygotowanie do startu"
    status_press: str = "Oczekiwanie na grzanie"
    is_landed: bool = False
    is_aborted: bool = False
    time_log: List[str] = field(default_factory=list)
    height_log: List[float] = field(default_factory=list)

state = MissionState()

def servo(cm,position,id):
    servo = Frame(ids.BoardID.ROCKET, 
                           ids.PriorityID.LOW, 
                           ids.ActionID.SERVICE, 
                           ids.BoardID.SOFTWARE, 
                           ids.DeviceID.SERVO, 
                           id, # oxidizer intake 
                           ids.DataTypeID.INT16,
                           ids.OperationID.SERVO.value.POSITION,
                           (position,) # 0 is for open position, 100 is for closed
                           )
    cm.push(servo)
    cm.send()

def relay(cm,state_relay,id):
    if state_relay:
        operation = ids.OperationID.RELAY.value.OPEN
    else:
        operation = ids.OperationID.RELAY.value.CLOSE

    relay_open_frame = Frame(ids.BoardID.ROCKET, 
                           ids.PriorityID.LOW, 
                           ids.ActionID.SERVICE, 
                           ids.BoardID.SOFTWARE, 
                           ids.DeviceID.RELAY, 
                           id, # oxidizer heater
                           ids.DataTypeID.FLOAT,
                           operation,
                           ()
                           )
    cm.push(relay_open_frame) # We need to push the frame onto the send queue
    cm.send() # Send queue first in the send queue

def update_sensors(cm):
    frame = None
    try:
        frame =cm.receive()
    except TransportTimeoutError:
        pass
    except UnregisteredCallbackError as e:
        frame = e.frame
   
    if frame and frame.action == ids.ActionID.FEED and frame.device_type == ids.DeviceID.SENSOR:
        val = float(frame.data) if isinstance(frame.data, (int, float)) else 0.0
        if frame.device_id== 0:
            state.sensors["fuel"] =val
        elif frame.device_id == 1:
            state.sensors["ox"] = val
        elif frame.device_id == 2:
            state.sensors["height"] =val
        elif frame.device_id== 3:
            state.sensors["press"] = val

def abort(cm, reason: str):
    state.is_aborted = True
    state.status = f"ABORT: {reason}"
    print(f"\n[ALARM KRYTYCZNY] {state.status}")

    #Wyłączamy wszystko
    relay(cm, False, 0)
    relay(cm, False, 1)
    servo(cm, 100, 0)
    servo(cm, 100, 1)
    print("[SAFE] Podzespoły zabezpieczone.")

def wait_for_telemetry(cm):
    update_sensors(cm)
    time.sleep(0.05)
