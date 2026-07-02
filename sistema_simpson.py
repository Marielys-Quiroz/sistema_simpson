from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from nicegui import app, ui
import sympy as sp
import math
import matplotlib
matplotlib.use('Agg')  
import matplotlib.pyplot as plt
import numpy as np
import io
import base64
import os


class DataSimpson(BaseModel):
    funcion: str
    a: float
    b: float
    n: int

def regla_simpson_13_detallado(f_str: str, a: float, b: float, n: int):
    if n % 2 != 0:
        raise ValueError("El número de subintervalos (n) debe ser par.")
    
    x = sp.symbols('x')
    try:
        f_str = f_str.replace('^', '**')
        expr = sp.sympify(f_str)
    except Exception:
        raise ValueError("La función ingresada no es válida. Revisa los asteriscos.")
    
    f = sp.lambdify(x, expr, modules=['math', {'sin': math.sin, 'cos': math.cos, 'exp': math.exp, 'log': math.log, 'sqrt': math.sqrt}])
    
    h = (b - a) / n
    pasos = []
    valores_f = []
    
    for i in range(n + 1):
        xi = a + i * h
        f_xi = f(xi)
        valores_f.append(f_xi)
        pasos.append({
            "indice": i,
            "xi": round(xi, 4),
            "f_xi": round(f_xi, 6)
        })
    
    suma = valores_f[0] + valores_f[-1]
    for i in range(1, n):
        if i % 2 == 0:
            suma += 2 * valores_f[i]
        else:
            suma += 4 * valores_f[i]
            
    resultado = (h / 3) * suma
    
    partes_sus = []
    for i in range(n + 1):
        val_redondeado = round(pasos[i]['f_xi'], 6)
        if i == 0 or i == n:
            partes_sus.append(f"{val_redondeado}")
        elif i % 2 != 0:
            partes_sus.append(f"4*({val_redondeado})")
        else:
            partes_sus.append(f"2*({val_redondeado})")
    
    sustitucion = f"I = ({round(h, 4)} / 3) * [" + " + ".join(partes_sus) + "]"

    # Gráfica Matplotlib
    plt.figure(figsize=(7.5, 4))
    x_vals = np.linspace(a - 0.5, b + 0.5, 200)
    y_vals = []
    for xv in x_vals:
        try: y_vals.append(f(xv))
        except: y_vals.append(0)
    plt.plot(x_vals, y_vals, color='#1e3a8a', label='f(x)', linewidth=2)
    
    xi_array = [p['xi'] for p in pasos]
    f_xi_array = [p['f_xi'] for p in pasos]
    plt.bar(xi_array, f_xi_array, width=0.02, color='#d90429', alpha=0.5, label='Puntos x_i')
    plt.scatter(xi_array, f_xi_array, color='#d90429', zorder=5)
    plt.fill_between(xi_array, f_xi_array, color='#bbf7d0', alpha=0.4, label='Área aprox.')
    
    plt.title('Representación geométrica (Simpson 1/3)', fontsize=12, fontweight='bold')
    plt.xlabel('x')
    plt.ylabel('f(x)')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150)
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()

    return {
        "h": round(h, 4),
        "pasos_tabla": pasos,
        "sustitucion_formula": sustitucion,
        "resultado": round(resultado, 6),
        "grafica_base64": f"data:image/png;base64,{img_base64}"
    }


app.add_static_files('/static', 'static')

def init_frontend():
    ui.page_title("Regla de Simpson - Dashboard")
    
    ui.add_head_html('''
        <style>
            body { 
                background-color: #010206; /* Fondo base negro absoluto profundo */
                color: #e0e1dd; 
                font-family: 'Inter', sans-serif;
                position: relative;
                overflow-x: hidden;
                font-size: 19px; 
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                padding: 20px 0;
            }
            
            /* Símbolos de fondo con opacidad calibrada (notables pero discretos) */
            .animated-bg {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-image: url('/static/math.png');
                background-size: 45%; 
                background-repeat: repeat;
                opacity: 0.03; 
                z-index: -1;
                pointer-events: none;
                animation: moveBackground 85s linear infinite;
            }
            @keyframes moveBackground {
                from { background-position: 0 0; }
                to { background-position: 100% 100%; }
            }
            
            /* TARJETA CONTENEDORA GENERAL */
            .main-container {
                background-color: rgba(3, 7, 18, 0) !important; 
                backdrop-filter: blur(3px) saturate(40%); 
                border: 2px solid rgba(217, 4, 41, 0.7) !important;
                box-shadow: 0 0 40px rgba(217, 4, 41, 0.18) !important;
                border-radius: 16px !important;
                width: 98% !important;        
                max-width: 1650px !important;   
                padding: 28px !important;
                min-height: 80vh !important;
            }
            
            /* TARJETAS INTERNAS TRANSPARENTES */
            .inner-card { 
                background-color: rgba(6, 11, 23, 0.3) !important; /* Transparente */
                backdrop-filter: blur(1px); 
                border: 1px solid rgba(217, 4, 41, 0.3) !important; 
                color: #e0e1dd !important; 
                border-radius: 12px !important;
            }
            
            /* Recuadro punteado del estado inicial */
            .placeholder-container {
                border: 2px dashed rgba(217, 4, 41, 0.3) !important;
                border-radius: 12px;
                background-color: rgba(6, 12, 26, 0.15);
                height: 540px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                width: 100%;
            }
            
            /* Ajuste de fuentes internas de los inputs */
            .q-field__native, .q-field__prefix, .q-field__suffix, .q-field__input { 
                color: #ffffff !important; 
                font-size: 20px !important; 
            }
            .q-field__label { 
                color: #94a3b8 !important; 
                font-size: 18px !important; 
            }
            
            code, pre, .q-markdown pre, .q-markdown code {
                background-color: rgba(2, 4, 8, 0.75) !important;
                color: #ffffff !important;
                font-family: 'Fira Code', monospace !important;
                font-size: 20px !important; 
                border: 3px solid rgba(217, 4, 41, 0.06) !important;
                padding: 20px !important;
                display: block;
                border-radius: 8px;
                outline: none !important;
                box-shadow: none !important;
            }
            
            /* Tablas en entornos traslúcidos */
            .q-table__card {
                background-color: transparent !important;
                border: none !important;
                box-shadow: none !important;
            }
            .q-table th {
                color: rgba(217, 4, 41, 1) !important;
                font-weight: 700 !important;
                font-size: 19px !important; 
                text-transform: uppercase;
                letter-spacing: 0.8px;
                border-bottom: 2px solid rgba(217, 4, 41, 0.35) !important;
            }
            .q-table td {
                color: #ffffff !important;
                font-size: 18px !important; 
                border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
                padding: 14px 18px !important;
            }
            .q-table tr:hover {
                background-color: rgba(217, 4, 41, 0.06) !important;
            }
        </style>
    ''')
    
    ui.element('div').classes('animated-bg')
    
    with ui.card().classes('main-container gap-4'):
        
        # Banner Superior con título en 14px como se especificó
        with ui.row().classes('w-full justify-between items-center q-pa-md border rounded').style('background-color: rgba(4, 8, 16, 0.45); border-color: rgba(217, 4, 41, 0.4); border-radius: 12px; backdrop-filter: blur(4px);'):
            with ui.row().classes('items-center gap-4'):
                ui.image('/static/logo.png').style('width: 55px; height: 55px;')
                with ui.column().classes('gap-0'):
                    ui.label('Métodos Numéricos').classes('font-bold text-white').style('font-size: 19px;')
                    ui.label('Universidad de Panamá · Ing. Informática').classes('text-subtitle1 text-grey-4')
            with ui.row().classes('items-center gap-2'):
                ui.badge('', color='red').style('background-color: #d90429; box-shadow: 0 0 6px #d90429;')
                ui.label('Sistema Activo').classes('text-h8 text-red-3 font-bold')

        # Distribución de Columnas de Ancho Largo
        with ui.row().classes('w-full no-wrap gap-6 items-start q-mt-sm'):
            
            # Formulario Izquierdo (25%)
            with ui.card().classes('w-[25%] q-pa-md inner-card'):
                ui.label('F(X) / PARÁMETROS').classes('text-h5 font-bold text-white q-mb-sm').style('letter-spacing: 1px;')
                
                funcion_input = ui.input(
                    label='Función f(x)', 
                    value='0.5*x**3+2', 
                    placeholder='Ej: 0.5 * x**2'
                ).props('dark outlined').classes('w-full q-mb-sm')
                
                with ui.row().classes('w-full gap-3 no-wrap q-mb-sm'):
                    a_input = ui.number(label='Límite inf. (a)', value=1.0).props('dark outlined').classes('w-1/2')
                    b_input = ui.number(label='Límite sup. (b)', value=2.0).props('dark outlined').classes('w-1/2')
                    
                n_input = ui.number(label='Subintervalos (n - Par)', value=2, format='%d').props('dark outlined').classes('w-full q-mb-md')
                
                # Botón de ejecución más pequeño usando text-subtitle1 y padding normal (q-py-sm)
                ui.button('Ejecutar Simpson', on_click=lambda: procesar_calculo()).classes('w-full text-white font-bold q-py-sm text-subtitle1').style('background-color: #d90429 !important; box-shadow: 0 0 12px rgba(217,4,41,0.35); border-radius: 8px;')
                
            # Resultados Derechos (75%)
            with ui.card().classes('w-[75%] q-pa-md inner-card max-h-[750px] overflow-y-auto'):
                ui.label('Desarrollo Matemático y Visualización').classes('text-h5 font-bold text-white q-mb-sm')
                desarrollo_container = ui.column().classes('w-full gap-5')
                
                # Estado inicial limpio
                with desarrollo_container:
                    with ui.element('div').classes('placeholder-container gap-3'):
                        ui.icon('table_view', size='64px', color='red-4').style('color: rgba(217, 4, 41, 0.5);')
                        ui.label('Ingrese los datos de la función y presione calcular para ver los resultados.').classes('text-h6 text-grey-4 text-center px-4')

        def procesar_calculo():
            desarrollo_container.clear()
            
            if not funcion_input.value:
                ui.notify('Por favor, ingresa una función', type='warning')
                return
            if int(n_input.value) % 2 != 0:
                ui.notify('¡El número de intervalos (n) debe ser par!', type='negative')
                return
                
            try:
                data = regla_simpson_13_detallado(
                    funcion_input.value, 
                    float(a_input.value), 
                    float(b_input.value), 
                    int(n_input.value)
                )
                
                with desarrollo_container:
                    with ui.row().classes('w-full q-pa-md rounded items-center gap-2').style('background-color: rgba(217,4,41,0.08); border: 1px solid rgba(217,4,41,0.3);'):
                        ui.icon('check_circle', color='white', size='md')
                        ui.label('Cálculo finalizado con éxito').classes('text-h6 font-bold text-white')

                    with ui.row().classes('w-full gap-4 no-wrap q-mt-sm'):
                        with ui.card().classes('w-1/2 q-pa-md inner-card').style('border-color: rgba(217,4,41,0.25) !important;'):
                            ui.label('TAMAÑO DEL PASO (h)').classes('text-subtitle1 text-white-4')
                            ui.label(str(data['h'])).classes('text-h5 font-bold text-white')
                        with ui.card().classes('w-1/2 q-pa-md inner-card').style('border-color: rgba(217,4,41,0.25) !important;'):
                            ui.label('RESULTADO INTEGRAL').classes('text-subtitle1 text-white-4')
                            ui.label(str(data['resultado'])).classes('text-h5 font-bold text-white')

                    # Cuadro adaptado de la "imagen.png"
                    texto_resumen = (
                        f"Integración completada exitosamente usando {n_input.value} subintervalos. "
                        f"El valor aproximado del área bajo la curva f(x) = {funcion_input.value} "
                        f"desde x = {a_input.value} hasta x = {b_input.value} es ≈ {data['resultado']}. "
                        f"El método dividió el dominio en segmentos equidistantes con un ancho de paso h = {data['h']}."
                    )
                    
                    with ui.row().classes('w-full justify-between items-center q-pa-md rounded').style(
                        'background-color: rgba(217, 4, 41, 0.05); '
                        'border: 1px solid rgba(217, 4, 41, 0.4); '
                        'border-radius: 8px;'
                    ):
                        with ui.row().classes('items-center gap-3 w-[85%]'):
                            ui.icon('check_box', color='red-5', size='md')
                            ui.label(texto_resumen).classes('text-subtitle3 text-white leading-relaxed')
                        ui.button('Copiar', on_click=lambda: ui.clipboard.write(texto_resumen)).classes('text-white font-bold q-px-md').style('background-color: rgba(217, 4, 41, 0.25) !important; border: 1px solid rgba(217, 4, 41, 0.5); border-radius: 6px;')

                    ui.label('Valores de las Variables (Tabla xi)').classes('text-h6 font-bold text-white-4 q-mt-md')
                    columnas = [
                        {'name': 'indice', 'label': 'i', 'field': 'indice', 'align': 'center'},
                        {'name': 'xi', 'label': 'x_i', 'field': 'xi', 'align': 'center'},
                        {'name': 'f_xi', 'label': 'f(x_i)', 'field': 'f_xi', 'align': 'center'}
                    ]
                    ui.table(columns=columnas, rows=data['pasos_tabla'], row_key='indice').props('dark flat').classes('w-full')
                    
                    with ui.row().classes('w-full gap-6 items-start q-mt-md no-wrap'):
                        with ui.column().classes('w-1/2 gap-2'):
                            ui.label('Sustitución Completa (Resultado)').classes('text-h6 font-bold text-white-4')
                            ui.code(data['sustitucion_formula']).classes('w-full overflow-x-auto')
                        
                        with ui.column().classes('w-1/2 gap-2 items-center'):
                            ui.label('Historial Visual (Área Geométrica)').classes('text-h6 font-bold text-grey-3 align-start w-full')
                            ui.image(data['grafica_base64']).classes('w-full border rounded shadow-md').style('border-color: rgba(217,4,41,0.25); max-width: 480px; background-color: rgba(4,8,16,0.2);')
                    
                ui.notify('Gráfica y desarrollo generados con éxito', type='positive')
            except Exception as e:
                ui.notify(f'Error: {str(e)}', type='negative')

if __name__ in {"__main__", "docker"}:
    init_frontend()
    ui.run(host='0.0.0.0', port=8080, title="Simpson Dashboard", reload=False)