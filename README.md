# Bird Species Observation Analysis in Forest and Grassland Ecosystem

## Introduction
This project delves into the analysis of bird species observations in distinct forest and grassland ecosystems. Its primary aim is to uncover critical insights into bird distribution, diversity, and habitat preferences, ultimately contributing to informed ecological conservation and land management strategies.

## Data Sources & Guidelines
The project utilizes observational data of bird species recorded across multiple forest and grassland sites.
* **Data Files**: `Bird_Monitoring_Data_FOREST.XLSX` and `Bird_Monitoring_Data_GRASSLAND.XLSX`.
* The project adheres to best practices for data handling and analysis.

## File Structure
The core project files are organized as follows:
* `data_ingestion.py`: Handles initial data loading from Excel files (reading all sheets from both Excel workbooks), consolidation, cleaning, type conversion, and feature engineering. It then loads the processed data into PostgreSQL.
* `eda.py`: Performs comprehensive Exploratory Data Analysis, generating insights and saving static and interactive plots into the `eda_plots/` directory.
* `app.py`: The main Streamlit application script for the interactive dashboard.
* `requirements.txt`: Lists all Python libraries required to run the project.
* `.gitignore`: Specifies files and directories to be ignored by Git (e.g., virtual environment, generated data files like `cleaned_bird_observations.csv`).
* `eda_plots/`: Directory containing static (.png) and interactive (.html) EDA plots generated by `eda.py`.
* `screenshots/`: (Optional) Directory to place screenshots of your Streamlit application's key features.

## How to Run Locally
Follow these steps to set up and run the project on your machine:

1.  **Clone the repository**:
    ```bash
    git clone [https://github.com/Roshan-25-cbe/Bird-Species-Observation-Analysis-in-Forest-and-Grassland-Ecosystem.git](https://github.com/Roshan-25-cbe/Bird-Species-Observation-Analysis-in-Forest-and-Grassland-Ecosystem.git)
    cd Bird-Species-Observation-Analysis-in-Forest-and-Grassland-Ecosystem
    ```

2.  **Create and activate a Python virtual environment**:
    ```bash
    python -m venv .venv
    ```
    * **Windows (Command Prompt / PowerShell):** `.\.venv\Scripts\activate`
    * **macOS/Linux:** `source ./.venv/bin/activate`

3.  **Install dependencies**:
    * First, create a `requirements.txt` file in your project's root directory. Copy and paste the following into it:
        ```
        pandas
        openpyxl
        sqlalchemy
        psycopg2-binary
        plotly
        streamlit
        kaleido
        ```
    * Then, install them using pip:
        ```bash
        pip install -r requirements.txt
        ```

4.  **Set up PostgreSQL Database and Prepare Data**:
    * **Ensure PostgreSQL is installed and running** on your system.
    * **Create a database** for this project (e.g., `bird_analysis_db`) and a user (e.g., `postgres` with password `Roshan@2025`) with full privileges on this database. You can do this via `psql` or `pgAdmin`.
    * **Place the raw data files** (`Bird_Monitoring_Data_FOREST.XLSX` and `Bird_Monitoring_Data_GRASSLAND.XLSX`) directly in the root of your project folder.
    * **Update the connection details** (`PG_USERNAME`, `PG_PASSWORD`, `PG_HOST`, `PG_PORT`, `PG_DB_NAME`) in `data_ingestion.py` and `app.py` to match your PostgreSQL setup. (You used `postgres` and `Roshan@2025` with `localhost:5432/bird_analysis_db`).
    * **Run the data ingestion script** to load, clean, and store data in PostgreSQL:
        ```bash
        python data_ingestion.py
        ```
        This script will create the `bird_observations` table in your `bird_analysis_db`. It will also generate a `cleaned_bird_observations.csv` backup file.

5.  **Perform Exploratory Data Analysis (Optional Step for Report Generation)**:
    * To generate static and interactive EDA plots for your report, run the EDA script:
        ```bash
        python eda.py
        ```
        This will create the `eda_plots/` directory containing all generated visualizations. You can view the `.html` files in any web browser for interactive exploration.

6.  **Run the Streamlit Dashboard**:
    * Ensure your PostgreSQL server is still running.
    * Run the Streamlit application script:
        ```bash
        streamlit run app.py
        ```
    * This will open the interactive dashboard in your web browser (typically at `http://localhost:8501`).

## Technologies Used
* Python 3.x (with `pandas`, `sqlalchemy`, `psycopg2-binary`, `openpyxl`, `plotly`, `streamlit`, `kaleido` libraries)
* PostgreSQL (Database Management System)
* Streamlit (Web Application Framework for Dashboards)
* Plotly (Interactive Visualization Library)
* VS Code (Integrated Development Environment)
* Git & GitHub (Version Control)

## Key Findings & Insights
Through a structured analysis approach (Data Preparation -> EDA -> Deep Dive Analyses -> Visualization), several key insights were derived:

* **Habitat Biodiversity:** Grassland ecosystems consistently exhibit higher unique bird species diversity compared to forest habitats. This highlights the critical ecological importance of preserving and managing grassland areas for avian populations.
* **Optimal Observation Periods:** Bird activity and observation counts show distinct temporal patterns, with observations often clustered within specific months (e.g., May-July in 2018 data) and peaking during certain hours of the day or days of the week. This suggests optimal timing for future bird surveys or eco-tourism activities.
* **Biodiversity Hotspots & Site Prioritization:** Specific observation plots or administrative units were identified as biodiversity hotspots, showing significantly higher unique species counts. These locations warrant focused conservation planning and resource allocation.
* **Environmental Influence:** Analyses explored correlations between bird observations and environmental conditions (temperature, humidity, sky, wind) and the impact of disturbances. These findings can inform adaptive land management and conservation policies.


## Conclusion & Recommendations
Based on the analysis, we recommend:
1.  **Prioritizing Diverse Ecosystems:** Focused conservation efforts and land management strategies should be directed towards ecosystems identified with higher bird species diversity (e.g., Forests in our analysis) while also implementing specific strategies for habitats with unique species.
2.  **Optimizing Survey & Monitoring Efforts:** Aligning bird observation surveys with identified peak activity times and months (e.g., Spring mornings) can enhance efficiency and accuracy in biodiversity monitoring.
3.  **Targeting Conservation Hotspots:** Directing conservation resources and planning to specific identified high-diversity plots or administrative units will yield maximum impact on avian community health.
4.  **Data-Driven Policy Development:** Utilizing the observed relationships between environmental factors and bird behavior can help environmental agencies create more effective and adaptive conservation policies.

## Presentation

The project has been presented, and you can find the slides [here](https://1drv.ms/p/c/ff0f2d98614978aa/EQDbIsCwtTFCs_UEKil6XEUBPNtmLAeQqvx5bOFawxP_Lw?e=isR6hR)

## Challenges Faced
* **Data Consolidation & Cleaning from Multi-Sheet Excel:** Successfully reading and combining data from multiple sheets within two separate Excel workbooks, extracting `Admin_Unit_Code` and `Location_Type` dynamically, and ensuring robust type conversions (especially for `Date` and boolean fields) was a significant initial challenge.
* **PostgreSQL Integration:** Establishing a reliable connection to PostgreSQL from Python, particularly resolving issues with special characters in the password (requiring URL encoding), was a key hurdle. Debugging `OperationalError` for non-existent roles or databases required precise verification of database credentials.
* **Plotly Library Dependencies:** Ensuring all Plotly functionalities, including saving static plots, worked correctly involved installing necessary dependencies like `kaleido` and debugging `No matching distribution found` errors.
* **Git Repository Management:** Experienced common Git setup issues in the Windows terminal, including `Permission denied` warnings (due to incorrect directory for `git init`) and `remote contains work` conflicts (when pushing to a pre-initialized GitHub repository). These were resolved by performing Git operations within the correct project directory, setting a default editor, and executing a `git pull --allow-unrelated-histories` before the final `git push`.

## Future Enhancements
* Integrate historical data from multiple years to analyze long-term population trends and environmental impacts.
* Incorporate geographical coordinates for interactive map visualizations of bird distributions and hotspots.
* Develop predictive models for species presence or abundance based on environmental variables.
* Add more interactive filters and drill-down capabilities within the Streamlit dashboard for deeper user exploration.

---

## Project Author
* **Roshan**
* **GitHub:** [https://github.com/Roshan-25-cbe/Bird-Species-Observation-Analysis-in-Forest-and-Grassland-Ecosystem.git](https://github.com/Roshan-25-cbe/Bird-Species-Observation-Analysis-in-Forest-and-Grassland-Ecosystem.git)
* **LinkedIn:** [www.linkedin.com/in/roshan-angamuthu-195ba230a](www.linkedin.com/in/roshan-angamuthu-195ba230a)
* **Contact Email:** [roshana36822@gmail.com](mailto:roshana36822@gmail.com)
