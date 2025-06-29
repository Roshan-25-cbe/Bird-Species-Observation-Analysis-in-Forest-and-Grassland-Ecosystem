import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
from urllib.parse import quote_plus # For encoding password

# --- Database Connection ---
# These values are based on your confirmed setup:
PG_USERNAME = 'postgres'          # Your confirmed username
PG_PASSWORD = 'Roshan@2025'       # Your confirmed password
PG_HOST = 'localhost'             # Your confirmed host
PG_PORT = '5432'                  # Your confirmed port
PG_DB_NAME = 'bird_analysis_db'    # Your confirmed database name

# URL-encode the password for the connection string
encoded_password = quote_plus(PG_PASSWORD)
DATABASE_URL = f'postgresql://{PG_USERNAME}:{encoded_password}@{PG_HOST}:{PG_PORT}/{PG_DB_NAME}'

@st.cache_data # Cache data to avoid re-running every time the app reloads
def get_data_from_sql():
    """Fetches data from the SQL database and performs initial processing for dashboard."""
    engine = create_engine(DATABASE_URL)
    try:
        # Use double quotes for table name and column names for PostgreSQL case sensitivity
        df = pd.read_sql('SELECT * FROM "bird_observations"', engine)
        
        # Ensure correct data types for Streamlit/Plotly after fetching from SQL
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        # Fill missing year/month with 0 or a placeholder if Date is NaT,
        # otherwise they might cause errors in numeric conversions.
        df['ObservationYear'] = df['Date'].dt.year.fillna(0).astype(int) 
        df['ObservationMonth'] = df['Date'].dt.month.fillna(0).astype(int)
        
        # Convert Start_Time to datetime objects to extract hour
        df['Start_Time_DT'] = pd.to_datetime(df['Start_Time'], format='%H:%M:%S', errors='coerce')
        df['ObservationHour'] = df['Start_Time_DT'].dt.hour.fillna(-1).astype(int) # Fill with -1 for unknown/unparsed

        # Convert Distance to an ordered categorical type for better plotting order
        distance_order = ['<=50 Meters', '50-100 Meters', '>100 Meters', 'Unknown'] # Ensure 'Unknown' is last
        df['Distance'] = pd.Categorical(df['Distance'], categories=distance_order, ordered=True)
        
        # Convert Distance to a sortable numeric for better plotting if needed
        def convert_distance_numeric(dist_str):
            if pd.isna(dist_str) or str(dist_str).strip().lower() == 'unknown':
                return None
            dist_str = str(dist_str).strip().lower()
            if '<=50 meters' in dist_str:
                return 25
            elif '50-100 meters' in dist_str:
                return 75
            elif '>100 meters' in dist_str:
                return 125
            return None
        df['Distance_Numeric'] = df['Distance'].apply(convert_distance_numeric)

        # Ensure boolean columns are actual booleans for Plotly and filtering
        df['PIF_Watchlist_Status'] = df['PIF_Watchlist_Status'].astype(bool)
        df['Regional_Stewardship_Status'] = df['Regional_Stewardship_Status'].astype(bool)
        df['Flyover_Observed'] = df['Flyover_Observed'].astype(bool)

        return df
    except Exception as e:
        st.error(f"Error connecting to PostgreSQL database or fetching data: {e}")
        st.error("Please ensure your PostgreSQL server is running and connection details in app.py are correct.")
        return pd.DataFrame()

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="Bird Species Observation Analysis",
    layout="wide", # Use wide layout for more space
    initial_sidebar_state="expanded",
    menu_items={'About': "This dashboard analyzes bird species observations from various habitats."}
)

# --- Load Data ---
df = get_data_from_sql()

if df.empty:
    st.warning("No data available to display. Please ensure data_ingestion.py was run successfully and your PostgreSQL server is accessible.")
    st.stop() # Stop if no data is loaded

# --- Sidebar Filters ---
st.sidebar.header("Global Filters")

all_location_types = df['Location_Type'].unique()
selected_location_type = st.sidebar.multiselect(
    "Select Habitat Type(s)",
    options=all_location_types,
    default=all_location_types,
    help="Filter observations by forest or grassland habitats."
)

# --- UPDATED: Year filter changed from slider to multi-select ---
# Get all unique valid years (exclude 0 if it exists from date parsing errors)
all_years = sorted(df[df['ObservationYear'] > 0]['ObservationYear'].unique().tolist())
if not all_years: # If no valid years, provide a warning
    st.sidebar.warning("No valid years found in data for filtering.")
    selected_years = [] # No years selected if no valid data
else:
    selected_years = st.sidebar.multiselect(
        "Select Year(s)",
        options=all_years,
        default=all_years, # Default to selecting all years
        help="Filter observations by specific year(s)."
    )

all_observers = df['Observer'].unique()
selected_observers = st.sidebar.multiselect(
    "Select Observer(s)",
    options=all_observers,
    default=all_observers,
    help="Filter observations by the person who recorded them."
)

# Apply global filters
# Adjusted filter logic for selected_years (now a list)
if not selected_years: # If no years are selected, treat as no data selected for year
    filtered_df = pd.DataFrame() # Return empty DataFrame
else:
    filtered_df = df[
        (df['Location_Type'].isin(selected_location_type)) &
        (df['ObservationYear'].isin(selected_years)) & # Changed for multiselect
        (df['Observer'].isin(selected_observers))
    ]

st.sidebar.markdown("---")
st.sidebar.subheader("Explore Specific Species")
# Ensure 'Unknown' common name is excluded from species selection if desired
all_common_names = filtered_df['Common_Name'].unique()
species_options = sorted([name for name in all_common_names if name and name != 'Unknown'])
selected_species = st.sidebar.selectbox(
    "Select a Species (for detailed view)",
    options=['All Species'] + species_options,
    index=0
)

# --- Main Dashboard Content ---
st.title("🦅 Bird Species Observation Dashboard 🌿")
st.markdown("A comprehensive analysis of bird species distribution, diversity, and behavior across forest and grassland ecosystems.")

# Check if filtered_df is empty after applying filters
if filtered_df.empty:
    st.warning("No data available for the selected filters. Please adjust your selections in the sidebar.")
else:
    # --- Tabbed Navigation ---
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Overview & Key Metrics",
        "📈 Temporal Trends",
        "📍 Spatial Insights",
        "🌡️ Environmental Factors",
        "🦉 Conservation Status",
        "👤 Observer Trends"
    ])

    with tab1:
        st.header("Dashboard Overview")
        st.markdown("### Key Performance Indicators")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Observations", filtered_df.shape[0])
        with col2:
            st.metric("Unique Species Observed", filtered_df['Common_Name'].nunique())
        with col3:
            st.metric("Unique Sites", filtered_df['Site_Name'].nunique())
        with col4:
            avg_temp = filtered_df['Temperature'].mean()
            st.metric("Avg. Temp Across Obs.", f"{avg_temp:.1f} °C" if pd.notna(avg_temp) else "N/A")

        st.markdown("---")
        st.subheader("Top 10 Most Observed Species")
        top_species = filtered_df['Common_Name'].value_counts().nlargest(10).reset_index()
        top_species.columns = ['Common_Name', 'Count']
        fig_top_species = px.bar(
            top_species,
            x='Common_Name',
            y='Count',
            color='Common_Name',
            title='Top 10 Most Frequently Observed Bird Species',
            labels={'Common_Name': 'Bird Species', 'Count': 'Number of Observations'},
            text='Count'
        )
        fig_top_species.update_layout(showlegend=False)
        st.plotly_chart(fig_top_species, use_container_width=True)

        st.subheader("Observation Method Distribution")
        id_method_counts = filtered_df['ID_Method'].value_counts().reset_index()
        id_method_counts.columns = ['ID_Method', 'Count']
        fig_id_method = px.pie(
            id_method_counts,
            values='Count',
            names='ID_Method',
            title='Distribution of Identification Methods',
            hole=0.3
        )
        st.plotly_chart(fig_id_method, use_container_width=True)

    with tab2:
        st.header("Temporal Trends: When are Birds Most Active?")
        
        # Observations by Month
        st.subheader("Monthly Observation Patterns")
        # Filter out rows where date parsing might have failed (ObservationMonth is 0)
        valid_temporal_df = filtered_df[filtered_df['ObservationMonth'] > 0] 
        
        if not valid_temporal_df.empty:
            observations_by_month = valid_temporal_df.groupby('ObservationMonth').size().reset_index(name='Count')
            month_names = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun', 
                           7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}
            observations_by_month['Month_Name'] = observations_by_month['ObservationMonth'].map(month_names)
            
            fig_monthly = px.bar(
                observations_by_month.sort_values('ObservationMonth'),
                x='Month_Name',
                y='Count',
                title='Total Observations by Month',
                labels={'Month_Name': 'Month', 'Count': 'Number of Observations'}
            )
            st.plotly_chart(fig_monthly, use_container_width=True)
        else:
            st.info("No valid date data for monthly analysis in selected range.")

        # Observations over Years (Line Chart)
        st.subheader("Observations Over Time (Yearly View)")
        if not valid_temporal_df.empty:
            observations_by_year = valid_temporal_df.groupby('ObservationYear').size().reset_index(name='Count')
            fig_yearly_line = px.line(
                observations_by_year,
                x='ObservationYear',
                y='Count',
                title='Total Observations Per Year',
                labels={'ObservationYear': 'Year', 'Count': 'Number of Observations'}
            )
            fig_yearly_line.update_xaxes(dtick="M12", tickformat="%Y")
            st.plotly_chart(fig_yearly_line, use_container_width=True)
        else:
            st.info("No valid date data for yearly analysis in selected range.")

        st.subheader("Hourly Observation Patterns")
        # Filter out invalid hours (-1) for plotting
        valid_hourly_df = filtered_df[filtered_df['ObservationHour'] != -1]
        
        if not valid_hourly_df.empty:
            hourly_counts = valid_hourly_df['ObservationHour'].value_counts().sort_index().reset_index()
            hourly_counts.columns = ['Hour', 'Count']
            fig_hourly = px.bar(
                hourly_counts,
                x='Hour',
                y='Count',
                title='Observations by Hour of Day',
                labels={'Hour': 'Hour of Day', 'Count': 'Number of Observations'}
            )
            st.plotly_chart(fig_hourly, use_container_width=True)
        else:
            st.info("No valid start time data for hourly analysis.")

        # New: Temporal Heatmap (Year vs Month)
        st.subheader("Observations Heatmap: Year vs. Month")
        if not valid_temporal_df.empty:
            monthly_yearly_counts = valid_temporal_df.groupby(['ObservationYear', 'ObservationMonth']).size().reset_index(name='Count')
            # Map month numbers to names for better readability
            monthly_yearly_counts['Month_Name'] = monthly_yearly_counts['ObservationMonth'].map(month_names)
            
            fig_heatmap = px.density_heatmap(
                monthly_yearly_counts,
                x="Month_Name",
                y="ObservationYear",
                z="Count",
                nbinsx=12,
                title="Observation Count by Month and Year (Heatmap)",
                labels={'Month_Name': 'Month', 'ObservationYear': 'Year', 'Count': 'Observations'},
                color_continuous_scale="Viridis",
                category_orders={"Month_Name": list(month_names.values())} # Ensure months are in order
            )
            st.plotly_chart(fig_heatmap, use_container_width=True)
        else:
            st.info("No valid date data for heatmap analysis in selected range.")

    with tab3:
        st.header("Spatial Insights: Where are Birds Found?")
        
        # Species diversity by Location Type
        st.subheader("Species Diversity Across Habitat Types")
        species_diversity_loc = filtered_df.groupby('Location_Type')['Common_Name'].nunique().reset_index(name='Unique_Species_Count')
        fig_diversity_loc = px.bar(
            species_diversity_loc,
            x='Location_Type',
            y='Unique_Species_Count',
            color='Location_Type',
            title='Unique Species Count by Habitat Type',
            labels={'Location_Type': 'Habitat Type', 'Unique_Species_Count': 'Number of Unique Species'},
            text='Unique_Species_Count'
        )
        st.plotly_chart(fig_diversity_loc, use_container_width=True)

        # Observations per Site
        st.subheader("Observations by Site Name")
        obs_per_site = filtered_df['Site_Name'].value_counts().reset_index(name='Count')
        obs_per_site.columns = ['Site_Name', 'Count']
        fig_site = px.bar(
            obs_per_site.nlargest(15, 'Count'), # Show top 15 sites
            x='Site_Name',
            y='Count',
            color='Count',
            title='Top 15 Observation Sites (by Count)',
            labels={'Site_Name': 'Site Name', 'Count': 'Number of Observations'}
        )
        st.plotly_chart(fig_site, use_container_width=True)

        # Plot-Level Analysis (if many plots, use a table or filter)
        st.subheader("Plot-Level Insights (Top 10 Plots by Unique Species)")
        plot_diversity = filtered_df.groupby(['Admin_Unit_Code', 'Plot_Name'])['Common_Name'].nunique().reset_index(name='Unique_Species_Count')
        plot_diversity_sorted = plot_diversity.sort_values(by='Unique_Species_Count', ascending=False)
        st.dataframe(plot_diversity_sorted.head(10), use_container_width=True) # Show top 10 plots
        st.markdown("*(Note: This table shows top plots. Filter by Admin Unit or Plot Name in the sidebar for more specific details if implemented.)*")


    with tab4:
        st.header("Environmental Factors: How Weather Influences Birds")

        st.subheader("Temperature vs. Observation Count/Diversity")
        # Filter out NaN temperatures before binning
        valid_temp_df = filtered_df[filtered_df['Temperature'].notna()]

        if not valid_temp_df.empty:
            # Dynamically determine bins or use fixed ones if data range is limited
            temp_min = valid_temp_df['Temperature'].min()
            temp_max = valid_temp_df['Temperature'].max()
            num_bins = 10 if (temp_max - temp_min) > 10 else max(2, int(temp_max - temp_min)) # At least 2 bins
            if num_bins == 0: num_bins = 1 # Handle case where all temps are same

            # Use pd.cut to create bins, ensure unique bin labels
            temp_bins = pd.cut(valid_temp_df['Temperature'], bins=num_bins, precision=0, include_lowest=True)
            # Convert Interval to string to handle cases where pandas gives complex Interval objects
            temp_bins_str = temp_bins.astype(str)

            temp_obs = temp_bins_str.value_counts().sort_index().reset_index(name='Count')
            temp_obs.columns = ['Temp_Bin', 'Count'] # Rename columns for clarity
            
            fig_temp_count = px.bar(
                temp_obs,
                x='Temp_Bin',
                y='Count',
                title='Observation Count by Temperature Range',
                labels={'Temp_Bin': 'Temperature Range (°C)', 'Count': 'Number of Observations'}
            )
            st.plotly_chart(fig_temp_count, use_container_width=True)
        else:
            st.info("Temperature data is not available or not numeric for plotting under current filters.")

        st.subheader("Humidity and Wind Conditions")
        col_env1, col_env2 = st.columns(2)
        with col_env1:
            # Filter out 'Unknown' humidity if it's there as a categorical fill and NaNs
            valid_humidity_df = filtered_df[filtered_df['Humidity'].notna() & (filtered_df['Humidity'] != 'Unknown')]
            if not valid_humidity_df.empty:
                # Ensure humidity is numeric before binning
                valid_humidity_df['Humidity'] = pd.to_numeric(valid_humidity_df['Humidity'], errors='coerce')
                valid_humidity_df = valid_humidity_df.dropna(subset=['Humidity']) # Drop any NaNs from coerce

                if not valid_humidity_df.empty:
                    humidity_bins = pd.cut(valid_humidity_df['Humidity'], bins=5, precision=0, include_lowest=True).astype(str)
                    humidity_counts = humidity_bins.value_counts().sort_index().reset_index(name='Count')
                    humidity_counts.columns = ['Humidity_Range', 'Count']
                    fig_humidity = px.bar(
                        humidity_counts,
                        x='Humidity_Range',
                        y='Count',
                        title='Observations by Humidity Range',
                        labels={'Humidity_Range': 'Humidity (%)', 'Count': 'Number of Observations'}
                    )
                    st.plotly_chart(fig_humidity, use_container_width=True)
                else:
                    st.info("No valid humidity data after numeric conversion.")
            else:
                st.info("No valid humidity data for plotting.")

        with col_env2:
            wind_counts = filtered_df['Wind'].value_counts().reset_index(name='Count')
            wind_counts.columns = ['Wind_Condition', 'Count']
            fig_wind = px.bar(
                wind_counts,
                x='Wind_Condition',
                y='Count',
                color='Count',
                title='Observations by Wind Condition',
                labels={'Wind_Condition': 'Wind', 'Count': 'Number of Observations'}
            )
            st.plotly_chart(fig_wind, use_container_width=True)
        
        st.subheader("Impact of Disturbances on Observations")
        disturbance_effect = filtered_df['Disturbance'].value_counts().reset_index(name='Count')
        disturbance_effect.columns = ['Disturbance_Type', 'Count']
        fig_disturbance = px.bar(
            disturbance_effect,
            x='Disturbance_Type',
            y='Count',
            color='Count',
            title='Observations by Reported Disturbance',
            labels={'Disturbance_Type': 'Disturbance', 'Count': 'Number of Observations'}
        )
        st.plotly_chart(fig_disturbance, use_container_width=True)

    with tab5:
        st.header("Conservation Status: Protecting Our Avian Friends")
        st.markdown("Analyzing species based on their conservation watchlist and stewardship status to identify at-risk populations.")

        st.subheader("PIF Watchlist Status Distribution")
        watchlist_counts = filtered_df['PIF_Watchlist_Status'].value_counts().reset_index(name='Count')
        watchlist_counts.columns = ['Watchlist_Status', 'Count']
        fig_watchlist = px.pie(
            watchlist_counts,
            values='Count',
            names=watchlist_counts['Watchlist_Status'].map({True: 'On Watchlist', False: 'Not On Watchlist'}),
            title='Proportion of Observations for PIF Watchlist Species',
            hole=0.3
        )
        st.plotly_chart(fig_watchlist, use_container_width=True)

        st.subheader("Regional Stewardship Status Distribution")
        stewardship_counts = filtered_df['Regional_Stewardship_Status'].value_counts().reset_index(name='Count')
        stewardship_counts.columns = ['Stewardship_Status', 'Count']
        fig_stewardship = px.pie(
            stewardship_counts,
            values='Count',
            names=stewardship_counts['Stewardship_Status'].map({True: 'Regional Priority', False: 'Not Regional Priority'}),
            title='Proportion of Observations by Regional Stewardship Status',
            hole=0.3
        )
        st.plotly_chart(fig_stewardship, use_container_width=True)

        st.subheader("Observed At-Risk Species (PIF Watchlist OR Regional Stewardship)")
        at_risk_species = filtered_df[
            (filtered_df['PIF_Watchlist_Status'] == True) | 
            (filtered_df['Regional_Stewardship_Status'] == True)
        ]
        if not at_risk_species.empty:
            at_risk_summary = at_risk_species.groupby(['Location_Type', 'Common_Name']).size().reset_index(name='Count')
            fig_at_risk = px.bar(
                at_risk_summary.sort_values('Count', ascending=False),
                x='Common_Name',
                y='Count',
                color='Location_Type',
                title='Observed At-Risk Species by Habitat',
                labels={'Common_Name': 'Species', 'Count': 'Number of Observations'},
                hover_data=['Location_Type', 'Count']
            )
            st.plotly_chart(fig_at_risk, use_container_width=True)
        else:
            st.info("No 'At-Risk' species observed under current filters.")

    with tab6: # New Tab: Observer Trends
        st.header("Observer Trends & Visit Patterns")

        st.subheader("Observations by Observer")
        observer_counts = filtered_df['Observer'].value_counts().nlargest(10).reset_index(name='Count') # Top 10 observers
        observer_counts.columns = ['Observer', 'Count']
        fig_observer_obs = px.bar(
            observer_counts,
            x='Observer',
            y='Count',
            color='Count',
            title='Top 10 Observers by Total Observations',
            labels={'Observer': 'Observer Name', 'Count': 'Number of Observations'}
        )
        st.plotly_chart(fig_observer_obs, use_container_width=True)

        st.subheader("Unique Species per Observer")
        observer_unique_species = filtered_df.groupby('Observer')['Common_Name'].nunique().nlargest(10).reset_index(name='Unique Species Count')
        observer_unique_species.columns = ['Observer', 'Unique Species Count']
        fig_observer_unique = px.bar(
            observer_unique_species,
            x='Observer',
            y='Unique Species Count',
            color='Unique Species Count',
            title='Top 10 Observers by Unique Species Count',
            labels={'Observer': 'Observer Name', 'Unique Species Count': 'Number of Unique Species'}
        )
        st.plotly_chart(fig_observer_unique, use_container_width=True)

        st.subheader("Visit Patterns to Sites/Plots")
        visit_counts = filtered_df.groupby(['Site_Name', 'Visit']).size().reset_index(name='Count')
        # Display top 10 sites with their visit patterns
        top_sites_visits = visit_counts.groupby('Site_Name')['Count'].sum().nlargest(10).index
        fig_visit_pattern = px.bar(
            visit_counts[visit_counts['Site_Name'].isin(top_sites_visits)].sort_values(['Site_Name', 'Visit']),
            x='Visit',
            y='Count',
            color='Site_Name',
            title='Visit Patterns to Top 10 Observation Sites',
            labels={'Visit': 'Visit Number', 'Count': 'Number of Observations', 'Site_Name': 'Site'},
            barmode='group'
        )
        st.plotly_chart(fig_visit_pattern, use_container_width=True)
        
        # New: Flyover Observations general overview
        st.subheader("General Flyover Observations")
        flyover_counts = filtered_df['Flyover_Observed'].value_counts().reset_index(name='Count')
        flyover_counts.columns = ['Flyover_Observed', 'Count']
        fig_flyover_general = px.pie(
            flyover_counts,
            values='Count',
            names=flyover_counts['Flyover_Observed'].map({True: 'Flyover Observed', False: 'No Flyover'}),
            title='Proportion of Observations with Flyover',
            hole=0.3
        )
        st.plotly_chart(fig_flyover_general, use_container_width=True)


    # --- Detailed Species View (optional section if species is selected) ---
    if selected_species != 'All Species':
        st.markdown("---")
        st.header(f"Detailed Analysis for: {selected_species}")
        species_df = filtered_df[filtered_df['Common_Name'] == selected_species]

        if not species_df.empty:
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                st.subheader(f"{selected_species} - Sex Distribution")
                sex_counts = species_df['Sex'].value_counts().reset_index(name='Count')
                sex_counts.columns = ['Sex', 'Count']
                fig_sex = px.pie(
                    sex_counts,
                    values='Count',
                    names='Sex',
                    title=f'Sex Distribution for {selected_species}',
                    hole=0.4
                )
                st.plotly_chart(fig_sex, use_container_width=True)
            
            with col_s2:
                st.subheader(f"{selected_species} - Identification Methods")
                id_method_species_counts = species_df['ID_Method'].value_counts().reset_index(name='Count')
                id_method_species_counts.columns = ['ID_Method', 'Count']
                fig_id_species = px.bar(
                    id_method_species_counts,
                    x='ID_Method',
                    y='Count',
                    title=f'ID Methods for {selected_species}',
                    labels={'ID_Method': 'Identification Method', 'Count': 'Number of Observations'}
                )
                st.plotly_chart(fig_id_species, use_container_width=True)
            
            st.subheader(f"{selected_species} - Distance from Observer")
            # Filter out rows where Distance_Numeric is None/NaN
            valid_distance_df = species_df[species_df['Distance_Numeric'].notna()]
            if not valid_distance_df.empty:
                # Reorder categories for better visualization using the Categorical type defined at load
                distance_counts = valid_distance_df['Distance'].value_counts().reset_index(name='Count')
                distance_counts.columns = ['Distance_Category', 'Count']
                
                fig_distance = px.bar(
                    distance_counts,
                    x='Distance_Category',
                    y='Count',
                    title=f'Observation Distance for {selected_species}',
                    labels={'Distance_Category': 'Distance from Observer', 'Count': 'Number of Observations'},
                    category_orders={"Distance_Category": df['Distance'].cat.categories.tolist()} # Use the defined order
                )
                st.plotly_chart(fig_distance, use_container_width=True)
            else:
                st.info(f"Distance data for {selected_species} is not available or not numeric.")

        else:
            st.info(f"No observations for {selected_species} with current filters.")