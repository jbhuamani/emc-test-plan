import streamlit as st
import pandas as pd

# Set page configuration
st.set_page_config(layout="wide", page_title="Enhanced EMC Test Plan Generator")

# Load the updated database
@st.cache_data
def load_data():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-dcp7RM6MkGU32oBBR3afCt5ujMrlNeOVKtvXltvsvr7GbkqsJwHIDpu0Z73hYDwF8rDMzFbTnoc5/pub?gid=1351032631&single=true&output=csv"
    try:
        data = pd.read_csv(url)
        return data
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

# Filter the database based on user selections
def filter_database(df, product_features=None, entities=None, port_types=None, voltage_types=None, voltages=None):
    if product_features:
        df = df[df['PRODUCT_FEATURE'].isin(product_features)]
    if entities:
        df = df[df['ENTITY'].isin(entities)]
    if port_types:
        df = df[df['PORT_TYPE'].isin(port_types)]
    if voltage_types:
        df = df[df['VOLTAGE_TYPE'].isin(voltage_types)]
    if voltages:
        df = df[df['VOLTAGES'].isin(voltages)]
    return df

# Generate a summary of the test plan with a "Justifiable" section
def generate_summary(filtered_df):
    if filtered_df.empty:
        return "No test plan available for the selected criteria.", ""

    summary_lines = set()  # Use a set to avoid redundant lines
    justifiable_lines = set()

    criteria_hierarchy = {'A': 1, 'B': 2, 'C': 3}  # Lower value = stricter
    unique_cases = {}

    for _, row in filtered_df.iterrows():
        test_type = row['TEST_TYPE']
        criteria = row.get('DCR_Criteria') or row.get('ACV_Criteria')
        if criteria not in criteria_hierarchy:
            continue  # Skip invalid or missing criteria

        if test_type == "DC Ripple":
            frequency = row['DCR_Freq_[Hz]']
            level = row['DCR_Level_[%]']
            summary = f"DC Ripple: Frequency {frequency} Hz, Level {level}%, Criteria {criteria}"
        elif test_type == "AC VDI":
            applicability = row['ACV_Apply']
            frequency = row['ACV_Freq_[Hz]']
            reduction = row['ACV_Red_[%]']
            duration_cycles = row['ACV_Dur_[Cycles]']
            duration_ms = row['ACV_Dur_[ms]']
            crossing = row['ACV_Cross_[deg]']
            duration_str = f"{duration_cycles} cycles" if pd.notnull(duration_cycles) else ""
            duration_str += f", {duration_ms} ms" if pd.notnull(duration_ms) else ""
            summary = (f"AC VDI: Applicability {applicability}, Frequency {frequency} Hz, Reduction {reduction}%, "
                       f"Duration {duration_str}, Crossing {crossing} degrees, Criteria {criteria}")

        # Handle redundancy and justification
        if summary not in unique_cases:
            unique_cases[summary] = criteria
        else:
            existing_criteria = unique_cases[summary]
            if criteria_hierarchy[criteria] > criteria_hierarchy[existing_criteria]:
                justifiable_lines.add(summary)
            else:
                justifiable_lines.add(summary)
                unique_cases[summary] = criteria

    # Finalize unique and justifiable test cases
    unique_summaries = sorted([f"{i+1}) {summary}" for i, summary in enumerate(unique_cases.keys())])
    justifiable_summaries = sorted([f"{i+1}) {summary}" for i, summary in enumerate(justifiable_lines)])
    return "\n".join(unique_summaries), "\n".join(justifiable_summaries)

# Remove empty columns
def remove_empty_columns(df):
    return df.dropna(how="all", axis=1)

# Main application
def main():
    st.title("Enhanced EMC Test Plan Generator")
    st.write("Select options below to generate a test plan based on your requirements.")

    # Load the data
    df = load_data()
    if df.empty:
        st.error("No data available. Please check your database connection.")
        return

    # Sidebar multi-select menus
    st.sidebar.header("Filter Options")
    product_features = st.sidebar.multiselect(
        "Select PRODUCT_FEATURE:",
        df['PRODUCT_FEATURE'].unique().tolist()
    )
    filtered_df = filter_database(df, product_features=product_features)

    entities = st.sidebar.multiselect(
        "Select ENTITY:",
        filtered_df['ENTITY'].unique().tolist()
    )
    filtered_df = filter_database(filtered_df, entities=entities)

    port_types = st.sidebar.multiselect(
        "Select PORT_TYPE:",
        filtered_df['PORT_TYPE'].unique().tolist()
    )
    filtered_df = filter_database(filtered_df, port_types=port_types)

    voltage_types = st.sidebar.multiselect(
        "Select VOLTAGE_TYPE:",
        filtered_df['VOLTAGE_TYPE'].unique().tolist()
    )
    filtered_df = filter_database(filtered_df, voltage_types=voltage_types)

    voltages = st.sidebar.multiselect(
        "Select VOLTAGES:",
        filtered_df['VOLTAGES'].unique().tolist()
    )
    filtered_df = filter_database(filtered_df, voltages=voltages)

    # Remove empty columns
    filtered_df = remove_empty_columns(filtered_df)

    # Display the table and the summary
    st.header("Generated Test Plan")
    if not filtered_df.empty:
        st.write("The following test cases match your selection:")
        st.dataframe(filtered_df, use_container_width=True)

        # Generate and display the test plan summary
        st.subheader("Test Plan Summary")
        summary, justifiable_summary = generate_summary(filtered_df)
        st.text("### Unique Test Cases")
        st.text(summary)
        if justifiable_summary:
            st.text("### Justifiable Test Cases")
            st.text(justifiable_summary)
    else:
        st.warning("No matching test cases found. Please modify your selections.")

if __name__ == "__main__":
    main()
