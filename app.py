import streamlit as st
from supabase import create_client
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Prode Online", page_icon="⚽")

# Pon esto al principio de tu app
st.warning("⚠️ ¡Recuerda! Tienes hasta el viernes a las 20:00 para cerrar tus apuestas de la Jornada 29.")

LOGOS_EQUIPOS = {
    "Alavés": "https://tmssl.akamaized.net//images/wappen/head/1108.png?lm=1596131395",
    "Athletic Club": "https://upload.wikimedia.org/wikipedia/en/9/98/Club_Athletic_Bilbao_logo.svg",
    "Atlético Madrid": "https://upload.wikimedia.org/wikipedia/en/f/f4/Atletico_madrid_2017_logo.svg",
    "Barcelona": "https://upload.wikimedia.org/wikipedia/en/4/47/FC_Barcelona.svg",
    "Celta de Vigo": "https://upload.wikimedia.org/wikipedia/en/1/12/RC_Celta_de_Vigo_logo.svg",
    "Elche": "https://upload.wikimedia.org/wikipedia/en/e/e3/Elche_CF_logo.svg",
    "Espanyol": "https://upload.wikimedia.org/wikipedia/en/d/d6/RCD_Espanyol_logo.svg",
    "Getafe": "https://upload.wikimedia.org/wikipedia/en/7/7f/Getafe_CF_logo.svg",
    "Girona": "https://upload.wikimedia.org/wikipedia/en/9/90/Girona_FC_logo.svg",
    "Levante": "https://upload.wikimedia.org/wikipedia/en/7/7b/Levante_Uni%C3%B3n_Deportiva_logo.svg",
    "Mallorca": "https://upload.wikimedia.org/wikipedia/en/e/e0/RCD_Mallorca_logo.svg",
    "Osasuna": "https://upload.wikimedia.org/wikipedia/en/d/db/CA_Osasuna_logo.svg",
    "Rayo Vallecano": "https://upload.wikimedia.org/wikipedia/en/1/11/Rayo_Vallecano_logo.svg",
    "Real Betis": "https://upload.wikimedia.org/wikipedia/en/1/11/Real_betis_logo.svg",
    "Real Madrid": "https://upload.wikimedia.org/wikipedia/en/5/56/Real_Madrid_CF.svg",
    "Real Oviedo": "https://upload.wikimedia.org/wikipedia/en/a/a2/Real_Oviedo_logo.svg",
    "Real Sociedad": "https://upload.wikimedia.org/wikipedia/en/f/f1/Real_Sociedad_logo.svg",
    "Sevilla": "https://upload.wikimedia.org/wikipedia/en/3/3b/Sevilla_FC_logo.svg",
    "Valencia": "https://upload.wikimedia.org/wikipedia/en/c/ce/Valenciacf.svg",
    "Villarreal": "https://upload.wikimedia.org/wikipedia/en/7/70/Villarreal_CF_logo.svg",
    "Default": "https://upload.wikimedia.org/wikipedia/commons/d/d3/Soccerball.svg"
}
# --- 1. CONFIGURACIÓN DE CONEXIÓN ---
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
SERVICE_KEY = st.secrets["SUPABASE_SERVICE_KEY"]

# MUEVE ESTO AQUÍ ARRIBA ⬇️
ADMIN_ID = "19789338-f0e2-4766-be43-7a8c5c805339" 

# Clientes
supabase = create_client(URL, KEY)
supabase_admin = create_client(URL, SERVICE_KEY)

st.title("⚽ Prode Online: ¡Adivina y Gana!")

# --- 2. SISTEMA DE AUTENTICACIÓN ---
st.sidebar.header("Acceso de Usuario")

if 'user' not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    menu = ["Login", "Registrarse"]
    choice = st.sidebar.selectbox("Selecciona una opción", menu)
    email = st.sidebar.text_input("Correo Electrónico")
    password = st.sidebar.text_input("Contraseña", type='password')

    if choice == "Registrarse":
        if st.sidebar.button("Crear Cuenta"):
            try:
                res = supabase.auth.sign_up({"email": email, "password": password})
                if res.user:
                    time.sleep(1)
                    nuevo_perfil = {
                        "id": res.user.id, 
                        "username": email.split('@')[0]
                    }
                    # Usamos el cliente normal para el perfil
                    supabase.table("profiles").upsert(nuevo_perfil).execute()
                    st.sidebar.success("✅ ¡Cuenta creada! Ahora cambia a 'Login'.")
                else:
                    st.sidebar.error("No se pudo crear el usuario.")
            except Exception as e:
                st.sidebar.error(f"Error al registrar: {e}")

    elif choice == "Login":
        if st.sidebar.button("Entrar"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = res.user
                st.sidebar.success(f"Sesión iniciada: {res.user.email}")
                st.rerun() 
            except Exception as e:
                st.sidebar.error("Email o contraseña incorrectos")

else:
    st.sidebar.write(f"👤 Logueado como: **{st.session_state.user.email}**")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.user = None
        st.rerun()

# --- 3. CONTROL DE ACCESO ---
if st.session_state.user is None:
    st.info("👈 Por favor, regístrate o inicia sesión en el menú de la izquierda para ver los partidos.")
    st.stop() 

# --- SECCIÓN: MI PERFIL ---
with st.sidebar.expander("⚙️ Configuración de Perfil"):
    st.subheader("Tu Apodo en el Ranking")
    perfil_actual = supabase.table("profiles").select("username").eq("id", st.session_state.user.id).single().execute()
    nombre_actual = perfil_actual.data.get('username', 'Usuario')
    
    nuevo_nombre = st.text_input("Cambiar Apodo:", value=nombre_actual)
    
    if st.button("Guardar Cambios"):
        try:
            supabase.table("profiles").update({"username": nuevo_nombre}).eq("id", st.session_state.user.id).execute()
            st.success("¡Apodo actualizado!")
            st.rerun()
        except Exception as e:
            st.error(f"Error al actualizar: {e}")

# --- 4. TUS PARTIDOS (APUESTAS) ---
st.header("Próximos Partidos")

try:
    response = supabase.table("matches").select("*").eq("finalizado", False).execute()
    partidos = response.data
except Exception as e:
    st.error(f"Error al conectar con la base de datos: {e}")
    partidos = []

if not partidos:
    st.info("No hay partidos activos por ahora.")
else:
    for partido in partidos:
        with st.container():
            col_img1, col_vs, col_img2 = st.columns([1, 3, 1])
            with col_img1:
                st.image(LOGOS_EQUIPOS.get(partido['equipo_local'], LOGOS_EQUIPOS["Default"]), width=60)
            with col_vs:
                st.markdown(f"<h3 style='text-align: center;'>{partido['equipo_local']} vs {partido['equipo_visitante']}</h3>", unsafe_allow_html=True)
            with col_img2:
                st.image(LOGOS_EQUIPOS.get(partido['equipo_visitante'], LOGOS_EQUIPOS["Default"]), width=60)

            c1, c2 = st.columns(2)
            with c1:
                goles_l = st.number_input(f"Goles {partido['equipo_local']}", min_value=0, key=f"l_{partido['id']}")
            with c2: 
                goles_v = st.number_input(f"Goles {partido['equipo_visitante']}", min_value=0, key=f"v_{partido['id']}")
            
            if st.button("Enviar Predicción", key=f"btn_{partido['id']}", use_container_width=True):
                try:
                    data = {
                        "match_id": partido['id'],
                        "prediccion_local": goles_l,
                        "prediccion_visitante": goles_v,
                        "user_id": st.session_state.user.id
                    }
                    
                    # SI ERES EL ADMIN, USAMOS LA LLAVE MAESTRA
                    if st.session_state.user.id == ADMIN_ID:
                        supabase_admin.table("predictions").insert(data).execute()
                    else:
                        # SI ES UN USUARIO NORMAL, USA LA LLAVE NORMAL
                        supabase.table("predictions").insert(data).execute()
                        
                    st.success(f"✅ ¡Predicción guardada!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")
            st.divider()

# --- 5. TABLA DE POSICIONES ---
st.header("🏆 Tabla de Posiciones")
try:
    preds = supabase.table("predictions").select("*, matches(goles_local_real, goles_visitante_real, finalizado), profiles(username)").execute().data
    ranking = {}
    for p in preds:
        info_partido = p.get('matches')
        if info_partido and info_partido.get('finalizado'):
            user = p.get('profiles', {}).get('username', 'Usuario Anónimo')
            if user not in ranking: ranking[user] = 0
            real_l, real_v = info_partido['goles_local_real'], info_partido['goles_visitante_real']
            pred_l, pred_v = p['prediccion_local'], p['prediccion_visitante']
            if pred_l == real_l and pred_v == real_v:
                ranking[user] += 3
            elif (real_l > real_v and pred_l > pred_v) or (real_v > real_l and pred_v > pred_l) or (real_l == real_v and pred_l == pred_v):
                ranking[user] += 1

    if not ranking:
        st.info("Todavía no hay puntos repartidos.")
    else:
        ranking_ordenado = sorted(ranking.items(), key=lambda x: x[1], reverse=True)
        for i, (usuario, puntos) in enumerate(ranking_ordenado):
            st.write(f"{'🥇' if i==0 else '🥈' if i==1 else '🥉' if i==2 else '👤'} **{usuario}**: {puntos} pts")
except Exception as e:
    st.error(f"Error al calcular ranking: {e}")

# --- 6. PANEL DE ADMINISTRADOR ---
# Asegúrate de que este ID sea el tuyo en la tabla auth.users
ADMIN_ID = "19789338-f0e2-4766-be43-7a8c5c805339" 

if st.session_state.user.id == ADMIN_ID:
    st.divider()
    st.header("⚙️ Panel de Administrador")
    
    with st.expander("🔑 Añadir Nuevos Partidos"):
        lista_equipos = sorted([e for e in LOGOS_EQUIPOS.keys() if e != "Default"])
        c1, c2 = st.columns(2)
        with c1:
            local = st.selectbox("Equipo Local", lista_equipos)
            fecha = st.date_input("Fecha")
        with c2:
            visitante = st.selectbox("Equipo Visitante", lista_equipos, index=1)
            hora = st.time_input("Hora")

        if st.button("Publicar Partido", use_container_width=True):
            nuevo_match = {
                "equipo_local": local, "equipo_visitante": visitante,
                "fecha": str(fecha), "hora": str(hora), "finalizado": False
            }
            try:
                # AQUÍ USAMOS EL CLIENTE ADMIN
                supabase_admin.table("matches").insert(nuevo_match).execute()
                st.success("✅ ¡Partido añadido!")
                st.rerun()
            except Exception as e:
                st.error(f"Error Admin: {e}")

    with st.expander("🏆 Finalizar Partidos"):
        partidos_abiertos = supabase.table("matches").select("*").eq("finalizado", False).execute().data
        if not partidos_abiertos:
            st.info("No hay partidos pendientes.")
        else:
            for m in partidos_abiertos:
                col_p, col_r1, col_r2, col_btn = st.columns([3, 1, 1, 2])
                col_p.write(f"**{m['equipo_local']} vs {m['equipo_visitante']}**")
                res_l = col_r1.number_input("L", min_value=0, key=f"res_l_{m['id']}")
                res_v = col_r2.number_input("V", min_value=0, key=f"res_v_{m['id']}")
                
                if col_btn.button("Puntuar", key=f"fin_{m['id']}"):
                    # AQUÍ TAMBIÉN USAMOS EL CLIENTE ADMIN
                    supabase_admin.table("matches").update({
                        "goles_local_real": res_l,
                        "goles_visitante_real": res_v,
                        "finalizado": True
                    }).eq("id", m['id']).execute()
                    st.success("¡Puntos repartidos!")
                    st.rerun()
