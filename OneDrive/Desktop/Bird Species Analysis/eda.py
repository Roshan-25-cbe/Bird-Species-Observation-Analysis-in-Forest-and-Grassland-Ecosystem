import pandas as pd
import plotly.express as px
import plotly.io as pio # To save plotly figures
from sqlalchemy import create_engine
from urllib.parse import quote_plus # For encoding password
import os

# --- Database Connection Details ---
# IMPORTANT: These must match your PostgreSQL setup
PG_USERNAME = 'postgres'          # Your confirmed username
PG_PASSWORD = 'Roshan@2025'       # Your confirmed password
PG_HOST = 'localhost'             # Your confirmed host
PG_PORT = '5432'                  # Your confirmed port
PG_DB_NAME = 'bird_analysis_db'    # Your confirmed database name

# URL-encode the password for the connection string
encoded_password = quote_plus(PG_PASSWORD)
DATABASE_URL = f'postgresql://{PG_USERNAME}:{encoded_password}@{PG_HOST}:{PG_PORT}/{PG_DB_NAME}'

# --- Output Folder for Plots ---
EDA_PLOTS_DIR = 'eda_plots'
os.makedirs(EDA_PLOTS_DIR, exist_ok=True) # Create the directory if it doesn't exist

# --- Data Loading Function ---
def get_data_from_sql():
    """Fetches data from the SQL database and performs initial processing."""
    engine = create_engine(DATABASE_URL)
    try:
        print("Fetching data from PostgreSQL...")
        df = pd.read_sql('SELECT * FROM "bird_observations"', engine)
        print(f"Data fetched. Shape: {df.shape}")

        # Ensure correct data types for analysis and plotting
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['ObservationYear'] = df['Date'].dt.year.fillna(0).astype(int)
        df['ObservationMonth'] = df['Date'].dt.month.fillna(0).astype(int)
        
        # Convert Start_Time to extract hour
        df['Start_Time_DT'] = pd.to_datetime(df['Start_Time'], format='%H:%M:%S', errors='coerce')
        df['ObservationHour'] = df['Start_Time_DT'].dt.hour.fillna(-1).astype(int)

        # Convert boolean columns to actual booleans
        df['PIF_Watchlist_Status'] = df['PIF_Watchlist_Status'].astype(bool)
        df['Regional_Stewardship_Status'] = df['Regional_Stewardship_Status'].astype(bool)
        df['Flyover_Observed'] = df['Flyover_Observed'].astype(bool)

        # Convert Distance to an ordered categorical type for better plotting order
        distance_order = ['<=50 Meters', '50-100 Meters', '>100 Meters', 'Unknown']
        df['Distance'] = pd.Categorical(df['Distance'], categories=distance_order, ordered=True)

        print("Data preparation for EDA complete.")
        return df
    except Exception as e:
        print(f"Error fetching data from PostgreSQL: {e}")
        print("Please ensure your PostgreSQL server is running and connection details are correct.")
        return pd.DataFrame()

# --- EDA and Plotting Functions ---

def plot_and_save(fig, filename, title):
    """Saves a Plotly figure to the EDA_PLOTS_DIR."""
    filepath_png = os.path.join(EDA_PLOTS_DIR, f"{filename}.png")
    filepath_html = os.path.join(EDA_PLOTS_DIR, f"{filename}.html")
    
    pio.write_image(fig, filepath_png, scale=2) # Save as high-res PNG
    pio.write_html(fig, filepath_html, include_plotlyjs='cdn') # Save as interactive HTML
    print(f"Saved plot: '{title}' to {filepath_png} and {filepath_html}")


def perform_eda_and_plot(df):
    """Performs various EDA analyses and generates plots."""

    print("\n--- Performing EDA and Generating Plots ---")

    # 1. Overall Data Overview
    print("Generating Overall Data Overview plots...")
    overall_metrics = pd.DataFrame({
        'Metric': ['Total Observations', 'Unique Species', 'Unique Sites', 'Average Temperature'],
        'Value': [
            df.shape[0],
            df['Common_Name'].nunique(),
            df['Site_Name'].nunique(),
            f"{df['Temperature'].mean():.1f} °C" if not df['Temperature'].isnull().all() else "N/A"
        ]
    })
    print(overall_metrics) # Print to console for summary
    
    # 2. Temporal Analysis
    print("Generating Temporal Analysis plots...")
    # Observations by Month
    valid_temporal_df = df[df['ObservationMonth'] > 0] # Filter out invalid dates
    if not valid_temporal_df.empty:
        observations_by_month = valid_temporal_df.groupby('ObservationMonth').size().reset_index(name='Count')
        month_names = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun', 
                       7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}
        observations_by_month['Month_Name'] = observations_by_month['ObservationMonth'].map(month_names)
        fig_monthly = px.bar(observations_by_month.sort_values('ObservationMonth'), x='Month_Name', y='Count',
                             title='Total Observations by Month', labels={'Month_Name': 'Month', 'Count': 'Number of Observations'})
        plot_and_save(fig_monthly, 'temporal_monthly_observations', 'Total Observations by Month')
    else:
        print("Skipping monthly observations plot due to no valid date data.")

    # Observations by Year
    if not valid_temporal_df.empty:
        observations_by_year = valid_temporal_df.groupby('ObservationYear').size().reset_index(name='Count')
        fig_yearly = px.line(observations_by_year, x='ObservationYear', y='Count',
                             title='Total Observations Per Year', labels={'ObservationYear': 'Year', 'Count': 'Number of Observations'})
        plot_and_save(fig_yearly, 'temporal_yearly_observations', 'Total Observations Per Year')
    else:
        print("Skipping yearly observations plot due to no valid date data.")

    # Observations by Hour of Day
    valid_hourly_df = df[df['ObservationHour'] != -1] # Filter out invalid hours
    if not valid_hourly_df.empty:
        hourly_counts = valid_hourly_df['ObservationHour'].value_counts().sort_index().reset_index()
        hourly_counts.columns = ['Hour', 'Count']
        fig_hourly = px.bar(hourly_counts, x='Hour', y='Count',
                            title='Observations by Hour of Day', labels={'Hour': 'Hour of Day', 'Count': 'Number of Observations'})
        plot_and_save(fig_hourly, 'temporal_hourly_observations', 'Observations by Hour of Day')
    else:
        print("Skipping hourly observations plot due to no valid time data.")


    # 3. Spatial Analysis
    print("Generating Spatial Analysis plots...")
    # Species diversity by Location Type
    species_diversity_loc = df.groupby('Location_Type')['Common_Name'].nunique().reset_index(name='Unique_Species_Count')
    fig_diversity_loc = px.bar(species_diversity_loc, x='Location_Type', y='Unique_Species_Count', color='Location_Type',
                               title='Unique Species Count by Habitat Type', labels={'Location_Type': 'Habitat Type', 'Unique_Species_Count': 'Number of Unique Species'}, text='Unique_Species_Count')
    plot_and_save(fig_diversity_loc, 'spatial_species_diversity_by_habitat', 'Unique Species Count by Habitat Type')

    # Top 15 Observation Sites by Count
    obs_per_site = df['Site_Name'].value_counts().nlargest(15).reset_index(name='Count')
    obs_per_site.columns = ['Site_Name', 'Count']
    fig_site_obs = px.bar(obs_per_site, x='Site_Name', y='Count', color='Count',
                          title='Top 15 Observation Sites (by Count)', labels={'Site_Name': 'Site Name', 'Count': 'Number of Observations'})
    plot_and_save(fig_site_obs, 'spatial_top_sites_by_observations', 'Top 15 Observation Sites by Count')

    # Top 10 Plots by Unique Species
    plot_diversity = df.groupby(['Admin_Unit_Code', 'Plot_Name'])['Common_Name'].nunique().reset_index(name='Unique_Species_Count')
    plot_diversity_sorted = plot_diversity.sort_values(by='Unique_Species_Count', ascending=False).head(10)
    fig_plot_diversity = px.bar(plot_diversity_sorted, x='Plot_Name', y='Unique_Species_Count', color='Admin_Unit_Code',
                                title='Top 10 Plots by Unique Species Count', labels={'Plot_Name': 'Plot Name', 'Unique_Species_Count': 'Unique Species Count'})
    plot_and_save(fig_plot_diversity, 'spatial_top_plots_by_species', 'Top 10 Plots by Unique Species Count')


    # 4. Species Analysis
    print("Generating Species Analysis plots...")
    # Top 15 most frequently observed species
    top_species = df['Common_Name'].value_counts().nlargest(15).reset_index(name='Count')
    top_species.columns = ['Common_Name', 'Count']
    fig_top_species = px.bar(top_species, x='Common_Name', y='Count', color='Count',
                             title='Top 15 Most Frequently Observed Bird Species', labels={'Common_Name': 'Bird Species', 'Count': 'Number of Observations'})
    plot_and_save(fig_top_species, 'species_top_observed', 'Top 15 Most Observed Species')

    # ID Method Distribution
    id_method_counts = df['ID_Method'].value_counts().reset_index(name='Count')
    id_method_counts.columns = ['ID_Method', 'Count']
    fig_id_method = px.pie(id_method_counts, values='Count', names='ID_Method',
                           title='Distribution of Identification Methods', hole=0.3)
    plot_and_save(fig_id_method, 'species_id_method_distribution', 'ID Method Distribution')

    # Sex Ratio
    sex_counts = df['Sex'].value_counts().reset_index(name='Count')
    sex_counts.columns = ['Sex', 'Count']
    fig_sex_ratio = px.pie(sex_counts, values='Count', names='Sex',
                           title='Overall Sex Distribution of Observed Birds', hole=0.3)
    plot_and_save(fig_sex_ratio, 'species_sex_ratio', 'Overall Sex Ratio')


    # 5. Environmental Conditions Analysis
    print("Generating Environmental Conditions plots...")
    # Temperature Distribution
    valid_temp_df = df[df['Temperature'].notna()]
    if not valid_temp_df.empty:
        fig_temp_dist = px.histogram(valid_temp_df, x='Temperature', nbins=20,
                                     title='Distribution of Observations by Temperature', labels={'Temperature': 'Temperature (°C)'})
        plot_and_save(fig_temp_dist, 'env_temperature_distribution', 'Temperature Distribution')
    else:
        print("Skipping temperature distribution plot due to no valid temperature data.")

    # Wind Condition Observations
    wind_counts = df['Wind'].value_counts().reset_index(name='Count')
    wind_counts.columns = ['Wind_Condition', 'Count']
    fig_wind_cond = px.bar(wind_counts, x='Wind_Condition', y='Count', color='Count',
                           title='Observations by Wind Condition', labels={'Wind_Condition': 'Wind Condition', 'Count': 'Number of Observations'})
    plot_and_save(fig_wind_cond, 'env_wind_conditions', 'Observations by Wind Condition')

    # Disturbance Effect
    disturbance_counts = df['Disturbance'].value_counts().reset_index(name='Count')
    disturbance_counts.columns = ['Disturbance_Type', 'Count']
    fig_disturbance = px.bar(disturbance_counts, x='Disturbance_Type', y='Count', color='Count',
                             title='Observations by Reported Disturbance', labels={'Disturbance_Type': 'Disturbance Type', 'Count': 'Number of Observations'})
    plot_and_save(fig_disturbance, 'env_disturbance_effect', 'Observations by Disturbance Effect')


    # 6. Conservation Insights
    print("Generating Conservation Insights plots...")
    # PIF Watchlist Status
    watchlist_counts = df['PIF_Watchlist_Status'].value_counts().reset_index(name='Count')
    watchlist_counts.columns = ['Watchlist_Status', 'Count']
    fig_watchlist = px.pie(watchlist_counts, values='Count',
                           names=watchlist_counts['Watchlist_Status'].map({True: 'On Watchlist', False: 'Not On Watchlist'}),
                           title='Proportion of Observations for PIF Watchlist Species', hole=0.3)
    plot_and_save(fig_watchlist, 'conservation_pif_watchlist', 'PIF Watchlist Status')

    # Regional Stewardship Status
    stewardship_counts = df['Regional_Stewardship_Status'].value_counts().reset_index(name='Count')
    stewardship_counts.columns = ['Stewardship_Status', 'Count']
    fig_stewardship = px.pie(stewardship_counts, values='Count',
                             names=stewardship_counts['Stewardship_Status'].map({True: 'Regional Priority', False: 'Not Regional Priority'}),
                             title='Proportion of Observations by Regional Stewardship Status', hole=0.3)
    plot_and_save(fig_stewardship, 'conservation_regional_stewardship', 'Regional Stewardship Status')

    # Top At-Risk Species by Observation Count
    at_risk_species = df[(df['PIF_Watchlist_Status'] == True) | (df['Regional_Stewardship_Status'] == True)]
    if not at_risk_species.empty:
        at_risk_summary = at_risk_species['Common_Name'].value_counts().nlargest(10).reset_index(name='Count')
        at_risk_summary.columns = ['Common_Name', 'Count']
        fig_at_risk = px.bar(at_risk_summary, x='Common_Name', y='Count', color='Count',
                             title='Top 10 Observed At-Risk Species (by Count)', labels={'Common_Name': 'Species', 'Count': 'Number of Observations'})
        plot_and_save(fig_at_risk, 'conservation_top_at_risk_species', 'Top 10 Observed At-Risk Species')
    else:
        print("No at-risk species observed in the dataset.")

    print("\nEDA and plot generation complete. Check the 'eda_plots' folder for output files.")


if __name__ == "__main__":
    df_observations = get_data_from_sql()
    if not df_observations.empty:
        perform_eda_and_plot(df_observations)
    else:
        print("Cannot perform EDA as no data was loaded.")