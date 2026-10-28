import threading
from nicegui import ui
import autopilot

ui.page_title = "Kontrola Lotu"

with ui.header().classes('items-center justify-between bg-slate-900 text-white px-6 py-3 shadow'):
    ui.label('ROCKET SOFTWARE').classes('text-lg font-bold tracking-wide')
    status_badge = ui.badge(autopilot.state.status, color='red').classes('text-sm font-mono px-3 py-1 font-bold')

with ui.row().classes('w-full p-4 gap-4 no-wrap'):
    with ui.column().classes('w-1/3 gap-3'):
        ui.button('START MISJI', on_click=lambda: threading.Thread(target=autopilot.run_mission, daemon=True).start()) \
            .classes('w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3 text-base shadow-md')

        with ui.card().classes('w-full shadow-sm border p-3'):
            ui.label('Utleniacz').classes('text-xs font-bold text-gray-500')
            ox_bar = ui.linear_progress(value=0.0).classes('h-3')
            ox_label = ui.label('0.0 %').classes('font-mono font-bold text-blue-600 text-right w-full')

            ui.label('Paliwo').classes('text-xs font-bold text-gray-500 mt-2')
            fuel_bar = ui.linear_progress(value=0.0).classes('h-3')
            fuel_label = ui.label('0.0 %').classes('font-mono font-bold text-amber-600 text-right w-full')

        with ui.row().classes('w-full gap-3'):
            with ui.card().classes('flex-1 shadow-sm border p-3'):
                ui.label('Ciśnienie').classes('text-xs font-bold text-gray-500')
                press_label = ui.label('0.0 bar').classes('text-2xl font-mono font-bold text-slate-800')
                thrust_label = ui.label(autopilot.state.status_press).classes('text-xs font-bold text-gray-400')

            with ui.card().classes('flex-1 shadow-sm border p-3'):
                ui.label('Wysokość').classes('text-xs font-bold text-gray-500')
                alt_label = ui.label('0.0 m').classes('text-2xl font-mono font-bold text-slate-800')

    with ui.column().classes('w-2/3'):
        with ui.card().classes('w-full shadow-sm border border-slate-200 p-4 rounded-xl bg-white'):
            with ui.row().classes('w-full justify-between items-center mb-2'):
                ui.label('PROFIL WYSOKOŚCI LOTU').classes('text-sm font-bold text-slate-700 tracking-wide')
                ui.label('Pełny przebieg misji').classes('text-xs text-slate-400 font-mono')

            chart = ui.echart({
                'tooltip': {'trigger': 'axis', 'formatter': 'Czas: {b} s<br/>Wysokość: {c} m'},
                'grid': {'left': '8%', 'right': '4%', 'top': '8%', 'bottom': '12%'},
                'xAxis': {
                    'type': 'category',
                    'data': [],
                    'name': 'Czas [s]',
                    'nameLocation': 'middle',
                    'nameGap': 25,
                    'axisLabel': {'interval': 'auto'},
                    'axisLine': {'lineStyle': {'color': '#94a3b8'}}
                },
                'yAxis': {
                    'type': 'value',
                    'name': 'Wysokość [m]',
                    'splitLine': {'lineStyle': {'type': 'dashed', 'color': '#e2e8f0'}},
                    'axisLine': {'lineStyle': {'color': '#94a3b8'}}
                },
                'series': [{
                    'data': [],
                    'type': 'line',
                    'smooth': True,
                    'symbol': 'none',
                    'lineStyle': {'color': '#e11d48', 'width': 3},
                    'areaStyle': {
                        'color': {
                            'type': 'linear',
                            'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                            'colorStops': [
                                {'offset': 0, 'color': 'rgba(225, 29, 72, 0.35)'},
                                {'offset': 1, 'color': 'rgba(225, 29, 72, 0.0)'}
                            ]
                        }
                    }
                }]
            }).classes('w-full h-96')

notified_landed = False

def refresh_ui():
    global notified_landed
    s = autopilot.state

    status_badge.set_text(s.status)
    if "SUKCESEM" in s.status:
        status_badge.props('color=green')
    elif "powietrzu" in s.status or "Odliczanie" in s.status or "STARTUJEMY!!!!" in s.status:
        status_badge.props('color=orange')

    ox_bar.set_value(s.sensors["ox"] / 100.0)
    ox_label.set_text(f'{s.sensors["ox"]:.1f} %')
    fuel_bar.set_value(s.sensors["fuel"] / 100.0)
    fuel_label.set_text(f'{s.sensors["fuel"]:.1f} %')

    press_label.set_text(f'{s.sensors["press"]:.1f} bar')
    alt_label.set_text(f'{s.sensors["height"]:.1f} m')

    thrust_label.set_text(s.status_press)
    if "100%" in s.status_press:
        thrust_label.classes(replace='text-xs font-bold text-emerald-600')
    elif "50-100%" in s.status_press:
        thrust_label.classes(replace='text-xs font-bold text-amber-500')
    elif "Ryzyko" in s.status_press or "za niskie" in s.status_press:
        thrust_label.classes(replace='text-xs font-bold text-rose-600')
    else:
        thrust_label.classes(replace='text-xs font-bold text-gray-400')

    if s.time_log:
        chart.options['xAxis']['data'] = s.time_log
        chart.options['series'][0]['data'] = s.height_log
        chart.update()

ui.timer(0.2, refresh_ui)

ui.run(port=8080, title="Ground Control", reload=False)