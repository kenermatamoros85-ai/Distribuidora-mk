import streamlit as st

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Distribuidora M&K - Ventas",
    page_icon="📦",  # Puedes cambiar este emoji por 🚚, 💰, o 🏭
    layout="wide"
)

import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os
import plotly.express as px

# --- 1. CONFIGURACIÓN INICIAL Y BASE DE DATOS ---
# Inventario: [Costo, Venta, Stock Actual, Stock Mínimo]
if 'inventario' not in st.session_state:
    st.session_state.inventario = {
        "Arroz Especial (Saco 50lb)": [1200.00, 1450.00, 25, 5],
        "Frijol Rojo (Quintal)": [2800.00, 3200.00, 10, 3],
        "Aceite Vegetal (Caja 12L)": [700.00, 850.00, 4, 10],
        "Azúcar (Saco 50kg)": [950.00, 1100.00, 15, 5]
    }

if 'carrito' not in st.session_state:
    st.session_state.carrito = []

PASSWORD_GERENCIA = "MK2026"  # <--- TU CONTRASEÑA

# --- 2. FUNCIONES DE APOYO ---
def registrar_venta_csv(cliente, total_v, total_c, ganancia):
    archivo = "historial_mk.csv"
    nueva_fila = pd.DataFrame([{
        "Fecha": datetime.now().strftime("%d/%m/%Y"),
        "Cliente": cliente,
        "Venta": total_v,
        "Costo": total_c,
        "Ganancia": ganancia
    }])
    if not os.path.exists(archivo):
        nueva_fila.to_csv(archivo, index=False)
    else:
        nueva_fila.to_csv(archivo, mode='a', header=False, index=False)

def generar_pdf(cliente, items):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "DISTRIBUIDORA M&K", ln=True, align='C')
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"Cliente: {cliente} | Fecha: {datetime.now().strftime('%d/%m/%Y')}*, ln=True)
    pdf.ln(10)
    # Tabla simple
    pdf.cell(90, 10, "Producto", 1)
    pdf.cell(30, 10, "Cant.", 1, 0, 'C')
    pdf.cell(60, 10, "Total (C$)", 1, 1, 'C')
    total = 0
    for i in items:
        sub = i['cant'] * i['v']
        total += sub
        pdf.cell(90, 10, i['nombre'], 1)
        pdf.cell(30, 10, str(i['cant']), 1, 0, 'C')
        pdf.cell(60, 10, f"{sub:,.2f}", 1, 1, 'R')
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(120, 10, "TOTAL NETO A PAGAR:", 0)
    pdf.cell(60, 10, f"C$ {total:,.2f}", 0, 1, 'R')
    pdf.output("factura.pdf")
    return "factura.pdf"

# --- 3. INTERFAZ (SIDEBAR) ---
st.sidebar.title("📦 Distribuidora M&K")
opcion = st.sidebar.radio("Navegación", ["Ventas", "Gerencia"])

# --- MÓDULO DE VENTAS ---
if opcion == "Ventas":
    st.header("🛒 Terminal de Ventas")
    
    # Alertas de Stock
    for p, d in st.session_state.inventario.items():
        if d[2] <= d[3]:
            st.error(f"⚠️ ¡REABASTECER! {p} (Quedan {d[2]})")

    cliente_nombre = st.text_input("Nombre del Cliente")
    col1, col2 = st.columns(2)
    with col1:
        prod = st.selectbox("Seleccionar Producto", list(st.session_state.inventario.keys()))
    with col2:
        c_vender = st.number_input("Cantidad", min_value=1, step=1)

    if st.button("➕ Añadir al Carrito"):
        if st.session_state.inventario[prod][2] >= c_vender:
            st.session_state.carrito.append({
                'nombre': prod, 'cant': c_vender, 
                'c': st.session_state.inventario[prod][0], 
                'v': st.session_state.inventario[prod][1]
            })
            st.session_state.inventario[prod][2] -= c_vender # Descontar stock
            st.success("Producto añadido.")
        else:
            st.error("No hay suficiente stock disponible.")

    if st.session_state.carrito:
        st.table(pd.DataFrame(st.session_state.carrito)[['nombre', 'cant', 'v']])
        if st.button("🏁 Finalizar Venta y PDF"):
            t_v = sum(x['cant'] * x['v'] for x in st.session_state.carrito)
            t_c = sum(x['cant'] * x['c'] for x in st.session_state.carrito)
            gan = t_v - t_c
            registrar_venta_csv(cliente_nombre, t_v, t_c, gan)
            path = generar_pdf(cliente_nombre, st.session_state.carrito)
            with open(path, "rb") as f:
                st.download_button("📥 Descargar Factura", f, file_name=f"M&K_{cliente_nombre}.pdf")
            st.session_state.carrito = [] # Limpiar carrito
            st.balloons()

# --- MÓDULO DE GERENCIA ---
elif opcion == "Gerencia":
    st.header("🔐 Panel Administrativo")
    pw = st.text_input("Contraseña de acceso", type="password")
    if pw == PASSWORD_GERENCIA:
        st.success("Acceso autorizado.")
        
        # Gráficas
        if os.path.exists("historial_mk.csv"):
            df = pd.read_csv("historial_mk.csv")
            st.subheader("📊 Ganancias Totales")
            st.metric("Ganancia Neta Acumulada", f"C$ {df['Ganancia'].sum():,.2f}")
            
            fig = px.bar(df, x='Fecha', y='Ganancia', title="Ganancia por Día", color_discrete_sequence=['#2ecc71'])
            st.plotly_chart(fig)
            st.dataframe(df)
        else:
            st.info("No hay ventas registradas todavía.")
    elif pw != "":
        st.error("Clave incorrecta.")