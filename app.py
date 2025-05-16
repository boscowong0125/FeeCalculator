import streamlit as st
import pandas as pd
import numpy as np

if 'has_calculated' not in st.session_state:
    st.session_state.has_calculated = False
if 'annual_fee' not in st.session_state:
    st.session_state.annual_fee = 0
if 'daily_fee' not in st.session_state:
    st.session_state.daily_fee = 0
if 'tier_data' not in st.session_state:
    st.session_state.tier_data = []
if 'download_df' not in st.session_state:
    st.session_state.download_df = None

def calculate_fees(amount, thresholds, rates):
    """Calculate fees based on tiers."""
    total_fee = 0
    tier_fees = []
    prev_threshold = 0
    
    # Calculate for defined tiers
    for i in range(len(thresholds)):
        current_threshold = float(thresholds[i])
        current_rate = float(rates[i]) / 100  # Convert percentage to decimal
        
        if amount > prev_threshold:
            tier_amount = min(amount, current_threshold) - prev_threshold
            tier_fee = tier_amount * current_rate
            total_fee += tier_fee
            tier_fees.append(tier_fee)
        else:
            tier_fees.append(0)
        
        prev_threshold = current_threshold
    
    # Calculate for remainder
    if amount > prev_threshold:
        remainder_rate = float(rates[-1]) / 100  # Convert percentage to decimal
        remainder_amount = amount - prev_threshold
        remainder_fee = remainder_amount * remainder_rate
        total_fee += remainder_fee
        tier_fees.append(remainder_fee)
    else:
        tier_fees.append(0)
    
    return total_fee, tier_fees

st.title("Fee Calculator")
st.markdown("""
This app calculates fees based on defined tiers. 
You can define multiple thresholds and corresponding rates, then see the calculated fees for a given amount.
""")

# Initialize session state for thresholds and rates
if 'thresholds' not in st.session_state:
    st.session_state.thresholds = ['2000000', '3000000']
if 'rates' not in st.session_state:
    st.session_state.rates = ['1.25', '1.00', '0.75']

# Input for total amount
st.subheader("Total AUM")
amount = st.number_input("Enter AUM ($):", min_value=0.0, value=10000000.0, step=1000.0)

# Display and edit tiers
st.subheader("Fee Tiers")
st.markdown("""
Define your fee tiers below:
* First tier applies to the initial amount
* Middle tiers apply to the "next" amounts
* The remainder tier applies to any amount above the highest threshold
""")

# Add a new tier button
col1, col2 = st.columns([1, 3])
with col1:
    if st.button("Add Tier"):
        # Get the last threshold value
        last_threshold = float(st.session_state.thresholds[-1])
        # Add a new increment of 1,000,000 by default
        st.session_state.thresholds.append(str(last_threshold + 1000000))
        st.session_state.rates.append('0')
        st.rerun()

# Display tier headers
tier_cols = st.columns([1, 2, 2, 1])
tier_cols[0].markdown("**Tier**")
tier_cols[1].markdown("**Amount ($)**")
tier_cols[2].markdown("**Rate (%)**")
tier_cols[3].markdown("**Action**")

# Track cumulative threshold for display
cumulative_threshold = 0

# Display current tiers
for i in range(len(st.session_state.thresholds)):
    cols = st.columns([1, 2, 2, 1])
    
    # First tier is "First $X"
    if i == 0:
        tier_label = "First"
        cols[0].markdown(f"{tier_label}")
        
        # Get the tier amount (first threshold)
        tier_amount = cols[1].text_input(
            f"First $ amount",
            value=st.session_state.thresholds[i],
            key=f"threshold_{i}",
            help="Amount for the first tier"
        )
        
        # Store the absolute threshold
        st.session_state.thresholds[i] = tier_amount
        cumulative_threshold = float(tier_amount)
    else:
        tier_label = "Next"
        cols[0].markdown(f"{tier_label}")
        
        # Calculate the increment for this tier
        prev_threshold = float(st.session_state.thresholds[i-1])
        current_threshold = float(st.session_state.thresholds[i])
        tier_increment = current_threshold - prev_threshold
        
        # Get the tier increment
        tier_amount = cols[1].text_input(
            f"Next $ amount",
            value=str(tier_increment),
            key=f"threshold_{i}",
            help=f"Amount for tier {i+1}"
        )
        
        # Update the cumulative threshold
        cumulative_threshold += float(tier_amount)
        # Store the absolute threshold
        st.session_state.thresholds[i] = str(cumulative_threshold)
    
    # Rate input
    st.session_state.rates[i] = cols[2].text_input(
        f"Rate {i+1}",
        value=st.session_state.rates[i],
        key=f"rate_{i}",
        help=f"Fee percentage for tier {i+1}"
    )
    
    # Remove button - not for first tier
    if i > 0 and cols[3].button("Remove", key=f"remove_{i}"):
        st.session_state.thresholds.pop(i)
        st.session_state.rates.pop(i)
        st.rerun()

# Remainder tier
cols = st.columns([1, 2, 2, 1])
cols[0].markdown("**Remainder**")
cols[1].markdown("Amount Remaining")

# Ensure rates list has enough elements
if len(st.session_state.rates) <= len(st.session_state.thresholds):
    st.session_state.rates.append('0')

# Rate input for remainder
remainder_idx = len(st.session_state.thresholds)
st.session_state.rates[remainder_idx] = cols[2].text_input(
    f"Remainder Rate",
    value=st.session_state.rates[remainder_idx],
    key=f"rate_{remainder_idx}",
    help="Fee percentage for amounts above the highest threshold"
)

st.subheader("Calculate Fees")
if st.button("Calculate"):
    try:
        # Calculate fees
        annual_fee, tier_fees = calculate_fees(amount, st.session_state.thresholds, st.session_state.rates)
        daily_fee = annual_fee / 365
        
        # Store results in session state
        st.session_state.has_calculated = True
        st.session_state.annual_fee = annual_fee
        st.session_state.daily_fee = daily_fee
        
        # Prepare data for display and download
        tier_data = []
        prev_threshold = 0
        
        for i, threshold in enumerate(st.session_state.thresholds):
            threshold = float(threshold)
            rate = float(st.session_state.rates[i])
            
            tier_amount = min(max(0, amount - prev_threshold), threshold - prev_threshold)
            tier_fee = tier_fees[i]
            
            # Format the tier description
            if i == 0:
                tier_desc = f"First ${threshold:,.2f}"
                range_desc = f"$0.00 to ${threshold:,.2f}"
            else:
                tier_desc = f"Next ${threshold - prev_threshold:,.2f}"
                range_desc = f"${prev_threshold:,.2f} to ${threshold:,.2f}"
            
            tier_data.append({
                "Tier": tier_desc,
                "Range": range_desc,
                "Rate (%)": rate,
                "Amount in Tier ($)": tier_amount,
                "Fee ($)": round(tier_fee, 2)
            })
            
            prev_threshold = threshold
        
        # Add remainder tier if amount exceeds the last threshold
        if amount > float(st.session_state.thresholds[-1]):
            remainder_amount = amount - float(st.session_state.thresholds[-1])
            remainder_rate = float(st.session_state.rates[-1])
            remainder_fee = tier_fees[-1]
            
            tier_data.append({
                "Tier": "Remainder",
                "Range": f"Above ${float(st.session_state.thresholds[-1]):,.2f}",
                "Rate (%)": remainder_rate,
                "Amount in Tier ($)": remainder_amount,
                "Fee ($)": round(remainder_fee, 2)
            })
        
        # Store the tier data in session state
        st.session_state.tier_data = tier_data
        
        # Create summary and daily fee rows
        summary_data = {
            "Tier": "Total",
            "Range": "",
            "Rate (%)": "",
            "Amount in Tier ($)": amount,
            "Fee ($)": round(annual_fee, 2)
        }
        
        daily_data = {
            "Tier": "Daily Fee",
            "Range": "",
            "Rate (%)": "",
            "Amount in Tier ($)": "",
            "Fee ($)": round(daily_fee, 2)
        }
        
        # Create download dataframe and store in session state
        tier_df = pd.DataFrame(tier_data)
        st.session_state.download_df = pd.concat([tier_df, pd.DataFrame([summary_data, daily_data])])
        
    except ValueError as e:
        st.error(f"Error in calculation: {e}. Please ensure all thresholds and rates are valid numbers.")

# Add a new section after the Calculate button to display results
if st.session_state.has_calculated:
    # Display results
    st.subheader("Fee Results")
    results_cols = st.columns(2)
    results_cols[0].metric("Annual Fee", f"${st.session_state.annual_fee:,.2f}")
    results_cols[1].metric("Daily Fee Accrual", f"${st.session_state.daily_fee:,.2f}")
    
    # Display tier details
    st.subheader("Fee Breakdown")
    tier_df = pd.DataFrame(st.session_state.tier_data)
    summary_data = {
        "Tier": "Total",
        "Range": "",
        "Rate (%)": "",
        "Amount in Tier ($)": amount,
        "Fee ($)": round(st.session_state.annual_fee, 2)
    }
    display_df = pd.concat([tier_df, pd.DataFrame([summary_data])])
    st.dataframe(display_df)
    
    # Download button
    csv = st.session_state.download_df.to_csv(index=False)
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="fee_calculation.csv",
        mime="text/csv",
    )