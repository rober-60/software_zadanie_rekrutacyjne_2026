import time
from communication_library.communication_manager import CommunicationManager, TransportType
from communication_library.tcp_transport import TcpSettings

from core import state, servo, relay, abort, wait_for_telemetry

def run_mission():
    cm = CommunicationManager() # Class responsible for communication handling
    cm.change_transport_type(TransportType.TCP)
    cm.connect(TcpSettings("127.0.0.1", 3000))
    state.status = "Połączono z symulacją"
    state.is_aborted = False

    state.status = "Tankowanie utleniacza"
    servo(cm,0,1) #otwieramy utleniacz
    while state.sensors["ox"]<99:
        wait_for_telemetry(cm)
    servo(cm,100,1)

    if state.sensors["ox"] < 90:
        abort(cm, "Brak wymaganego utleniacza przed tankowaniem paliwa!")
        return

    state.status = "Tankowanie paliwa"
    servo(cm,0,0) #paliwo
    while state.sensors["fuel"]<99:
        wait_for_telemetry(cm)
    servo(cm,100,0)

    state.status = "Podgrzewanie utleniacza"
    relay(cm,True,0)
    while state.sensors["press"]<56:
        wait_for_telemetry(cm)
        if state.sensors["press"] > 68.0:
            abort(cm, f"Nadciśnienie w zbiorniku utleniacza ({state.sensors['press']:.1f} bar > 68 bar)!")
            return
    relay(cm,False,0)


    for t in range(5,0,-1):
        state.status = f"{t}"
        time.sleep(1)

    servo(cm,0,3) # oxidizer
    servo(cm,0,2)#paliwo
    time.sleep(0.1)
    relay(cm,True,1)#igniter

    state.status = "STARTUJEMY!!!!"

    time.sleep(2)
    relay(cm,False,1)
    state.status = "Jestesmy w powietrzu"

    max_h = 0
    last_t = time.time()
    flight_start_time = last_t
    last_h= 0
    while True:
        wait_for_telemetry(cm)
        curr_h = state.sensors["height"]
        now = time.time()

        state.time_log.append(f"{now - flight_start_time:.1f}")
        state.height_log.append(curr_h)

        if state.sensors["height"] > max_h:
            max_h = state.sensors["height"]

        if max_h > 20  and state.sensors["fuel"] < 0.5 and state.sensors["ox"] <0.5 and curr_h < (max_h - 1.0):
            state.status = f"Osiagnelismy apogeum na wysokosci: {max_h:.2f}m"
            relay(cm,True,2)
            break

    state.status = "Opadanie"
    no_change = 0
    while True:
        last_h = state.sensors["height"]
        wait_for_telemetry(cm)
        curr_h = state.sensors["height"]
        now = time.time()
        t_sec = f"{now - flight_start_time:.1f}"
        if not state.time_log or t_sec != state.time_log[-1]:
            state.time_log.append(t_sec)
            state.height_log.append(round(curr_h, 1))

        if curr_h <= 1.5:
            break
        if curr_h == last_h:
            no_change +=1
            if no_change >30:
                break
        else:
            no_change = 0

    state.sensors["height"] = 0.0
    state.time_log.append(f"{time.time() - flight_start_time:.1f}")
    state.height_log.append(0.0)

    state.status = "Rakieta WYLĄDOWALA Z SUKCESEM"
    state.is_landed = True