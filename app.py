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
    """Crea un DataFrame si el archivo no existe, o lo carga si ya existe."""
    if not os.path.exists(filename):
        df = pd.DataFrame(columns=columns)
        df.to_csv(filename, index=False)
    # Cargar los datos y forzar las columnas importantes a tipo string
    df = pd.read_csv(filename, dtype=str)
    return df

# Cargar los datos iniciales
df_clientes = inicializar_data(CLIENTES_FILE, ['Nombre', 'Empresa', 'Tlf', 'Localidad', 'Zona'])
df_citas = inicializar_data(CITAS_FILE, ['Fecha', 'Nombre', 'Empresa', 'Tlf', 'Localidad', 'Zona', 'Asunto'])


# --- FUNCIÓN DE LIMPIEZA DE DATOS ---
def limpiar_df(df):
    """Limpia columnas clave para eliminar espacios en blanco."""
    for col in ['Nombre', 'Empresa', 'Localidad', 'Zona']:
        if col in df.columns:
            # Elimina espacios en blanco al inicio/final de las entradas
            df[col] = df[col].str.strip()
    return df

df_clientes = limpiar_df(df_clientes)
df_citas = limpiar_df(df_citas)


# --- 2. FUNCIONES PARA GUARDAR DATOS ---
def guardar_cliente(nombre, empresa, tlf, localidad, zona):
    """Guarda un cliente si no existe (basado en Nombre y Empresa)."""
    # Limpiar entradas antes de guardar
    nombre, empresa, localidad, zona = nombre.strip(), empresa.strip(), localidad.strip(), zona.strip()
    
    global df_clientes
    if not ((df_clientes['Nombre'] == nombre) & (df_clientes['Empresa'] == empresa)).any():
        nuevo_cliente = pd.DataFrame([{
            'Nombre': nombre, 
            'Empresa': empresa, 
            'Tlf': tlf.strip(), 
            'Localidad': localidad, 
            'Zona': zona
        }])
        df_clientes = pd.concat([df_clientes, nuevo_cliente], ignore_index=True)
        df_clientes.to_csv(CLIENTES_FILE, index=False)
        st.session_state.df_clientes = df_clientes
        return True
    return False

def guardar_cita(fecha, nombre, empresa, tlf, localidad, zona, asunto):
    """Guarda una nueva entrada de cita."""
    # Limpiar entradas antes de guardar
    nombre, empresa, localidad, zona, asunto = nombre.strip(), empresa.strip(), localidad.strip(), zona.strip(), asunto.strip()

    global df_citas
    nueva_cita = pd.DataFrame([{
        'Fecha': fecha.strftime('%Y-%m-%d'),
        'Nombre': nombre,
        'Empresa': empresa,
        'Tlf': tlf.strip(),
        'Localidad': localidad,
        'Zona': zona,
        'Asunto': asunto
    }])
    df_citas = pd.concat([df_citas, nueva_cita], ignore_index=True)
    df_citas.to_csv(CITAS_FILE, index=False)
    st.session_state.df_citas = df_citas


# --- 3. INTERFAZ DE STREAMLIT ---
st.title("📅 Diario de Visitas Comerciales")
st.markdown("---")

# Crear pestañas
tab1, tab2 = st.tabs(["➕ Registrar Visita", "🔍 Consultar y Exportar"])

# ====================================================================
# PESTAÑA 1: REGISTRAR VISITA
# ====================================================================
with tab1:
    st.header("Agendar Nueva Visita")
    
    fecha_seleccionada = st.date_input("Selecciona la fecha de la visita:", datetime.today())
    opcion_cliente = st.radio("Cliente:", ("Buscar Cliente Existente", "Añadir Nuevo Cliente"))

    nombre = empresa = tlf = localidad = zona = ""

    if opcion_cliente == "Buscar Cliente Existente":
        if not df_clientes.empty:
            # Usamos el DataFrame limpio para las opciones
            clientes_opciones = df_clientes['Nombre'].dropna().unique()
            nombre_elegido = st.selectbox("Selecciona un Cliente Guardado:", [''] + sorted(list(clientes_opciones)))

            if nombre_elegido:
                cliente_data = df_clientes[df_clientes['Nombre'] == nombre_elegido].iloc[0]
                nombre = cliente_data['Nombre']
                empresa = st.text_input("Empresa:", value=cliente_data['Empresa'], key='emp_exist')
                tlf = st.text_input("Teléfono:", value=cliente_data['Tlf'], key='tlf_exist')
                localidad = st.text_input("Localidad:", value=cliente_data['Localidad'], key='loc_exist')
                zona = st.text_input("Zona:", value=cliente_data['Zona'], key='zona_exist')
                st.info(f"Datos de {nombre_elegido} cargados.")
            else:
                st.warning("Selecciona un cliente o usa 'Añadir Nuevo Cliente'.")
        else:
             st.warning("No hay clientes guardados. Por favor, usa la opción 'Añadir Nuevo Cliente'.")

    else: # Añadir Nuevo Cliente
        nombre = st.text_input("Nombre del Contacto:")
        empresa = st.text_input("Empresa:")
        tlf = st.text_input("Teléfono:")
        localidad = st.text_input("Localidad:")
        zona = st.text_input("Zona:")
        
        if nombre and empresa:
             st.success("Este cliente se guardará para futuras citas.")

    asunto = st.text_area("Asunto/Motivo de la Visita (NO se reutiliza):")

    if st.button("Guardar Visita"):
        if nombre and empresa and localidad and asunto:
            guardar_cliente(nombre, empresa, tlf, localidad, zona)
            guardar_cita(fecha_seleccionada, nombre, empresa, tlf, localidad, zona, asunto)
            st.success(f"✅ Visita con {nombre.strip()} para el {fecha_seleccionada.strftime('%d/%m/%Y')} registrada con éxito.")
        else:
            st.error("❌ Por favor, completa los campos obligatorios: Nombre, Empresa, Localidad y Asunto.")


# ====================================================================
# PESTAÑA 2: CONSULTAR Y EXPORTAR
# ====================================================================
with tab2:
    st.header("Consultar Historial")

    # Usamos el DataFrame de la sesión para reflejar los cambios inmediatos
    df_citas_actual = st.session_state.get('df_citas', df_citas)
    
    # --- FILTROS ---
    # Fila 1 de filtros
    col1, col2 = st.columns(2)
    with col1:
        filtro_fecha = st.date_input("Filtrar desde fecha:", datetime.today().replace(day=1))
    with col2:
        # **FILTRO DE NOMBRE MEJORADO**
        filtro_nombre = st.selectbox("Filtrar por Nombre:", ['Todos'] + sorted(list(df_citas_actual['Nombre'].dropna().unique())))
    
    # Fila 2 de filtros
    col3, col4 = st.columns(2)
    with col3:
        # **FILTRO DE LOCALIDAD MEJORADO**
        filtro_localidad = st.selectbox("Filtrar por Localidad:", ['Todos'] + sorted(list(df_citas_actual['Localidad'].dropna().unique())))
    with col4:
        # **FILTRO DE ZONA MEJORADO**
        filtro_zona = st.selectbox("Filtrar por Zona:", ['Todos'] + sorted(list(df_citas_actual['Zona'].dropna().unique())))

    # Aplicar Filtros
    df_filtrado = df_citas_actual.copy()
    
    # Conversión de Fecha
    df_filtrado['Fecha'] = pd.to_datetime(df_filtrado['Fecha'])
    
    # Filtro 1: Por Fecha
    df_filtrado = df_filtrado[df_filtrado['Fecha'] >= pd.to_datetime(filtro_fecha)]

    # Filtro 2, 3, 4: Por Nombre, Localidad y Zona
    if filtro_nombre != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Nombre'] == filtro_nombre]

    if filtro_localidad != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Localidad'] == filtro_localidad]

    if filtro_zona != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Zona'] == filtro_zona]

    # --- MOSTRAR RESULTADOS Y EXPORTAR ---
    st.subheader(f"Resultados ({len(df_filtrado)} visitas):")
    
    if df_filtrado.empty:
        st.info("No hay visitas que coincidan con los filtros seleccionados.")
    else:
        df_display = df_filtrado.sort_values(by='Fecha', ascending=False).copy()
        df_display['Fecha'] = df_display['Fecha'].dt.strftime('%d/%m/%Y')
        st.dataframe(df_display, use_container_width=True, hide_index=True)

        # Botón de Exportar
        csv = df_display.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Descargar Datos Filtrados (CSV)",
            data=csv,
            file_name='reporte_visitas_filtrado.csv',
            mime='text/csv',
        )

# Inicialización de DataFrames en el estado de sesión
if 'df_clientes' not in st.session_state:
    st.session_state.df_clientes = df_clientes
if 'df_citas' not in st.session_state:
    st.session_state.df_citas = df_citas