import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta

invoices_df = pd.read_excel("Journal Entry (account.move).xlsx")
payments_df = pd.read_excel("Payments (account.payment).xlsx")
customers_df = pd.read_excel("All customers.xlsx")
credit_df = pd.read_excel("Credit notes.xlsx")

today = datetime.today()
yesterday = today - timedelta(days=1)
credit_df["Custom"] = credit_df.apply(
    lambda row: row["Number"] if pd.isna(row["Invoice Partner Display Name"]) else None,
    axis=1
)

credit_df["Representative Name"] = credit_df["Custom"].fillna(method="ffill")

credit_df["Representative Name"] = credit_df["Representative Name"].astype(str).str.replace(r"\s*\(\d+\)", "", regex=True)
credit_df.drop(columns=["Custom"], inplace=True)

credit_df["Representative Name"] = credit_df["Representative Name"].replace("Undefined", "Abdallah")

current_month = datetime.today().month
current_year = datetime.today().year

credit_df = credit_df[
    (credit_df["Invoice/Bill Date"].dt.month == current_month) &
    (credit_df["Invoice/Bill Date"].dt.year == current_year)
]

credit_df = credit_df[["Representative Name", "Untaxed Amount Signed", "Invoice Partner Display Name"]].copy()
new_customers = customers_df[
    pd.to_datetime(customers_df["Created At"], errors="coerce").dt.date == yesterday.date()
]

def extract_salesrep(row):
    for col in ["Representative Name__2", "Representative Name__1", "Representative__2", "Representative__1"]:
        if pd.notna(row.get(col)):
            return row[col]
    return "Administrator"

new_customers["Salesrep_1"] = new_customers.apply(extract_salesrep, axis=1)

new_customers["Salesrep"] = new_customers["Salesrep_1"].apply(
    lambda x: x if x == "Administrator" else f"{x} cash"
)

new_customers = new_customers.groupby("Salesrep").size().reset_index(name="New Customers Count")
MonthlyPayments = payments_df[
    (payments_df["Date"].dt.month == today.month) &
    (payments_df["Date"].dt.year == today.year) &
    (payments_df["Status"] == "posted")
]
YesterdayPayments = MonthlyPayments[
    MonthlyPayments["Date"].dt.date == yesterday.date()
]
# اختيار الأعمدة المطلوبة فقط
MonthlyPayments = MonthlyPayments[["Amount Signed", "Journal"]]

# تجميع المبالغ حسب نوع اليومية
MonthlyPayments = MonthlyPayments.groupby("Journal")["Amount Signed"].sum().reset_index(name="Total")
# اختيار الأعمدة المطلوبة فقط
YesterdayPayments = YesterdayPayments[["Amount Signed", "Journal"]]

# تجميع المبالغ حسب نوع اليومية
YesterdayPayments = YesterdayPayments.groupby("Journal")["Amount Signed"].sum().reset_index(name="Total")
MonthlyPayments = MonthlyPayments.rename(columns={"Amount": "Total_payments"})
YesterdayPayments = YesterdayPayments.rename(columns={"Amount": "Yesterday_payments"})

merged_payments = pd.merge(
    MonthlyPayments,
    YesterdayPayments,
    on="Journal",
    how="left"
)
merged_payments = merged_payments.rename(columns={"Total_x": "Total_payments", "Total_y": "Yesterday_payments"})
merged_payments.fillna(0, inplace=True)

monthly_invoices_df = invoices_df[
    (invoices_df["Invoice/Bill Date"].dt.month == today.month) &
    (invoices_df["Invoice/Bill Date"].dt.year == today.year)
]
yesterday_invoices_df = invoices_df[
    (invoices_df["Invoice/Bill Date"].dt.date == yesterday.date())
]

monthly_invoices_df = monthly_invoices_df.groupby("Sales Person Names")["Untaxed Amount Signed"].sum().reset_index(name="Total")
yesterday_invoices_df = yesterday_invoices_df.groupby("Sales Person Names")["Untaxed Amount Signed"].sum().reset_index(name="Total")
fig_monthly_invoices = px.bar(
    monthly_invoices_df,
    x="Sales Person Names",
    y="Total",
    title="📦 Monthly Invoices per Salesperson",
    text_auto=True,
    color="Total",
    color_continuous_scale="Blues"
)
st.plotly_chart(fig_monthly_invoices, use_container_width=True)
fig_yesterday_invoices = px.bar(
    yesterday_invoices_df,
    x="Sales Person Names",
    y="Total",
    title=f"🧾 Invoices from {yesterday.strftime('%d %b %Y')}",
    text_auto=True,
    color="Total",
    color_continuous_scale="Oranges"
)
st.plotly_chart(fig_yesterday_invoices, use_container_width=True)
fig_payments = px.bar(
    merged_payments,
    x="Journal",
    y=["Total_payments", "Yesterday_payments"],
    title="💰 Payments Breakdown by Journal",
    barmode="group",
    text_auto=True
)
st.plotly_chart(fig_payments, use_container_width=True)
fig_new_customers = px.bar(
    new_customers,
    x="Salesrep",
    y="New Customers Count",
    title=f"🧍‍♂️ New Customers on {yesterday.strftime('%d %b %Y')}",
    text_auto=True,
    color="New Customers Count",
    color_continuous_scale="Greens"
)
st.plotly_chart(fig_new_customers, use_container_width=True)
st.set_page_config(page_title="Daily Sales Dashboard", layout="wide")

st.title("📊 Daily Sales Dashboard")
st.markdown(f"**Date:** {today.strftime('%A, %d %B %Y')}")

# KPIs Section
col1, col2, col3 = st.columns(3)
col1.metric("🧾 Total Invoices This Month", f"{monthly_invoices_df['Total'].sum():,.0f}")
col2.metric("💰 Total Payments This Month", f"{MonthlyPayments['Total'].sum():,.0f}")
col3.metric("🧍‍♂️ New Customers Yesterday", f"{new_customers['New Customers Count'].sum():,.0f}")
st.subheader("📦 Monthly Invoices per Salesperson")
st.plotly_chart(fig_monthly_invoices, use_container_width=True)

st.subheader(f"🧾 Invoices from {yesterday.strftime('%d %b %Y')}")
st.plotly_chart(fig_yesterday_invoices, use_container_width=True)
st.subheader("💰 Payments Breakdown by Journal")
st.plotly_chart(fig_payments, use_container_width=True)
st.subheader(f"🧍‍♂️ New Customers on {yesterday.strftime('%d %b %Y')}")
st.plotly_chart(fig_new_customers, use_container_width=True)
with st.expander("🔍 View Raw Data"):
    st.write("Monthly Payments")
    st.dataframe(MonthlyPayments)

    st.write("Yesterday Payments")
    st.dataframe(YesterdayPayments)

    st.write("New Customers")
    st.dataframe(new_customers)

    st.write("Credit Notes")
    st.dataframe(credit_df)