import streamlit as st
import pandas as pd
from datetime import datetime
import os
import io

# --- 1. CONFIGURACIÓN DE ARCHIVOS DE DATOS ---
CLIENTES_FILE = 'clientes.csv'
CITAS_FILE = 'citas.csv'

# Inicializar los archivos de datos si no existen
def inicializar_data(filename, columns):
    if not os.path.exists(filename):
        df = pd.DataFrame(columns=columns)
        df.to_csv(filename, index=False)
    return pd.read_csv(filename)

df_clientes = inicializar_data(CLIENTES_FILE, ['Nombre', 'Empresa', 'Tlf', 'Localidad', 'Zona'])
df_citas = inicializar_data(CITAS_FILE, ['Fecha', 'Nombre', 'Empresa', 'Tlf', 'Localidad', 'Zona', 'Asunto'])


# --- 2. FUNCIÓN PARA GUARDAR DATOS ---
def guardar_cliente(nombre, empresa, tlf, localidad, zona):
    global df_clientes
    # Verificar si el cliente ya existe (por Nombre o Empresa)
    if not ((df_clientes['Nombre'] == nombre) & (df_clientes['Empresa'] == empresa)).any():
        nuevo_cliente = pd.DataFrame([{
            'Nombre': nombre, 
            'Empresa': empresa, 
            'Tlf': tlf, 
            'Localidad': localidad, 
            'Zona': zona
        }])
        df_clientes = pd.concat([df_clientes, nuevo_cliente], ignore_index=True)
        df_clientes.to_csv(CLIENTES_FILE, index=False)
        return True
    return False

def guardar_cita(fecha, nombre, empresa, tlf, localidad, zona, asunto):
    global df_citas
    nueva_cita = pd.DataFrame([{
        'Fecha': fecha.strftime('%Y-%m-%d'),
        'Nombre': nombre,
        'Empresa': empresa,
        'Tlf': tlf,
        'Localidad': localidad,
        'Zona': zona,
        'Asunto': asunto
    }])
    df_citas = pd.concat([df_citas, nueva_cita], ignore_index=True)
    df_citas.to_csv(CITAS_FILE, index=False)


# --- 3. INTERFAZ DE STREAMLIT ---
st.title("📅 Diario de Visitas Comerciales")
st.markdown("---")

# Crea pestañas para organizar la interfaz
tab1, tab2 = st.tabs(["➕ Registrar Visita", "🔍 Consultar y Exportar"])

# ====================================================================
# PESTAÑA 1: REGISTRAR VISITA
# ====================================================================
with tab1:
    st.header("Agendar Nueva Visita")
    
    # Selector de fecha (Calendario)
    fecha_seleccionada = st.date_input("Selecciona la fecha de la visita:", datetime.today())

    # Opción para seleccionar cliente existente o añadir uno nuevo
    opcion_cliente = st.radio("Cliente:", ("Buscar Cliente Existente", "Añadir Nuevo Cliente"))

    # Campos de formulario
    nombre = empresa = tlf = localidad = zona = ""

    if opcion_cliente == "Buscar Cliente Existente":
        if not df_clientes.empty:
            clientes_opciones = df_clientes['Nombre'].unique()
            # Combobox para seleccionar
            nombre_elegido = st.selectbox("Selecciona un Cliente Guardado:", [''] + list(clientes_opciones))

            if nombre_elegido:
                # Cargar los datos del cliente seleccionado
                cliente_data = df_clientes[df_clientes['Nombre'] == nombre_elegido].iloc[0]
                nombre = cliente_data['Nombre']
                empresa = st.text_input("Empresa:", value=cliente_data['Empresa'], key='emp_exist')
                tlf = st.text_input("Teléfono:", value=cliente_data['Tlf'], key='tlf_exist')
                localidad = st.text_input("Localidad:", value=cliente_data['Localidad'], key='loc_exist')
                zona = st.text_input("Zona:", value=cliente_data['Zona'], key='zona_exist')
                st.info(f"Datos de {nombre_elegido} cargados.")
            else:
                st.warning("No hay clientes guardados. Añade uno en la opción 'Añadir Nuevo Cliente'.")
        else:
             st.warning("No hay clientes guardados. Por favor, cambia a 'Añadir Nuevo Cliente'.")

    else: # Añadir Nuevo Cliente
        nombre = st.text_input("Nombre del Contacto:")
        empresa = st.text_input("Empresa:")
        tlf = st.text_input("Teléfono:")
        localidad = st.text_input("Localidad:")
        zona = st.text_input("Zona:")
        
        if nombre and empresa:
             st.success("Este cliente se guardará para futuras citas.")


    # Campo que NO se guarda para reutilizar: Asunto
    asunto = st.text_area("Asunto/Motivo de la Visita (NO se reutiliza):")

    # Botón de registro
    if st.button("Guardar Visita"):
        if nombre and empresa and localidad and asunto:
            # 1. Guardar el cliente (si es nuevo o se modificó el existente)
            guardar_cliente(nombre, empresa, tlf, localidad, zona)
            
            # 2. Guardar la cita con el asunto específico
            guardar_cita(fecha_seleccionada, nombre, empresa, tlf, localidad, zona, asunto)
            
            st.success(f"✅ Visita con {nombre} para el {fecha_seleccionada.strftime('%d/%m/%Y')} registrada con éxito.")
        else:
            st.error("❌ Por favor, completa los campos obligatorios: Nombre, Empresa, Localidad y Asunto.")


# ====================================================================
# PESTAÑA 2: CONSULTAR Y EXPORTAR
# ====================================================================
with tab2:
    st.header("Consultar Historial")

    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        filtro_fecha = st.date_input("Filtrar desde fecha:", datetime.today().replace(day=1))
    with col2:
        filtro_nombre = st.selectbox("Filtrar por Nombre:", ['Todos'] + list(df_citas['Nombre'].unique()))

    # Aplicar Filtros
    df_filtrado = df_citas.copy()
    
    # Filtro por fecha (mayor o igual a la fecha seleccionada)
    df_filtrado['Fecha'] = pd.to_datetime(df_filtrado['Fecha'])
    df_filtrado = df_filtrado[df_filtrado['Fecha'] >= pd.to_datetime(filtro_fecha)]

    # Filtro por nombre
    if filtro_nombre != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Nombre'] == filtro_nombre]

    # Mostrar Resultados
    st.subheader(f"Resultados ({len(df_filtrado)} visitas):")
    
    if df_filtrado.empty:
        st.info("No hay visitas que coincidan con los filtros seleccionados.")
    else:
        # Formatear la columna de fecha para mejor visualización
        df_display = df_filtrado.sort_values(by='Fecha', ascending=False).copy()
        df_display['Fecha'] = df_display['Fecha'].dt.strftime('%d/%m/%Y')
        st.dataframe(df_display, use_container_width=True)

        # Botón de Exportar
        csv = df_display.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Descargar Datos Filtrados (CSV)",
            data=csv,
            file_name='reporte_visitas.csv',
            mime='text/csv',
        )