import streamlit as st
from src.agents.supervisor import TravelBuddySupervisor

st.set_page_config(page_title="AI Travel Buddy", page_icon="🧭", layout="wide")

# ---- Hero ----
st.markdown(
    """
    <div style="padding:28px 22px; background:linear-gradient(90deg,#0f172a,#1e293b); border-radius:14px; color:white;">
        <h1 style="margin:0; font-size:32px;">🧭 AI Travel Buddy</h1>
        <p style="opacity:.9; margin:6px 0 0;">Multi‑agent trip planning (TEST env) — structured inputs for reliable scraping.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.write("")

# ---- Structured inputs (no more giant prompt) ----
col1, col2 = st.columns(2)
with col1:
    origin = st.text_input(
        "Origin (city or IATA)", value="LHE", help="e.g., LHE or Lahore"
    )
    start_date = st.date_input("Start date")
    budget = st.number_input("Total budget", min_value=0.0, step=50.0, value=2000.0)
with col2:
    destination = st.text_input(
        "Destination (city or IATA)", value="Rome", help="e.g., ROM or Rome"
    )
    end_date = st.date_input("End date")
    preferences = st.text_area("Preferences (comma‑separated)", value="history, food")

currency = st.text_input("Currency (ISO)", value="USD")

run = st.button("🚀 Plan my trip", type="primary", use_container_width=True)

# ---- Execute graph ----
if run:
    with st.spinner("Running agents..."):
        supervisor = TravelBuddySupervisor()

        # Build structured trip_request (what the parser validates/passes through)
        trip_request = {
            "origin": origin.strip(),
            "destination": destination.strip(),
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "budget": float(budget) if budget else None,
            "preferences": [p.strip() for p in preferences.split(",") if p.strip()],
        }

        # We still pass user_input for backward compatibility, but it's unused now
        input_state = {
            "user_input": "",
            "home_iata": None,
            "currency": currency.strip().upper(),
            "trip_request": trip_request,
        }

        output = supervisor.run(input_state)

    st.success("Done!")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Trip Request", "Flights & Hotels", "Itinerary", "Packing List", "Reminders"]
    )

    with tab1:
        st.subheader("Parsed Trip Request")
        st.json(output.get("trip_request", {}))

    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("✈️ Flights")
            st.json(output.get("flight_options", []))
        with c2:
            st.subheader("🏨 Hotels")
            st.json(output.get("hotel_options", []))

    with tab3:
        st.subheader("🗓️ Itinerary")
        st.json(output.get("itinerary", []))

    with tab4:
        st.subheader("🧳 Packing List")
        st.json(output.get("packing_list", []))

    with tab5:
        st.subheader("⏰ Reminders")
        st.json(output.get("reminders", []))
